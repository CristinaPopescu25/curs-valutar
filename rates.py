"""Preluarea cursurilor oficiale și logica de conversie.

Surse utilizate:
    * BNR (Banca Națională a României) - fișierul XML public de pe curs.bnr.ro.
    * BCE (Banca Centrală Europeană) - cursurile de referință EUR, prin API-ul
      Frankfurter (care republicează datele oficiale BCE).

Ambele surse sunt normalizate într-un obiect `RateTable` în care
`rates[moneda]` reprezintă câte unități din baza tabelului costă o unitate
din moneda respectivă. Astfel conversia este aceeași pentru ambele surse.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass

import requests

BNR_URL = "https://curs.bnr.ro/nbrfxrates.xml"
ECB_API_URL = "https://api.frankfurter.app/latest"
ECB_REFERENCE_URL = (
    "https://www.ecb.europa.eu/stats/policy_and_exchange_rates/"
    "euro_reference_exchange_rates/html/index.en.html"
)
REQUEST_TIMEOUT = 15
_HEADERS = {
    "User-Agent": "CursValutar/1.0 (Streamlit app)",
    "Accept": "application/xml,text/xml,application/json",
}


@dataclass(frozen=True)
class RateTable:
    """Tabel de cursuri cu o bază comună (RON pentru BNR, EUR pentru BCE)."""

    source: str
    date: str
    base: str
    rates: dict[str, float]
    url: str

    def currencies(self) -> list[str]:
        return sorted({self.base, *self.rates})

    def base_per_unit(self, currency: str) -> float:
        """Câte unități din bază costă 1 unitate din `currency`."""
        code = currency.upper()
        if code == self.base:
            return 1.0
        try:
            return self.rates[code]
        except KeyError as exc:
            raise ValueError(f"Moneda {code} nu există în cursul {self.source}.") from exc

    def units_per_base(self, currency: str) -> float:
        """Câte unități din `currency` costă 1 unitate din bază."""
        return 1.0 / self.base_per_unit(currency)

    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        """Convertește `amount` dintr-o monedă în alta."""
        if amount < 0:
            raise ValueError("Suma trebuie să fie pozitivă.")
        source_rate = self.base_per_unit(from_currency)
        target_rate = self.base_per_unit(to_currency)
        if source_rate <= 0 or target_rate <= 0:
            raise ValueError("Curs invalid primit de la sursă.")
        return amount * source_rate / target_rate


def _local_name(tag: str) -> str:
    """Returnează numele etichetei fără namespace (BNR și-a schimbat namespace-ul)."""
    return tag.rsplit("}", 1)[-1]


def _to_float(text: str | None) -> float:
    return float((text or "").strip().replace(",", "."))


def parse_bnr_xml(payload: bytes | str) -> RateTable:
    """Parsează feed-ul XML oficial BNR.

    BNR exprimă cursul ca „RON pentru `multiplier` unități”; valoarea este
    împărțită la multiplier pentru a obține „RON pentru 1 unitate”.
    """
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8-sig")
    root = ET.fromstring(payload)
    cubes = [node for node in root.iter() if _local_name(node.tag) == "Cube" and node.get("date")]
    if not cubes:
        raise ValueError("Feed-ul BNR nu conține cursuri (răspuns neașteptat).")

    cube = cubes[0]  # în feed-urile cu mai multe zile, prima este cea mai recentă
    rates: dict[str, float] = {}
    for node in cube:
        if _local_name(node.tag) != "Rate":
            continue
        code = (node.get("currency") or "").strip().upper()
        if not code:
            continue
        try:
            value = _to_float(node.text)
            multiplier = _to_float(node.get("multiplier", "1"))
        except ValueError as exc:
            raise ValueError(f"Valoare invalidă pentru {code} în feed-ul BNR.") from exc
        if value > 0 and multiplier > 0:
            rates[code] = value / multiplier

    if not rates:
        raise ValueError("Feed-ul BNR nu conține cursuri valide.")
    rates["RON"] = 1.0
    return RateTable(source="BNR", date=cube.attrib["date"], base="RON", rates=rates, url=BNR_URL)


def fetch_bnr() -> RateTable:
    """Descarcă ultimul curs oficial BNR."""
    response = requests.get(BNR_URL, timeout=REQUEST_TIMEOUT, headers=_HEADERS)
    response.raise_for_status()
    return parse_bnr_xml(response.content)


def parse_ecb_payload(data: dict) -> RateTable:
    """Convertește răspunsul Frankfurter (bază EUR) în RateTable."""
    try:
        date = str(data["date"])
        raw_rates = dict(data["rates"])
    except (KeyError, TypeError) as exc:
        raise ValueError("Răspunsul BCE/Frankfurter este invalid.") from exc

    raw_rates["EUR"] = 1.0
    rates: dict[str, float] = {}
    for code, value in raw_rates.items():
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Curs invalid pentru {code}.") from exc
        if number > 0:
            rates[code.upper()] = 1.0 / number

    return RateTable(source="BCE", date=date, base="EUR", rates=rates, url=ECB_REFERENCE_URL)


def fetch_ecb() -> RateTable:
    """Descarcă ultimul curs de referință BCE prin Frankfurter."""
    response = requests.get(
        ECB_API_URL,
        params={"from": "EUR"},
        timeout=REQUEST_TIMEOUT,
        headers=_HEADERS,
    )
    response.raise_for_status()
    return parse_ecb_payload(response.json())
