"""경제일정 앱: 한국수출입은행 환율(매매기준율)을 받아 fx.json 으로 저장

- 인증키는 GitHub Secrets 의 KOREAEXIM_API_KEY 에서만 읽고, 화면·파일에 절대 남기지 않습니다.
- 수출입은행 환율은 영업일 오전 11시쯤 고시됩니다. 오늘 값이 없으면(11시 전·주말·공휴일) 이전 영업일 값을 씁니다.
- 앱은 이 fx.json 을 읽어 "기준일 · 출처"와 함께 보여 줍니다. 실시간 시세가 아닙니다.
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://oapi.koreaexim.go.kr/site/program/financial/exchangeJSON"
SOURCE_URL = "https://www.koreaexim.go.kr"
KST = timezone(timedelta(hours=9))
OUT = "fx.json"


def fetch(key: str, day: str):
    query = urllib.parse.urlencode({"authkey": key, "searchdate": day, "data": "AP01"})
    req = urllib.request.Request(f"{API}?{query}", headers={"User-Agent": "EconomicCalendar-data/1.0"})
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read().decode("utf-8") or "[]")


def number(text) -> float:
    return float(str(text).replace(",", "").strip())


def main() -> int:
    key = os.environ.get("KOREAEXIM_API_KEY", "").strip()
    if not key:
        print("KOREAEXIM_API_KEY 가 없습니다. 저장소 Settings > Secrets 에 등록해 주세요.")
        return 1
    today = datetime.now(KST).date()
    for back in range(0, 8):
        day = today - timedelta(days=back)
        try:
            rows = fetch(key, day.strftime("%Y%m%d"))
        except Exception as e:  # 주소·네트워크 오류 (키가 섞인 주소는 출력하지 않음)
            print(f"{day}: 요청 실패 ({type(e).__name__})")
            continue
        if not isinstance(rows, list) or not rows:
            print(f"{day}: 고시 환율 없음 (11시 전·휴일)")
            continue
        codes = {r.get("result") for r in rows}
        if 3 in codes:
            print("인증키 오류 (result=3): 키를 확인해 주세요."); return 1
        if 4 in codes:
            print("하루 호출 횟수 초과 (result=4)"); return 1
        by_unit = {r.get("cur_unit"): r for r in rows if r.get("result") == 1}
        usd, jpy = by_unit.get("USD"), by_unit.get("JPY(100)")
        if not usd or not jpy:
            print(f"{day}: 달러·엔 값 없음"); continue
        usd_krw, jpy100_krw = number(usd["deal_bas_r"]), number(jpy["deal_bas_r"])
        if not (500 <= usd_krw <= 5000 and 300 <= jpy100_krw <= 3000):
            print(f"{day}: 값이 정상 범위를 벗어남"); return 1
        data = {
            "source": "한국수출입은행 매매기준율",
            "sourceUrl": SOURCE_URL,
            "date": day.isoformat(),
            "usdKrw": usd_krw,
            "jpy100Krw": jpy100_krw,
            "updatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        old = {}
        if os.path.exists(OUT):
            try:
                old = json.load(open(OUT, encoding="utf-8"))
            except Exception:
                old = {}
        if all(old.get(k) == data[k] for k in ("date", "usdKrw", "jpy100Krw")):
            print(f"{day}: 변경 없음 ({usd_krw} / {jpy100_krw})"); return 0
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2); f.write("\n")
        print(f"{day}: 저장 완료 원/달러 {usd_krw}, 원/100엔 {jpy100_krw}")
        return 0
    print("최근 8일 동안 받은 환율이 없습니다.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
