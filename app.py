"""Convertor valutar în stil dashboard, cu cursuri oficiale BNR și BCE."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from rates import (
    ECB_REFERENCE_URL,
    RateTable,
    fetch_bnr,
    fetch_bnr_history,
    fetch_ecb,
    fetch_ecb_history,
)

st.set_page_config(
    page_title="Curs Valutar",
    page_icon="💱",
    layout="centered",
    initial_sidebar_state="collapsed",
)

CURRENCY_LABELS = {
    "AED": "🇦🇪 Dirham",
    "AUD": "🇦🇺 Dolar australian",
    "BGN": "🇧🇬 Levă bulgărească",
    "BRL": "🇧🇷 Real brazilian",
    "CAD": "🇨🇦 Dolar canadian",
    "CHF": "🇨🇭 Franc elvețian",
    "CNY": "🇨🇳 Yuan chinezesc",
    "CZK": "🇨🇿 Coroană cehă",
    "DKK": "🇩🇰 Coroană daneză",
    "EGP": "🇪🇬 Liră egipteană",
    "EUR": "🇪🇺 Euro",
    "GBP": "🇬🇧 Liră sterlină",
    "HKD": "🇭🇰 Dolar Hong Kong",
    "HUF": "🇭🇺 Forint",
    "IDR": "🇮🇩 Rupiah indonezian",
    "ILS": "🇮🇱 Shekel",
    "INR": "🇮🇳 Rupie indiană",
    "ISK": "🇮🇸 Coroană islandeză",
    "JPY": "🇯🇵 Yen japonez",
    "KRW": "🇰🇷 Won coreean",
    "MDL": "🇲🇩 Leu moldovenesc",
    "MXN": "🇲🇽 Peso mexican",
    "MYR": "🇲🇾 Ringgit malaysian",
    "NOK": "🇳🇴 Coroană norvegiană",
    "NZD": "🇳🇿 Dolar neozeelandez",
    "PLN": "🇵🇱 Zlot polonez",
    "RON": "🇷🇴 Leu românesc",
    "SEK": "🇸🇪 Coroană suedeză",
    "SGD": "🇸🇬 Dolar singaporez",
    "THB": "🇹🇭 Baht thailandez",
    "TRY": "🇹🇷 Liră turcească",
    "UAH": "🇺🇦 Grivnă ucraineană",
    "USD": "🇺🇸 Dolar american",
    "ZAR": "🇿🇦 Rand sud-african",
}

CUSTOM_CSS = """
<style>
  [data-testid="stAppViewContainer"] { background: #0e1512; }
  [data-testid="stMainBlockContainer"] { max-width: 560px; padding-top: 1.4rem; padding-bottom: 2rem; }
  [data-testid="stContainerBorder"] {
    background: #141e18;
    border: 1px solid #22352a;
    border-radius: 18px;
    padding: 14px 16px;
  }
  .topbar { display:flex; align-items:baseline; justify-content:space-between; gap:10px; margin-bottom:14px; }
  .brand { color:#f1f8f3; font-size:21px; font-weight:700; letter-spacing:-.02em; }
  .brand span { margin-left:6px; }
  .brand-sub { color:#7f9a8a; font-size:12px; text-align:right; }
  .section-title {
    color:#8ba795; font-size:11px; font-weight:700; letter-spacing:.11em;
    text-transform:uppercase; margin:20px 0 9px;
  }
  .hero {
    background: linear-gradient(135deg, #173326 0%, #102019 100%);
    border: 1px solid #2a513b;
    border-radius: 20px;
    padding: 22px 22px 18px;
    margin-top: 12px;
  }
  .hero-label { color:#9db9a8; font-size:11px; font-weight:700; letter-spacing:.11em; text-transform:uppercase; }
  .hero-value { color:#f4fbf6; font-size:31px; font-weight:750; line-height:1.18; margin:10px 0 8px; overflow-wrap:anywhere; }
  .hero-sub { color:#9db9a8; font-size:13px; }
  .hero-meta { display:flex; align-items:center; gap:10px; margin-top:14px; }
  .badge {
    display:inline-block; background:#1d4a33; color:#65e69a;
    border-radius:999px; padding:3px 10px; font-size:11px; font-weight:700; letter-spacing:.04em;
  }
  .hero-date { color:#7f9a8a; font-size:12px; }
  .arrow { color:#4ade80; }
  .card {
    background:#141e18;
    border:1px solid #22352a;
    border-radius:18px;
    padding:4px 16px;
  }
  .rate-row { display:flex; align-items:center; gap:12px; padding:11px 0; border-bottom:1px solid #1f3026; }
  .rate-row:last-child { border-bottom:none; }
  .avatar {
    width:38px; height:38px; flex-shrink:0; border-radius:50%;
    background:#1d3327; display:flex; align-items:center; justify-content:center; font-size:18px;
  }
  .rate-info { flex:1; min-width:0; }
  .rate-code { color:#eaf5ee; font-size:14px; font-weight:650; }
  .rate-name { color:#7f9a8a; font-size:12px; }
  .rate-value { color:#4ade80; font-size:14px; font-weight:650; white-space:nowrap; }
  [data-testid="stButton"] button { border-radius:12px; }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_data(ttl=3600, show_spinner="Descarc cursul oficial…")
def load_rates(source: str) -> RateTable:
    """Cache de o oră, partajat de toți utilizatorii aplicației."""
    return fetch_bnr() if source == "BNR" else fetch_ecb()


@st.cache_data(ttl=21600, show_spinner=False)
def load_bnr_history() -> list[RateTable]:
    """Ultimele 10 zile bancare publicate de BNR."""
    return fetch_bnr_history()


@st.cache_data(ttl=21600, show_spinner=False)
def load_ecb_history(source: str, target: str) -> list[tuple[str, float]]:
    """Ultima lună de cursuri de referință BCE."""
    return fetch_ecb_history(source, target)


def label(code: str) -> str:
    return f"{CURRENCY_LABELS.get(code, code)}  ·  {code}"


def parts(code: str) -> tuple[str, str]:
    value = CURRENCY_LABELS.get(code, code)
    if " " in value:
        flag, currency_name = value.split(" ", 1)
        return flag, currency_name
    return "💱", value


def money(value: float) -> str:
    """Formatare cu precizie adaptată la valori mici (ex. IDR → RON)."""
    magnitude = abs(value)
    decimals = 8 if magnitude < 0.01 else 6 if magnitude < 1 else 4 if magnitude < 1000 else 2
    return f"{value:,.{decimals}f}".rstrip("0").rstrip(".")


def swap_currencies() -> None:
    """Callback apelat înainte de instantierea widget-urilor."""
    st.session_state["src"], st.session_state["dst"] = st.session_state["dst"], st.session_state["src"]


def history_series(table: RateTable, source_ccy: str, target_ccy: str) -> list[tuple[str, float]]:
    """Evoluția cursului 1 sursă = X țintă, din sursa oficială curentă."""
    try:
        if table.source == "BNR":
            points: list[tuple[str, float]] = []
            for day_table in load_bnr_history():
                try:
                    points.append(
                        (
                            day_table.date,
                            day_table.base_per_unit(source_ccy) / day_table.base_per_unit(target_ccy),
                        )
                    )
                except ValueError:
                    continue
            return points[-12:]
        if source_ccy == target_ccy:
            return []
        return load_ecb_history(source_ccy, target_ccy)[-12:]
    except Exception:
        return []


st.markdown(
    '<div class="topbar"><div class="brand">💱 <span>Curs Valutar</span></div>'
    '<div class="brand-sub">Cursuri oficiale<br>BNR &amp; BCE</div></div>',
    unsafe_allow_html=True,
)

source = st.segmented_control(
    "Sursa cursului",
    ("BNR", "BCE"),
    default="BNR",
    label_visibility="collapsed",
) or "BNR"

try:
    table = load_rates(source)
except Exception as exc:  # fallback automat între surse
    fallback = "BCE" if source == "BNR" else "BNR"
    st.warning(f"Sursa {source} nu este disponibilă momentan. Încerc {fallback}…")
    try:
        table = load_rates(fallback)
    except Exception as exc2:
        st.error(f"Nu pot prelua cursurile. Detalii: {exc2}")
        with st.expander("Eroare sursă primară"):
            st.code(str(exc))
        st.stop()
    source = fallback

codes = table.currencies()
for key, default in (("src", "EUR"), ("dst", "RON")):
    if st.session_state.get(key) not in codes:
        st.session_state[key] = default if default in codes else codes[0]

st.markdown('<div class="section-title">Conversie</div>', unsafe_allow_html=True)
with st.container(border=True):
    amount = st.number_input("Suma de convertit", min_value=0.0, value=100.0, step=10.0, format="%.2f")
    left, right = st.columns(2, gap="small")
    with left:
        source_ccy = st.selectbox("Din", codes, key="src", format_func=label)
    with right:
        target_ccy = st.selectbox("În", codes, key="dst", format_func=label)
    st.button("⇄  Schimbă sensul", use_container_width=True, on_click=swap_currencies)

try:
    result = table.convert(amount, source_ccy, target_ccy)
    unit_rate = table.base_per_unit(source_ccy) / table.base_per_unit(target_ccy)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

st.markdown(
    f"""
    <div class="hero">
      <div class="hero-label">Rezultat conversie</div>
      <div class="hero-value">{money(amount)} {source_ccy} <span class="arrow">→</span> {money(result)} {target_ccy}</div>
      <div class="hero-sub">1 {source_ccy} = {money(unit_rate)} {target_ccy}</div>
      <div class="hero-meta"><span class="badge">{table.source}</span>
      <span class="hero-date">curs din {table.date}</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="section-title">Evoluția cursului</div>', unsafe_allow_html=True)
series = history_series(table, source_ccy, target_ccy)
with st.container(border=True):
    if len(series) >= 2:
        frame = pd.Series(
            [value for _, value in series],
            index=pd.to_datetime([day for day, _ in series]),
            name=f"1 {source_ccy} = {target_ccy}",
        )
        st.area_chart(frame, width="stretch", height=210)
        st.caption(f"1 {source_ccy} în {target_ccy} · ultimele {len(series)} zile · {table.source}")
    else:
        st.info("Nu sunt suficiente date istorice pentru această pereche de valute.")

st.markdown('<div class="section-title">Cursuri populare</div>', unsafe_allow_html=True)
if table.base == "RON":
    popular = [(code, table.base_per_unit(code), "RON") for code in ("EUR", "USD", "GBP", "CHF", "JPY") if code in table.rates]
else:
    popular = [(code, table.units_per_base(code), code) for code in ("RON", "USD", "GBP", "CHF", "JPY") if code in table.rates]

rows_html = "".join(
    f'<div class="rate-row"><div class="avatar">{parts(code)[0]}</div>'
    f'<div class="rate-info"><div class="rate-code">{code}</div>'
    f'<div class="rate-name">{parts(code)[1]}</div></div>'
    f'<div class="rate-value">{money(value)} {unit}</div></div>'
    for code, value, unit in popular
)
st.markdown(f'<div class="card">{rows_html}</div>', unsafe_allow_html=True)

if st.button("🔄  Actualizează cursul", use_container_width=True):
    load_rates.clear()
    load_bnr_history.clear()
    load_ecb_history.clear()
    st.rerun()

st.caption(
    "Cursurile sunt de referință (BNR / BCE). Băncile și casele de schimb pot aplica "
    "alte cursuri în tranzacțiile reale."
)
st.markdown(f"[Sursa oficială]({table.url}) · [BNR](https://www.bnr.ro/) · [BCE]({ECB_REFERENCE_URL})")
