#!/usr/bin/env python3
"""
경제일정 앱 - 시장 심리 지수 주간 갱신 스크립트 (GitHub Actions 에서 실행)

하는 일
 1) FRED 에서 세인트루이스 연은 금융스트레스지수(STLFSI4) 최근 6년치를 받는다.
 2) 앱과 똑같은 방식으로 점수를 계산한다.
    score = 100 - (최근 값의 지난 260주 중 백분위), 0~100, 반올림은 Kotlin roundToInt 와 같게(0.5는 올림)
 3) key_schedule.json 의 marketSentiment 와 updatedAt 을 바꾼다. (값이 같으면 아무것도 안 바꿈)

보안
 - FRED 인증키는 GitHub 저장소 Secrets(FRED_API_KEY)에서만 읽는다. 파일·로그에 절대 쓰지 않는다.
 - 오류가 나도 주소(키 포함)를 출력하지 않는다.
출처 표기
 - Federal Reserve Bank of St. Louis, St. Louis Fed Financial Stress Index [STLFSI4], retrieved from FRED.
 - This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis.
"""
import datetime as dt
import json
import math
import os
import sys
import urllib.parse
import urllib.request

SCHEDULE = os.path.join(os.path.dirname(__file__), "..", "key_schedule.json")
WINDOW_WEEKS = 260


def fetch_observations(api_key: str):
    start = (dt.date.today() - dt.timedelta(days=366 * 6)).isoformat()
    query = urllib.parse.urlencode({
        "series_id": "STLFSI4", "file_type": "json",
        "observation_start": start, "api_key": api_key,
    })
    request = urllib.request.Request(
        "https://api.stlouisfed.org/fred/series/observations?" + query,
        headers={"User-Agent": "economic-calendar-data/1.0 (GitHub Actions)"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.load(response)
    except Exception as error:  # 주소에 키가 들어 있으므로 오류 종류만 출력
        sys.exit(f"FRED 자료를 받지 못했습니다: {type(error).__name__}")
    result = []
    for item in data.get("observations", []):
        if item.get("value") in (None, "", "."):
            continue
        result.append((dt.date.fromisoformat(item["date"]), float(item["value"])))
    return sorted(result)


def compute(observations):
    if len(observations) < 52:
        sys.exit("계산에 필요한 자료가 부족합니다.")
    window = observations[-WINDOW_WEEKS:]
    latest_date, latest_value = window[-1]
    below = sum(1 for _, v in window if v < latest_value)
    equal = sum(1 for _, v in window if v == latest_value)
    percentile = (below + 0.5 * equal) / len(window) * 100
    score = min(100, max(0, math.floor(100 - percentile + 0.5)))
    return score, latest_date, latest_value


def main():
    api_key = os.environ.get("FRED_API_KEY", "").strip()
    if not api_key:
        sys.exit("FRED_API_KEY 가 없습니다. 저장소 Settings > Secrets and variables > Actions 에 넣어 주세요.")
    score, as_of, stress = compute(fetch_observations(api_key))

    with open(SCHEDULE, encoding="utf-8") as f:
        schedule = json.load(f)
    new_value = {
        "score": score,
        "asOf": as_of.isoformat(),
        "stressValue": stress,
        "source": "Federal Reserve Bank of St. Louis, STLFSI4, retrieved from FRED",
    }
    old_value = schedule.get("marketSentiment") or {}
    if all(old_value.get(k) == new_value[k] for k in ("score", "asOf", "stressValue")):
        print(f"변경 없음: {as_of} 기준 {score}점")
        return
    schedule["marketSentiment"] = new_value
    # 앱은 updatedAt 이 더 최신인 파일만 받아들이므로 갱신 시각을 올린다.
    schedule["updatedAt"] = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    with open(SCHEDULE, "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"갱신: {as_of} 기준 {score}점 (스트레스 {stress})")


if __name__ == "__main__":
    main()
