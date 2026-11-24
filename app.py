"""Convertor valutar pentru browser, cu cursuri oficiale BNR și BCE."""

from __future__ import annotations

import streamlit as st

from rates import ECB_REFERENCE_URL, RateTable, fetch_bnr, fetch_ecb

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


@st.cache_data(ttl=3600, show_spinner="Descarc cursul oficial…")
def load_rates(source: str) -> RateTable:
    """Cache de o oră, partajat de toți utilizatorii aplicației.

    BNR publică cursul după ora 13:00 în zilele bancare și recomandă să nu
    fie interogat feed-ul la fiecare vizualizare, de aceea folosim cache-ul.
    """
    return fetch_bnr() if source == "BNR" else fetch_ecb()


def label(code: str) -> str:
    return f"{CURRENCY_LABELS.get(code, code)}  ·  {code}"


def money(value: float) -> str:
    """Formatare cu precizie adaptată la valori mici (ex. IDR → RON)."""
    magnitude = abs(value)
    decimals = 8 if magnitude < 0.01 else 6 if magnitude < 1 else 4 if magnitude < 1000 else 2
    return f"{value:,.{decimals}f}".rstrip("0").rstrip(".")


def swap_currencies() -> None:
    """Callback apelat înainte de instantierea widget-urilor (evită eroarea de cheie)."""
    st.session_state["src"], st.session_state["dst"] = st.session_state["dst"], st.session_state["src"]


st.title("💱 Convertor valutar")
st.caption("Cursuri oficiale, preluate automat · BNR și Banca Centrală Europeană")

source = st.radio(
    "Sursa cursului",
    ("BNR", "BCE"),
    horizontal=True,
    help="BNR = cursul oficial al României; BCE = cursurile de referință europene.",
)

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

with st.container(border=True):
    st.markdown(f"### {money(amount)} {source_ccy} → **{money(result)} {target_ccy}**")
    st.caption(
        f"1 {source_ccy} = {money(unit_rate)} {target_ccy}  ·  "
        f"curs din {table.date}  ·  sursă: {table.source}"
    )

st.subheader("Cursuri populare")
popular = ("EUR", "USD", "GBP", "CHF", "JPY") if table.base == "RON" else ("RON", "USD", "GBP", "CHF", "JPY")
if table.base == "RON":
    lines = ["| Monedă | 1 unitate = | În |", "|---|---:|---|"]
    lines += [
        f"| {code} | {money(table.base_per_unit(code))} | RON |"
        for code in popular
        if code in table.rates
    ]
else:
    lines = ["| Monedă | 1 EUR = | În |", "|---|---:|---|"]
    lines += [
        f"| EUR | {money(table.units_per_base(code))} | {code} |"
        for code in popular
        if code in table.rates
    ]
st.markdown("\n".join(lines))

if st.button("🔄  Actualizează cursul", use_container_width=True):
    load_rates.clear()
    st.rerun()

st.caption(
    "Cursurile sunt de referință (BNR / BCE). Băncile și casele de schimb pot aplica "
    "alte cursuri în tranzacțiile reale."
)
st.markdown(f"[Sursa oficială]({table.url}) · [BNR](https://www.bnr.ro/) · [BCE]({ECB_REFERENCE_URL})")

with st.expander("📱  Cum îl folosesc pe telefon"):
    st.markdown(
        "1. Deschide linkul aplicației în Chrome (Android) sau Safari (iPhone).\n"
        "2. Din meniul browserului alege **Add to Home Screen** / **Adaugă pe ecranul de start**.\n"
        "3. Ulterior, aplicația se deschide ca un icon pe telefon, direct în browser."
    )
