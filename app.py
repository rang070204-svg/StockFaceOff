# -*- coding: utf-8 -*-
"""종목 비교 인터랙티브 대시보드 — hyorang.com 임베드용"""

import math
import re

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

# ──────────────────────────────────────────────
# 기본 설정
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="종목 비교 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

FONT_STACK = '"Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont, system-ui, sans-serif'
ACCENT = "#B4F056"          # 포인트 라임그린 (뱃지 전용)
ACCENT_LINE = "#8FC63C"     # 라인/레이더용 진한 라임 (3번째 종목)
STOCK_COLORS = ["#161616", "#9C9C98", ACCENT_LINE]  # 무채색 농도 차이 + 포인트그린
KRW_PER_USD = 1400          # 거래대금 스코어 산출용 대략 환율 (표시용 아님)
MAX_TICKERS = 3

PERIODS = {"1개월": "1mo", "6개월": "6mo", "1년": "1y", "3년": "3y"}

PRESETS = {
    "삼성전자 vs SK하이닉스": "005930, 000660",
    "애플 vs 마이크로소프트": "AAPL, MSFT",
    "테슬라 vs 현대차": "TSLA, 005380",
    "네이버 vs 카카오": "035420, 035720",
}

KNOWN_NAMES = {
    "005930.KS": "삼성전자",
    "000660.KS": "SK하이닉스",
    "005380.KS": "현대차",
    "035420.KS": "네이버",
    "035720.KS": "카카오",
    "373220.KS": "LG에너지솔루션",
    "005490.KS": "포스코홀딩스",
    "AAPL": "애플",
    "MSFT": "마이크로소프트",
    "TSLA": "테슬라",
    "NVDA": "엔비디아",
    "AMD": "AMD",
    "GOOGL": "알파벳(구글)",
    "AMZN": "아마존",
    "META": "메타",
    "KO": "코카콜라",
    "PEP": "펩시코",
}

