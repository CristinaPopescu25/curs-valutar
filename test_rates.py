"""Teste unitare pentru parsarea și conversia cursurilor oficiale."""

from __future__ import annotations

import unittest

from rates import parse_bnr_history, parse_bnr_xml, parse_ecb_history, parse_ecb_payload

BNR_SAMPLE = """<?xml version="1.0" encoding="utf-8"?>
<DataSet xmlns="https://www.bnr.ro/xsd">
  <Header><Publisher>National Bank of Romania</Publisher></Header>
  <Body>
    <Cube date="2026-11-24">
      <Rate currency="EUR">5.3427</Rate>
      <Rate currency="USD">4.5000</Rate>
      <Rate currency="HUF" multiplier="100">1.4457</Rate>
    </Cube>
  </Body>
</DataSet>
"""


class BnrTests(unittest.TestCase):
    def setUp(self) -> None:
        self.table = parse_bnr_xml(BNR_SAMPLE)

    def test_parse_multiplier_and_namespace(self) -> None:
        self.assertEqual(self.table.source, "BNR")
        self.assertEqual(self.table.date, "2026-11-24")
        self.assertEqual(self.table.base, "RON")
        self.assertAlmostEqual(self.table.rates["EUR"], 5.3427)
        self.assertAlmostEqual(self.table.rates["HUF"], 0.014457)
        self.assertEqual(self.table.rates["RON"], 1.0)

    def test_conversions(self) -> None:
        self.assertAlmostEqual(self.table.convert(100, "EUR", "RON"), 534.27, places=4)
        self.assertAlmostEqual(self.table.convert(100, "RON", "EUR"), 18.717128, places=4)
        self.assertAlmostEqual(self.table.convert(1000, "HUF", "RON"), 14.457, places=4)
        self.assertEqual(self.table.convert(42, "EUR", "EUR"), 42)

    def test_unknown_currency(self) -> None:
        with self.assertRaises(ValueError):
            self.table.convert(10, "XYZ", "RON")


class HistoryTests(unittest.TestCase):
    def test_bnr_history_sorted_and_multiplier(self) -> None:
        payload = """<?xml version="1.0" encoding="utf-8"?>
        <DataSet xmlns="https://www.bnr.ro/xsd"><Body>
          <Cube date="2026-11-24"><Rate currency="EUR">5.3427</Rate><Rate currency="HUF" multiplier="100">1.4457</Rate></Cube>
          <Cube date="2026-11-23"><Rate currency="EUR">5.3483</Rate><Rate currency="HUF" multiplier="100">1.4470</Rate></Cube>
        </Body></DataSet>"""
        tables = parse_bnr_history(payload)
        self.assertEqual([t.date for t in tables], ["2026-11-23", "2026-11-24"])
        self.assertAlmostEqual(tables[0].base_per_unit("EUR"), 5.3483)
        self.assertAlmostEqual(tables[1].base_per_unit("HUF"), 0.014457)

    def test_ecb_history(self) -> None:
        data = {"rates": {"2026-11-23": {"RON": 5.3483}, "2026-11-24": {"RON": 5.3442, "USD": 1.16}}}
        self.assertEqual(parse_ecb_history(data, "RON"), [("2026-11-23", 5.3483), ("2026-11-24", 5.3442)])


class EcbTests(unittest.TestCase):
    def setUp(self) -> None:
        self.table = parse_ecb_payload(
            {"amount": 1.0, "base": "EUR", "date": "2026-11-24", "rates": {"RON": 5.3442, "USD": 1.1600}}
        )

    def test_parse_base_eur(self) -> None:
        self.assertEqual(self.table.base, "EUR")
        self.assertEqual(self.table.date, "2026-11-24")
        self.assertAlmostEqual(self.table.rates["EUR"], 1.0)
        self.assertAlmostEqual(self.table.units_per_base("RON"), 5.3442, places=4)

    def test_conversions(self) -> None:
        self.assertAlmostEqual(self.table.convert(100, "EUR", "RON"), 534.42, places=4)
        self.assertAlmostEqual(self.table.convert(100, "EUR", "USD"), 116.0, places=4)
        self.assertAlmostEqual(self.table.convert(100, "RON", "EUR"), 18.712, places=3)


if __name__ == "__main__":
    unittest.main()
