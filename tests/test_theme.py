"""Tests for desktop theme detection."""

import os
import tempfile
import textwrap
import pytest
from unittest.mock import patch

from pulse.utils.theme import _rgb, _load_kde, load_theme, Theme, _DARK_DEFAULT


class TestRgbConversion:
    def test_basic(self):
        assert _rgb("124,168,112") == "#7ca870"

    def test_with_spaces(self):
        assert _rgb("28, 21, 17") == "#1c1511"

    def test_black(self):
        assert _rgb("0,0,0") == "#000000"

    def test_white(self):
        assert _rgb("255,255,255") == "#ffffff"


class TestKdeTheme:
    _KDE_CONFIG = textwrap.dedent("""\
        [Colors:Window]
        BackgroundNormal=28,21,17
        BackgroundAlternate=42,32,25
        ForegroundNormal=232,216,176
        DecorationFocus=124,168,112
        ForegroundNeutral=200,152,88
        ForegroundNegative=200,120,104
        ForegroundInactive=138,112,96
    """)

    def test_parses_colours(self, tmp_path):
        cfg = tmp_path / "kdeglobals"
        cfg.write_text(self._KDE_CONFIG)
        with patch("pulse.utils.theme.os.path.expanduser", return_value=str(cfg)):
            theme = _load_kde()
        assert theme is not None
        assert theme.bg == "#1c1511"
        assert theme.bg_panel == "#2a2019"
        assert theme.fg == "#e8d8b0"
        assert theme.accent == "#7ca870"
        assert theme.warn == "#c89858"
        assert theme.danger == "#c87868"
        assert theme.muted == "#8a7060"

    def test_returns_none_if_missing(self, tmp_path):
        with patch("pulse.utils.theme.os.path.expanduser", return_value=str(tmp_path / "nope")):
            assert _load_kde() is None

    def test_uses_defaults_on_missing_keys(self, tmp_path):
        # File exists with [Colors:Window] section but no colour keys →
        # function should still return a Theme using built-in defaults.
        cfg = tmp_path / "kdeglobals"
        cfg.write_text("[Colors:Window]\nUnknownKey=whatever\n")
        with patch("pulse.utils.theme.os.path.expanduser", return_value=str(cfg)):
            result = _load_kde()
        assert isinstance(result, Theme)

    def test_returns_none_on_no_window_section(self, tmp_path):
        cfg = tmp_path / "kdeglobals"
        cfg.write_text("[OtherSection]\nfoo=bar\n")
        with patch("pulse.utils.theme.os.path.expanduser", return_value=str(cfg)):
            result = _load_kde()
        assert result is None


class TestLoadTheme:
    def test_returns_theme_dataclass(self):
        theme = load_theme()
        assert isinstance(theme, Theme)

    def test_all_colours_are_hex(self):
        theme = load_theme()
        for field in ("bg", "bg_panel", "fg", "accent", "warn", "danger", "muted"):
            val = getattr(theme, field)
            assert val.startswith("#"), f"{field} = {val!r} is not a hex colour"
            assert len(val) == 7, f"{field} = {val!r} wrong length"

    def test_gauge_colors_dict_keys(self):
        theme = load_theme()
        keys = theme.gauge_colors().keys()
        assert set(keys) == {"accent", "warn_color", "danger", "muted", "fg"}

    def test_fallback_when_no_desktop_config(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CURRENT_DESKTOP", "")
        with patch("pulse.utils.theme.os.path.exists", return_value=False):
            theme = load_theme()
        assert theme == _DARK_DEFAULT
