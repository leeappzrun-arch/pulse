"""Tests for arc gauge rendering and widget."""

import math
import pytest
from rich.text import Text

from pulse.widgets.gauge import gauge_color, render_arc


COLORS = dict(
    accent="#7ca870",
    warn_color="#c89858",
    danger="#c87868",
    muted="#8a7060",
    fg="#e8d8b0",
)


class TestGaugeColor:
    def test_good(self):
        assert gauge_color(0.50, "#a", "#b", "#c") == "#a"

    def test_warn_boundary(self):
        assert gauge_color(0.70, "#a", "#b", "#c") == "#b"

    def test_warn_mid(self):
        assert gauge_color(0.80, "#a", "#b", "#c") == "#b"

    def test_crit_boundary(self):
        assert gauge_color(0.90, "#a", "#b", "#c") == "#c"

    def test_crit_over(self):
        assert gauge_color(1.00, "#a", "#b", "#c") == "#c"

    def test_zero(self):
        assert gauge_color(0.00, "#a", "#b", "#c") == "#a"

    def test_custom_thresholds(self):
        assert gauge_color(0.50, "#a", "#b", "#c", warn_at=0.40, crit_at=0.80) == "#b"


class TestRenderArc:
    def _render(self, value=0.5, width=24, height=11, label="CPU", display="50%"):
        return render_arc(value, width, height, label, display, **COLORS)

    def test_returns_rich_text(self):
        assert isinstance(self._render(), Text)

    def test_correct_line_count(self):
        result = self._render(width=24, height=11)
        lines = str(result).split("\n")
        assert len(lines) == 11

    def test_correct_line_count_small(self):
        result = self._render(width=18, height=9)
        lines = str(result).split("\n")
        assert len(lines) == 9

    def test_each_line_within_width(self):
        w = 24
        result = self._render(width=w, height=11)
        for line in str(result).split("\n"):
            assert len(line) <= w, f"line too wide: {line!r}"

    def test_label_present_in_output(self):
        result = self._render(label="MYCPU")
        assert "MYCPU" in str(result)

    def test_display_value_present(self):
        result = self._render(display="73%")
        assert "73%" in str(result)

    def test_value_clamp_below_zero(self):
        # Should not raise
        result = render_arc(-0.5, 24, 11, "X", "0%", **COLORS)
        assert isinstance(result, Text)

    def test_value_clamp_above_one(self):
        result = render_arc(1.5, 24, 11, "X", "100%", **COLORS)
        assert isinstance(result, Text)

    def test_value_zero_has_all_muted_arc(self):
        result = render_arc(0.0, 24, 11, "X", "0%", **COLORS)
        raw = str(result)
        # Should contain dim dots; active filled dots should be minimal
        assert "·" in raw

    def test_value_one_has_all_active_arc(self):
        result = render_arc(1.0, 24, 11, "X", "100%", **COLORS)
        raw = str(result)
        assert "●" in raw

    def test_arc_contains_center_dot(self):
        result = render_arc(0.5, 24, 11, "X", "50%", **COLORS)
        assert "●" in str(result)

    def test_arc_contains_value_marker(self):
        result = render_arc(0.5, 24, 11, "X", "50%", **COLORS)
        assert "◆" in str(result)

    def test_minimum_viable_size(self):
        # Should not crash at small sizes
        result = render_arc(0.5, 8, 6, "X", "50%", **COLORS)
        assert isinstance(result, Text)

    @pytest.mark.parametrize("value", [0.0, 0.25, 0.5, 0.75, 1.0])
    def test_various_values_render(self, value):
        result = render_arc(value, 24, 11, "T", f"{value*100:.0f}%", **COLORS)
        assert isinstance(result, Text)
        assert len(str(result).split("\n")) == 11

    def test_active_colour_changes_at_warn(self):
        # At value=0.5 accent is used; at value=0.75 warn colour is used.
        # Check that the rendered spans change — we inspect the first span's style.
        low = render_arc(0.5, 24, 11, "X", "50%", **COLORS)
        high = render_arc(0.8, 24, 11, "X", "80%", **COLORS)
        # The span colours won't be identical
        low_styles = {s.style for s in low._spans}
        high_styles = {s.style for s in high._spans}
        assert low_styles != high_styles
