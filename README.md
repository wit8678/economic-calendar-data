# economic-calendar-data

경제일정 앱이 내려받는 **공개 일정 파일**입니다. 앱 소스 코드와 인증키는 이 저장소에 없습니다.

- `key_schedule.json` : 주요 경제 일정·휴장일·공휴일·기준금리, 시장 심리 지수(매주 자동 갱신)
- `scripts/update_sentiment.py` : 시장 심리 지수 계산 (GitHub Actions 가 매주 실행)
- `.github/workflows/update-sentiment.yml` : 자동 실행 설정

## 출처
- 경제 일정: 각 기관 공식 발표 일정 (항목마다 `sourceName`, `sourceUrl`, `checkedAt` 기재)
- 시장 심리 지수: Federal Reserve Bank of St. Louis, St. Louis Fed Financial Stress Index [STLFSI4], retrieved from FRED, Federal Reserve Bank of St. Louis. 이 앱의 자체 지표이며 CNN 공포·탐욕 지수와 다릅니다.
- This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis.

※ 일정 안내 자료이며 투자 권유가 아닙니다.
