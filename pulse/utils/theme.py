"""Desktop theme detection — reads live config each call so theme changes are picked up."""

import os
import configparser
from dataclasses import dataclass
from typing import Optional


@dataclass
class Theme:
    bg: str
    bg_panel: str
    fg: str
    accent: str
    warn: str
    danger: str
    muted: str

    def gauge_colors(self) -> dict:
        return {
            "accent": self.accent,
            "warn_color": self.warn,
            "danger": self.danger,
            "muted": self.muted,
            "fg": self.fg,
        }


# ── helpers ──────────────────────────────────────────────────────────────────

def _rgb(s: str) -> str:
    r, g, b = (int(x.strip()) for x in s.split(","))
    return f"#{r:02x}{g:02x}{b:02x}"


# ── KDE ──────────────────────────────────────────────────────────────────────

def _load_kde() -> Optional[Theme]:
    path = os.path.expanduser("~/.config/kdeglobals")
    if not os.path.exists(path):
        return None
    try:
        cfg = configparser.RawConfigParser()
        cfg.read(path)
        w = cfg["Colors:Window"]
        # DecorationFocus is the accent/highlight colour in most KDE themes
        raw_accent = (
            w.get("DecorationFocus")
            or w.get("ForegroundActive")
            or "124,168,112"
        )
        return Theme(
            bg=_rgb(w.get("BackgroundNormal", "28,21,17")),
            bg_panel=_rgb(w.get("BackgroundAlternate", "42,32,25")),
            fg=_rgb(w.get("ForegroundNormal", "232,216,176")),
            accent=_rgb(raw_accent),
            warn=_rgb(w.get("ForegroundNeutral", "200,152,88")),
            danger=_rgb(w.get("ForegroundNegative", "200,120,104")),
            muted=_rgb(w.get("ForegroundInactive", "138,112,96")),
        )
    except (KeyError, ValueError):
        return None


# ── GTK (GNOME / other desktops) ─────────────────────────────────────────────

def _load_gtk() -> Optional[Theme]:
    """Return a dark or light fallback palette based on the GTK preference."""
    path = os.path.expanduser("~/.config/gtk-3.0/settings.ini")
    if not os.path.exists(path):
        path = os.path.expanduser("~/.config/gtk-4.0/settings.ini")
    if not os.path.exists(path):
        return None
    try:
        cfg = configparser.RawConfigParser()
        cfg.read(path)
        dark_pref = cfg.get("Settings", "gtk-application-prefer-dark-theme", fallback="0")
        return _DARK_DEFAULT if dark_pref.strip() in ("1", "true", "True") else _LIGHT_DEFAULT
    except Exception:
        return None


# ── defaults ─────────────────────────────────────────────────────────────────

_DARK_DEFAULT = Theme(
    bg="#1c1511", bg_panel="#2a2019", fg="#e8d8b0",
    accent="#7ca870", warn="#c89858", danger="#c87868", muted="#8a7060",
)

_LIGHT_DEFAULT = Theme(
    bg="#f5f0e8", bg_panel="#ede8dc", fg="#2a2019",
    accent="#3a6e30", warn="#7a5010", danger="#8a1010", muted="#7a6a5a",
)


# ── public API ───────────────────────────────────────────────────────────────

def load_theme() -> Theme:
    """Detect and return the current desktop theme colours.

    Reads live config files so the result reflects the theme in use right now.
    Priority: KDE → GTK → dark fallback.
    """
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()

    if "kde" in desktop or os.path.exists(os.path.expanduser("~/.config/kdeglobals")):
        theme = _load_kde()
        if theme:
            return theme

    theme = _load_gtk()
    if theme:
        return theme

    return _DARK_DEFAULT
