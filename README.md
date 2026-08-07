# 종목 비교 인터랙티브 대시보드

종목 2~3개를 골라 나란히 비교하는 체험형 웹앱입니다. hyorang.com 블로그에 iframe으로 임베드하는 용도로 만들었습니다.

- 인기 라이벌 프리셋 (삼성전자 vs SK하이닉스, 애플 vs 마이크로소프트 등)
- 티커 직접 입력 (한국 주식은 6자리 코드만 입력하면 `.KS`/`.KQ` 자동 처리)
- 기간 토글: 1개월 / 6개월 / 1년 / 3년
- 시작점 0% 정규화 수익률 라인차트, 핵심 지표 카드(현재가·수익률·최대 낙폭), 레이더 강점 비교, 템플릿 기반 승부 요약
- yfinance 호출 1시간 캐싱, Render 무료 티어(512MB) 기준 경량 구성

> ⚠️ 과거 데이터 기반 단순 비교이며 투자 자문이 아닙니다.

## 로컬 실행

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 http://localhost:8501 접속.

## Docker 실행

```bash
docker build -t stock-compare .
docker run -p 8501:8501 stock-compare
```

`PORT` 환경변수를 주면 해당 포트로 실행됩니다 (없으면 8501).

```bash
docker run -e PORT=10000 -p 10000:10000 stock-compare
```

## Render 배포

1. 이 저장소를 GitHub에 푸시
2. Render 대시보드 → **New → Web Service** → 저장소 연결
3. 설정:
   - **Runtime**: Docker
   - **Instance Type**: Free
   - 별도 빌드/시작 명령 불필요 (Dockerfile이 `PORT` 환경변수를 자동 처리)
4. 배포 완료 후 `https://<서비스명>.onrender.com` 확인

> 무료 티어는 15분 무트래픽 시 슬립 → 첫 접속이 느릴 수 있습니다.

## 블로그 임베드 (iframe)

Streamlit의 임베드 모드(`?embed=true`)를 사용하면 여백 없이 깔끔하게 들어갑니다.

```html
<iframe
  src="https://<서비스명>.onrender.com/?embed=true"
  width="100%"
  height="1400"
  style="border: none; border-radius: 12px; overflow: hidden;"
  loading="lazy"
  title="종목 비교 대시보드"
></iframe>
```

- 모바일/좁은 폭에서는 카드가 세로로 쌓이므로 `height`를 넉넉히(1600~1800) 잡는 것을 권장합니다.

## 구조

```
├── app.py                  # Streamlit 앱 전체 (UI + 데이터 + 차트)
├── requirements.txt        # 버전 고정 (Python 3.11 기준)
├── Dockerfile
├── .streamlit/config.toml  # 테마/서버 설정
├── .gitignore
└── .dockerignore
```

## 면책

본 앱은 과거 시세 데이터를 기반으로 한 단순 비교 자료이며, 특정 종목에 대한 매수·매도 추천이나 투자 자문이 아닙니다. 데이터 출처는 Yahoo Finance이며 지연·오차가 있을 수 있습니다.