# ──────────────────────────────────────────────
# 커스텀 CSS — Streamlit 기본 디자인 제거 + 핀테크 미니멀
# ──────────────────────────────────────────────
st.markdown(
    """
<style>
@import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css");

html, body, .stApp, .stApp p, .stApp div, .stApp span, .stApp label,
.stApp input, .stApp button, .stApp h1, .stApp h2, .stApp h3 {
    font-family: "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
}

/* 배경: 오프화이트 + 아주 은은한 웜그레이 그라데이션 */
.stApp {
    background: linear-gradient(165deg, #F7F7F4 0%, #F5F5F2 45%, #F2F1EC 100%);
    color: #1A1A18;
}

/* Streamlit 기본 크롬 제거 */
#MainMenu, footer, header[data-testid="stHeader"],
[data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }
.block-container { padding: 2.4rem 2rem 3rem; max-width: 1100px; }
[data-testid="InputInstructions"] { display: none; }

/* 타이틀 */
.app-eyebrow {
    font-size: 0.78rem; font-weight: 500; letter-spacing: 0.12em;
    color: #9B9B94; text-transform: uppercase; margin-bottom: 0.35rem;
}
.app-title {
    font-size: clamp(1.5rem, 3.4vw, 2.1rem); font-weight: 700;
    letter-spacing: -0.02em; color: #141412; margin: 0 0 0.3rem 0;
}
.app-sub { font-size: 0.92rem; font-weight: 400; color: #8A8A83; margin-bottom: 1.6rem; }

.section-label {
    font-size: 0.8rem; font-weight: 600; letter-spacing: 0.02em;
    color: #6E6E67; margin: 1.4rem 0 0.5rem 0;
}

/* 프리셋/일반 버튼 → 미니멀 필 */
[data-testid="stBaseButton-secondary"] {
    background: #FFFFFF; border: 1px solid #E7E7E1; border-radius: 999px;
    color: #4A4A45; font-size: 0.85rem; font-weight: 500;
    padding: 0.32rem 0.95rem; box-shadow: none; transition: border-color .15s, color .15s;
}
[data-testid="stBaseButton-secondary"]:hover {
    border-color: #1A1A18; color: #1A1A18; background: #FFFFFF;
}

/* 기간 pills */
[data-testid="stBaseButton-pills"] {
    background: #FFFFFF; border: 1px solid #E7E7E1; border-radius: 999px;
    color: #6B6B64; font-size: 0.85rem; font-weight: 500; box-shadow: none;
}
[data-testid="stBaseButton-pillsActive"] {
    background: #1A1A18; border: 1px solid #1A1A18; border-radius: 999px;
    color: #FFFFFF; font-size: 0.85rem; font-weight: 600; box-shadow: none;
}
[data-testid="stBaseButton-pillsActive"]:hover { background: #1A1A18; color: #FFFFFF; }

/* 텍스트 입력 */
[data-testid="stTextInput"] input {
    background: #FFFFFF; border: 1px solid #E7E7E1; border-radius: 10px;
    color: #1A1A18; font-size: 0.92rem;
}
[data-testid="stTextInput"] input:focus { border-color: #1A1A18; box-shadow: none; }
[data-testid="stTextInput"] label { color: #6E6E67; font-size: 0.8rem; }

/* 종목 카드 */
.stock-card {
    background: #FFFFFF; border: 1px solid #ECECE6; border-radius: 12px;
    padding: 1.25rem 1.35rem 1.15rem; height: 100%;
    box-shadow: 0 1px 2px rgba(20, 20, 18, 0.03);
}
.stock-card-head { display: flex; align-items: baseline; gap: 0.45rem; margin-bottom: 0.7rem; }
.stock-dot { width: 9px; height: 9px; border-radius: 50%; flex: none; align-self: center; }
.stock-name { font-size: 0.98rem; font-weight: 600; color: #21211E; letter-spacing: -0.01em; }
.stock-ticker { font-size: 0.74rem; font-weight: 400; color: #A4A49D; }
.stock-price {
    font-size: clamp(1.9rem, 3.6vw, 2.6rem); font-weight: 600;
    letter-spacing: -0.03em; color: #141412; line-height: 1.1; margin-bottom: 0.85rem;
}
.stock-metrics { display: flex; flex-direction: column; gap: 0.5rem; }
.m-row { display: flex; align-items: center; justify-content: space-between; }
.m-label { font-size: 0.78rem; font-weight: 400; color: #9B9B94; }
.m-big { font-size: 1.25rem; font-weight: 600; letter-spacing: -0.02em; color: #3A3A36; }
.badge {
    display: inline-block; padding: 0.18rem 0.65rem; border-radius: 999px;
    font-size: 0.95rem; font-weight: 600; letter-spacing: -0.01em;
}
.badge-up { background: #B4F056; color: #1E2A08; }
.badge-down { background: #ECECE7; color: #6B6B64; }

/* 승부 요약 카드 */
.verdict-card {
    background: #FFFFFF; border: 1px solid #ECECE6; border-radius: 12px;
    padding: 1.2rem 1.35rem; box-shadow: 0 1px 2px rgba(20, 20, 18, 0.03);
}
.verdict-headline {
    font-size: 1.05rem; font-weight: 600; letter-spacing: -0.01em;
    color: #1A1A18; margin-bottom: 0.8rem;
}
.verdict-row {
    display: flex; align-items: baseline; gap: 0.6rem;
    padding: 0.42rem 0; border-top: 1px solid #F1F1EB; font-size: 0.88rem;
}
.verdict-metric { color: #9B9B94; font-weight: 400; min-width: 7.5em; flex: none; }
.verdict-result { color: #3A3A36; font-weight: 500; }
.verdict-winner {
    background: #B4F056; color: #1E2A08; font-weight: 600;
    padding: 0.05rem 0.5rem; border-radius: 999px; margin-right: 0.15rem;
}

/* 차트 카드 래퍼 */
.chart-note { font-size: 0.8rem; color: #9B9B94; margin: -0.3rem 0 0.4rem; }

/* 면책/푸터 */
.app-footer {
    margin-top: 2.4rem; padding-top: 1.1rem; border-top: 1px solid #E7E7E1;
    font-size: 0.76rem; color: #A4A49D; line-height: 1.6;
}
.app-footer a { color: #6E6E67; font-weight: 500; text-decoration: none; border-bottom: 1px solid #D8D8D1; }
.app-footer a:hover { color: #1A1A18; border-color: #1A1A18; }

/* 모바일/좁은 iframe: 카드 세로 스택 */
@media (max-width: 640px) {
    .block-container { padding: 1.4rem 1rem 2.2rem; }
    [data-testid="stHorizontalBlock"] { flex-direction: column; }
    [data-testid="stHorizontalBlock"] > div { width: 100% !important; min-width: 100% !important; }
    .stock-card { margin-bottom: 0.6rem; }
}
</style>
""",
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# 데이터 (yfinance, 1시간 캐시)
# ──────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_history(symbol: str, period: str) -> pd.DataFrame:
    try:
        df = yf.Ticker(symbol).history(period=period, auto_adjust=True)
    except Exception:
        return pd.DataFrame()
    if df is None or df.empty or "Close" not in df.columns:
        return pd.DataFrame()
    df = df[["Close", "Volume"]].dropna(subset=["Close"])
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    return df


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_display_name(symbol: str) -> str:
    if symbol in KNOWN_NAMES:
        return KNOWN_NAMES[symbol]
    try:
        info = yf.Ticker(symbol).info
        return info.get("shortName") or info.get("longName") or symbol
    except Exception:
        return symbol


def parse_tickers(raw: str) -> list[str]:
    tokens = [t.strip().upper() for t in re.split(r"[,\s]+", raw or "") if t.strip()]
    seen, out = set(), []
    for t in tokens:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def resolve_and_fetch(token: str, period: str):
    """한국 주식 6자리 코드는 .KS → .KQ 순서로 자동 시도."""
    if re.fullmatch(r"\d{6}", token):
        candidates = [f"{token}.KS", f"{token}.KQ"]
    elif re.fullmatch(r"\d{6}\.(KS|KQ)", token):
        candidates = [token]
    else:
        candidates = [token]
    for symbol in candidates:
        df = fetch_history(symbol, period)
        if len(df) >= 2:
            return symbol, df
    return None, None


def is_krw(symbol: str) -> bool:
    return symbol.endswith((".KS", ".KQ"))


def fmt_price(value: float, symbol: str) -> str:
    if is_krw(symbol):
        return f"₩{value:,.0f}"
    return f"${value:,.2f}"


def fmt_pct(value: float) -> str:
    sign = "+" if value >= 0 else "−"
    return f"{sign}{abs(value):.1f}%"


def compute_metrics(symbol: str, df: pd.DataFrame) -> dict:
    close = df["Close"]
    ret = (close.iloc[-1] / close.iloc[0] - 1) * 100
    mdd = ((close / close.cummax()) - 1).min() * 100
    daily = close.pct_change().dropna()
    vol = daily.std() * math.sqrt(252) * 100 if len(daily) > 1 else 0.0
    n = max(5, len(close) // 4)
    n = min(n, len(close) - 1)
    momentum = (close.iloc[-1] / close.iloc[-n - 1] - 1) * 100 if n >= 1 else 0.0
    trade_value = float((close * df["Volume"]).tail(20).mean() or 0)
    if is_krw(symbol):
        trade_value /= KRW_PER_USD  # 통화 통일(스코어 비교용)
    return {
        "price": float(close.iloc[-1]),
        "return": float(ret),
        "mdd": float(mdd),
        "volatility": float(vol),
        "momentum": float(momentum),
        "trade_value": trade_value,
    }


def relative_scores(values: list[float], invert: bool = False) -> list[float]:
    """비교 종목끼리 30~95점 상대 스코어. 값이 같으면 60점."""
    arr = np.array(values, dtype=float)
    if invert:
        arr = -arr
    lo, hi = arr.min(), arr.max()
    if hi - lo < 1e-9:
        return [60.0] * len(arr)
    return list(30 + (arr - lo) / (hi - lo) * 65)


# ──────────────────────────────────────────────
# 헤더 + 입력 UI
# ──────────────────────────────────────────────
st.markdown(
    """
<div class="app-eyebrow">Stock Face-off</div>
<h1 class="app-title">두 종목, 같은 돈을 넣었다면?</h1>
<div class="app-sub">궁금한 종목 2~3개를 골라 과거 데이터를 나란히 비교해 보세요.</div>
""",
    unsafe_allow_html=True,
)

if "ticker_text" not in st.session_state:
    st.session_state.ticker_text = "AAPL, MSFT"


def apply_preset(value: str):
    st.session_state.ticker_text = value


st.markdown('<div class="section-label">인기 대결 카드</div>', unsafe_allow_html=True)
preset_cols = st.columns(len(PRESETS))
for col, (label, value) in zip(preset_cols, PRESETS.items()):
    col.button(label, on_click=apply_preset, args=(value,), use_container_width=True)

in_col, period_col = st.columns([3, 2])
with in_col:
    st.text_input(
        "티커 직접 입력 (쉼표로 구분, 최대 3개)",
        key="ticker_text",
        placeholder="예: AAPL, MSFT 또는 005930, 000660",
        help="한국 주식은 6자리 종목코드만 입력하면 코스피(.KS)/코스닥(.KQ)을 자동으로 찾아드려요.",
    )
with period_col:
    st.markdown('<div style="height:1.7rem"></div>', unsafe_allow_html=True)
    period_label = st.pills("기간", list(PERIODS.keys()), default="1년", label_visibility="collapsed")

period_label = period_label or "1년"
period = PERIODS[period_label]

tokens = parse_tickers(st.session_state.ticker_text)
if len(tokens) > MAX_TICKERS:
    st.info(f"비교는 최대 {MAX_TICKERS}개까지만 지원해요. 앞의 {MAX_TICKERS}개만 사용할게요.")
    tokens = tokens[:MAX_TICKERS]

if not tokens:
    st.info("비교할 종목의 티커를 입력하거나, 위의 인기 대결 카드를 눌러 보세요.")
    st.stop()

# ──────────────────────────────────────────────
# 데이터 로딩
# ──────────────────────────────────────────────
stocks, failed = [], []
with st.spinner("시세 데이터를 불러오는 중..."):
    for token in tokens:
        symbol, df = resolve_and_fetch(token, period)
        if symbol is None:
            failed.append(token)
            continue
        stocks.append(
            {
                "symbol": symbol,
                "name": fetch_display_name(symbol),
                "df": df,
                **compute_metrics(symbol, df),
            }
        )

if failed:
    st.warning(
        f"다음 티커의 데이터를 찾지 못했어요: **{', '.join(failed)}** — "
        "야후 파이낸스 기준 티커인지 확인해 주세요. (예: 미국 주식 AAPL, 한국 주식 005930)"
    )
if not stocks:
    st.stop()

for i, s in enumerate(stocks):
    s["color"] = STOCK_COLORS[i % len(STOCK_COLORS)]

# ──────────────────────────────────────────────
# 핵심 지표 카드
# ──────────────────────────────────────────────
st.markdown('<div class="section-label">핵심 지표</div>', unsafe_allow_html=True)
cards = st.columns(len(stocks))
for col, s in zip(cards, stocks):
    badge_cls = "badge-up" if s["return"] >= 0 else "badge-down"
    col.markdown(
        f"""
<div class="stock-card">
  <div class="stock-card-head">
    <span class="stock-dot" style="background:{s['color']}"></span>
    <span class="stock-name">{s['name']}</span>
    <span class="stock-ticker">{s['symbol']}</span>
  </div>
  <div class="stock-price">{fmt_price(s['price'], s['symbol'])}</div>
  <div class="stock-metrics">
    <div class="m-row">
      <span class="m-label">{period_label} 수익률</span>
      <span class="badge {badge_cls}">{fmt_pct(s['return'])}</span>
    </div>
    <div class="m-row">
      <span class="m-label">최대 낙폭</span>
      <span class="m-big">{s['mdd']:.1f}%</span>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

# ──────────────────────────────────────────────
# 수익률 비교 라인차트 (시작점 0% 정규화)
# ──────────────────────────────────────────────
st.markdown('<div class="section-label">기간 수익률 비교</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="chart-note">{period_label} 전 같은 날 같은 돈을 넣었다고 가정했을 때의 누적 수익률이에요.</div>',
    unsafe_allow_html=True,
)

line_fig = go.Figure()
for s in stocks:
    close = s["df"]["Close"]
    norm = (close / close.iloc[0] - 1) * 100
    line_fig.add_trace(
        go.Scatter(
            x=norm.index,
            y=norm.values,
            name=s["name"],
            line=dict(color=s["color"], width=1.6),
            hovertemplate="%{y:+.1f}%<extra>" + s["name"] + "</extra>",
        )
    )
line_fig.add_hline(y=0, line_color="#D8D8D1", line_width=1)
line_fig.update_layout(
    font=dict(family=FONT_STACK, color="#6E6E67", size=12),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    hovermode="x unified",
    hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#E7E7E1", font=dict(family=FONT_STACK, color="#1A1A18")),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(size=12)),
    margin=dict(l=10, r=10, t=30, b=10),
    height=400,
    xaxis=dict(showgrid=False, linecolor="#E7E7E1", tickformat="%y.%m"),
    yaxis=dict(gridcolor="#EDEDE7", zeroline=False, ticksuffix="%"),
)
st.plotly_chart(line_fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})

# ──────────────────────────────────────────────
# 레이더 차트 + 승부 요약
# ──────────────────────────────────────────────
radar_col, verdict_col = st.columns([1, 1])

AXES = ["수익률", "최근 모멘텀", "안정성", "낙폭 방어", "거래대금"]
score_table = {
    "수익률": relative_scores([s["return"] for s in stocks]),
    "최근 모멘텀": relative_scores([s["momentum"] for s in stocks]),
    "안정성": relative_scores([s["volatility"] for s in stocks], invert=True),
    "낙폭 방어": relative_scores([s["mdd"] for s in stocks]),
    "거래대금": relative_scores([s["trade_value"] for s in stocks]),
}

with radar_col:
    st.markdown('<div class="section-label">강점 비교</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="chart-note">비교 종목끼리의 상대 점수(0~100)예요. 축이 넓을수록 그 항목이 상대적으로 강했어요.</div>',
        unsafe_allow_html=True,
    )
    radar_fig = go.Figure()
    for i, s in enumerate(stocks):
        r = [score_table[a][i] for a in AXES]
        c = s["color"].lstrip("#")
        rgb = tuple(int(c[j : j + 2], 16) for j in (0, 2, 4))
        radar_fig.add_trace(
            go.Scatterpolar(
                r=r + r[:1],
                theta=AXES + AXES[:1],
                name=s["name"],
                line=dict(color=s["color"], width=1.6),
                fill="toself",
                fillcolor=f"rgba({rgb[0]},{rgb[1]},{rgb[2]},0.10)",
                hovertemplate="%{theta}: %{r:.0f}점<extra>" + s["name"] + "</extra>",
            )
        )
    radar_fig.update_layout(
        font=dict(family=FONT_STACK, color="#6E6E67", size=12),
        paper_bgcolor="rgba(0,0,0,0)",
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(range=[0, 100], showticklabels=False, gridcolor="#EDEDE7", linecolor="#E7E7E1"),
            angularaxis=dict(gridcolor="#EDEDE7", linecolor="#E7E7E1", tickfont=dict(size=12, color="#6E6E67")),
        ),
        legend=dict(orientation="h", yanchor="bottom", y=-0.18, x=0, font=dict(size=12)),
        margin=dict(l=40, r=40, t=30, b=30),
        height=400,
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#E7E7E1", font=dict(family=FONT_STACK, color="#1A1A18")),
    )
    st.plotly_chart(radar_fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})

with verdict_col:
    st.markdown('<div class="section-label">승부 요약</div>', unsafe_allow_html=True)
    if len(stocks) >= 2:
        ret_winner = max(stocks, key=lambda s: s["return"])
        stab_winner = min(stocks, key=lambda s: s["volatility"])
        mdd_winner = max(stocks, key=lambda s: s["mdd"])
        mom_winner = max(stocks, key=lambda s: s["momentum"])
        liq_winner = max(stocks, key=lambda s: s["trade_value"])

        headline = f"{period_label} 수익률은 {ret_winner['name']} 승, 안정성은 {stab_winner['name']} 승!"
        if ret_winner["symbol"] == stab_winner["symbol"]:
            headline = f"{period_label} 동안은 수익률과 안정성 모두 {ret_winner['name']} 승이었어요."

        def detail(fmt):
            return " · ".join(f"{s['name']} {fmt(s)}" for s in stocks)

        others_ret = detail(lambda s: fmt_pct(s["return"]))
        others_vol = detail(lambda s: f"{s['volatility']:.1f}%")
        others_mdd = detail(lambda s: f"{s['mdd']:.1f}%")
        others_mom = detail(lambda s: fmt_pct(s["momentum"]))

        rows = [
            ("기간 수익률", ret_winner["name"], others_ret),
            ("안정성(변동성↓)", stab_winner["name"], others_vol),
            ("낙폭 방어", mdd_winner["name"], others_mdd),
            ("최근 모멘텀", mom_winner["name"], others_mom),
            ("거래대금", liq_winner["name"], "거래가 더 활발했어요"),
        ]
        rows_html = "".join(
            f'<div class="verdict-row"><span class="verdict-metric">{metric}</span>'
            f'<span class="verdict-result"><span class="verdict-winner">{winner} 승</span> {detail}</span></div>'
            for metric, winner, detail in rows
        )
        st.markdown(
            f'<div class="verdict-card"><div class="verdict-headline">{headline}</div>{rows_html}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="chart-note" style="margin-top:0.5rem">'
            "※ 선택한 기간의 과거 데이터만 비교한 결과예요. 미래 성과와는 무관해요.</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="verdict-card"><div class="verdict-headline">비교하려면 종목이 2개 이상 필요해요.</div>'
            '<div class="chart-note">티커를 하나 더 입력하면 승부 요약을 보여드릴게요.</div></div>',
            unsafe_allow_html=True,
        )

# ──────────────────────────────────────────────
# 푸터: 면책 + CTA
# ──────────────────────────────────────────────
st.markdown(
    """
<div class="app-footer">
  본 페이지는 과거 시세 데이터를 기반으로 한 단순 비교 자료이며, 특정 종목에 대한 매수·매도 추천이나 투자 자문이 아닙니다.
  과거의 성과는 미래의 수익을 보장하지 않으며, 모든 투자 판단과 책임은 투자자 본인에게 있습니다.
  데이터 출처: Yahoo Finance (지연·오차가 있을 수 있어요)<br><br>
  더 많은 투자 이야기 → <a href="https://hyorang.com" target="_blank" rel="noopener">hyorang.com</a>
</div>
""",
    unsafe_allow_html=True,
)
