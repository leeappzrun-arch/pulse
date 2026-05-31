"""Pulse — system monitor dashboard."""

import pyfiglet
from rich.text import Text as RichText

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static

from .utils.theme import load_theme, Theme
from .utils.stats import StatsCollector
from .widgets.gauge import ArcGauge

_APP_NAME = "PULSE"
_TAGLINE = "system monitor"
_LOGO_FONT = "ansi_shadow"


def _make_logo(theme: Theme) -> RichText:
    raw = pyfiglet.figlet_format(_APP_NAME, font=_LOGO_FONT).rstrip("\n")
    lines = raw.split("\n")
    max_w = max((len(l) for l in lines), default=20)
    full = raw + "\n" + _TAGLINE.center(max_w)
    return RichText(full, style=f"bold {theme.accent}")


class PulseApp(App):
    CSS_PATH = "styles.tcss"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "reload_theme", "Reload theme"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._theme = load_theme()
        self._collector = StatsCollector()

    # ── compose ──────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        colors = self._theme.gauge_colors()

        yield Static(_make_logo(self._theme), id="logo")

        with Horizontal(id="main-row"):
            yield ArcGauge("CPU USAGE", id="cpu", colors=colors)
            yield ArcGauge("RAM USAGE", id="ram", colors=colors)

        with Horizontal(id="secondary-row"):
            yield ArcGauge(
                "CPU TEMP", id="temp",
                warn_at=0.70, crit_at=0.85,
                colors=colors,
            )
            yield ArcGauge("DISK USAGE", id="disk", colors=colors)
            yield ArcGauge("NET  UPLOAD", id="net-up", colors=colors)
            yield ArcGauge("NET DOWNLOAD", id="net-dn", colors=colors)

    # ── mount ────────────────────────────────────────────────────────────────

    def on_mount(self) -> None:
        self._apply_theme()
        # Prime psutil's CPU % counter (first call always returns 0)
        self._collector.collect()
        self._update_stats()
        self.set_interval(1.0, self._update_stats)

    # ── stats refresh ────────────────────────────────────────────────────────

    def _update_stats(self) -> None:
        s = self._collector.collect()
        peak = self._collector.net_peak_bps

        self.query_one("#cpu", ArcGauge).set_value(
            s.cpu_pct / 100,
            f"{s.cpu_pct:.0f}%",
        )
        self.query_one("#ram", ArcGauge).set_value(
            s.ram_pct / 100,
            f"{s.ram_used_gb:.1f}/{s.ram_total_gb:.1f}G",
        )

        if s.cpu_temp is not None:
            # Scale to 0-1 over a 0-100 °C range
            self.query_one("#temp", ArcGauge).set_value(
                s.cpu_temp / 100.0,
                f"{s.cpu_temp:.0f}°C",
            )
        else:
            self.query_one("#temp", ArcGauge).set_value(0.0, "N/A")

        self.query_one("#disk", ArcGauge).set_value(
            s.disk_pct / 100,
            f"{s.disk_used_gb:.0f}/{s.disk_total_gb:.0f}G",
        )
        self.query_one("#net-up", ArcGauge).set_value(
            s.net_up_bps / peak,
            StatsCollector.fmt_bytes(s.net_up_bps),
        )
        self.query_one("#net-dn", ArcGauge).set_value(
            s.net_down_bps / peak,
            StatsCollector.fmt_bytes(s.net_down_bps),
        )

    # ── theme ─────────────────────────────────────────────────────────────────

    def action_reload_theme(self) -> None:
        """Re-read desktop theme files and reapply colours immediately."""
        self._theme = load_theme()
        colors = self._theme.gauge_colors()
        self.query_one("#logo", Static).update(_make_logo(self._theme))
        for gauge in self.query(ArcGauge):
            gauge._colors = colors
            gauge.refresh()
        self._apply_theme()

    def _apply_theme(self) -> None:
        t = self._theme
        self.screen.styles.background = t.bg
        self.query_one("#logo", Static).styles.background = t.bg
        for gauge in self.query(ArcGauge):
            gauge.styles.background = t.bg_panel
