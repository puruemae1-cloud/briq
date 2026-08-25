#!/usr/bin/env python3
"""Unit tests for Prada RTW size extraction / mixed-size guard."""
from __future__ import annotations

import unittest

from pr_sizes import (
    MixedRtwSizesError,
    assert_no_mixed_rtw_sizes,
    has_mixed_rtw_sizes,
    sizes_from_hit,
    sizes_from_pdp_html,
)


class TestPrSizes(unittest.TestCase):
    def test_sizes_from_hit_drops_chart_letters_when_numeric_store(self) -> None:
        hit = {
            "SizeGroupStore": {"en_GB": ["S", "M", "L", "XL", "XXL"]},
            "availableSizesStore": [
                {"label": "48", "code": "4407"},
                {"label": "50", "code": "4408"},
                {"label": "52", "code": "4409"},
            ],
            "availableSizes": [
                {"label": "48", "code": "4407"},
                {"label": "50", "code": "4408"},
            ],
        }
        labels = [r["size"] for r in sizes_from_hit(hit)]
        self.assertEqual(labels, ["48", "50", "52"])
        self.assertFalse(has_mixed_rtw_sizes(labels))

    def test_sizes_from_hit_keeps_letter_only_products(self) -> None:
        hit = {
            "SizeGroupStore": {"en_GB": ["S", "M", "L", "XL"]},
            "availableSizesStore": [
                {"label": "S", "code": "0902"},
                {"label": "M", "code": "0903"},
                {"label": "L", "code": "0904"},
                {"label": "XL", "code": "0905"},
            ],
            "availableSizes": [{"label": "L", "code": "0904"}],
        }
        labels = [r["size"] for r in sizes_from_hit(hit)]
        self.assertEqual(labels, ["S", "M", "L", "XL"])

    def test_pdp_html_parses_short_and_regular(self) -> None:
        html = """
        <button aria-label="Select size 46S" disabled><span>46S</span></button>
        <button aria-label="Select size 46" disabled><span>46</span></button>
        <button aria-label="Select size 48S" disabled><span>48S</span></button>
        <button aria-label="Select size 48"><span>48</span></button>
        <button aria-label="Select size 50"><span>50</span></button>
        """
        rows = sizes_from_pdp_html(html)
        labels = [r["size"] for r in rows]
        self.assertEqual(labels, ["46S", "46", "48S", "48", "50"])
        self.assertTrue(rows[3]["inStock"])
        self.assertFalse(rows[0]["inStock"])

    def test_assert_no_mixed_rtw_sizes_raises(self) -> None:
        products = [
            {
                "id": "GEB310",
                "sizes": [
                    {"size": "S"},
                    {"size": "M"},
                    {"size": "48"},
                    {"size": "50"},
                ],
            }
        ]
        with self.assertRaises(MixedRtwSizesError):
            assert_no_mixed_rtw_sizes(products, context="test")

    def test_assert_no_mixed_rtw_sizes_ok(self) -> None:
        products = [
            {"id": "A", "sizes": [{"size": "48"}, {"size": "48S"}, {"size": "50"}]},
            {"id": "B", "variants": [{"size": "S"}, {"size": "M"}, {"size": "L"}]},
        ]
        assert_no_mixed_rtw_sizes(products, context="test")


if __name__ == "__main__":
    unittest.main()
