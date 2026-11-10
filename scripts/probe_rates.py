"""임시 확인용: 수출입은행 국제금리(AP03)·대출금리(AP02)에 어떤 값이 있는지 로그로 출력 (인증키는 출력하지 않음)"""
import json, os, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
API = "https://oapi.koreaexim.go.kr/site/program/financial/exchangeJSON"
key = os.environ["KOREAEXIM_API_KEY"].strip()
today = datetime.now(timezone(timedelta(hours=9))).date()
for code in ("AP03", "AP02"):
    print(f"===== {code} =====")
    for back in range(0, 8):
        day = (today - timedelta(days=back)).strftime("%Y%m%d")
        q = urllib.parse.urlencode({"authkey": key, "searchdate": day, "data": code})
        try:
            with urllib.request.urlopen(urllib.request.Request(f"{API}?{q}", headers={"User-Agent": "probe"}), timeout=30) as r:
                rows = json.loads(r.read().decode("utf-8") or "[]")
        except Exception as e:
            print(day, "요청 실패", type(e).__name__); continue
        print(day, "건수", len(rows) if isinstance(rows, list) else rows)
        if isinstance(rows, list) and rows:
            for row in rows:
                print(json.dumps(row, ensure_ascii=False))
            break
