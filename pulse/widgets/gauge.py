"""Arc gauge widget — renders a semicircular speedometer-style dial."""

import math
from rich.text import Text
from rich.style import Style
from textual.widget import Widget


# ── colour helper ─────────────────────────────────────────────────────────────

def gauge_color(
    value: float,
    accent: str,
    warn_color: str,
    danger: str,
    warn_at: float = 0.70,
    crit_at: float = 0.90,
) -> str:
    if value >= crit_at:
        return danger
    if value >= warn_at:
        return warn_color
    return accent


# ── arc renderer ──────────────────────────────────────────────────────────────

def render_arc(
    value: float,
    width: int,
    height: int,
    label: str,
    display_str: str,
    accent: str,
    warn_color: str,
    danger: str,
    muted: str,
    fg: str,
    warn_at: float = 0.70,
    crit_at: float = 0.90,
) -> Text:
    """Return a Rich Text object containing the arc gauge art.

    The gauge is a semicircle (left=0%, top=50%, right=100%) with:
    - filled dots (●) up to the current value in the active colour
    - dim dots (·) for the remainder
    - a bright diamond (◆) marking the exact value position
    - a line of dots from centre to the value (needle)
    - value text centred inside the arc
    - label on the bottom row
    """
    value = max(0.0, min(1.0, value))
    active = gauge_color(value, accent, warn_color, danger, warn_at, crit_at)

    # 2-D character grid
    chars = [[" "] * width for _ in range(height)]
    colors: list[list[str | None]] = [[None] * width for _ in range(height)]

    def put(x: int, y: int, ch: str, col: str) -> None:
        if 0 <= x < width and 0 <= y < height:
            chars[y][x] = ch
            colors[y][x] = col

    # Geometry ----------------------------------------------------------------
    cx = (width - 1) / 2.0
    cy = float(height - 3)       # centre pivot; leaves 2 rows: value + label
    rx = (width / 2.0) - 1.5    # horizontal radius in char units
    ry = rx / 2.1                # vertical radius (compensates ~2:1 cell ratio)

    # Arc ---------------------------------------------------------------------
    # Sample densely; deduplicate by (xi, yi) so each cell is assigned once.
    n = max(500, width * 16)
    seen: set[tuple[int, int]] = set()
    arc_cells: list[tuple[int, int, float]] = []  # (xi, yi, t)  t: 0=left, 1=right

    for i in range(n + 1):
        t = i / n
        theta = math.pi * (1.0 - t)   # π → 0  (left → right)
        xi = int(round(cx + rx * math.cos(theta)))
        yi = int(round(cy - ry * math.sin(theta)))
        key = (xi, yi)
        if key not in seen and 0 <= xi < width and 0 <= yi < height:
            seen.add(key)
            arc_cells.append((xi, yi, t))

    for xi, yi, t in arc_cells:
        ch = "●" if t <= value else "·"
        col = active if t <= value else muted
        put(xi, yi, ch, col)

    # Value marker (bright ◆ at exact value position on the arc) -------------
    vtheta = math.pi * (1.0 - value)
    vx = int(round(cx + rx * math.cos(vtheta)))
    vy = int(round(cy - ry * math.sin(vtheta)))
    put(vx, vy, "◆", active)

    # Needle (dots from centre out toward the value position) -----------------
    steps = max(3, int(min(rx, ry) * 0.80))
    for step in range(1, steps):
        frac = step / steps
        nx = int(round(cx + rx * frac * math.cos(vtheta)))
        ny = int(round(cy - ry * frac * math.sin(vtheta)))
        if (nx, ny) not in seen:          # don't overwrite arc cells
            put(nx, ny, "·", active)

    # Centre pivot ------------------------------------------------------------
    put(int(round(cx)), int(round(cy)), "●", active)

    # Value text (row just above centre) --------------------------------------
    val_y = int(round(cy)) - 1
    if val_y >= 0 and display_str:
        val_x = int(round(cx - len(display_str) / 2.0))
        for j, ch in enumerate(display_str):
            put(val_x + j, val_y, ch, active)

    # Label (bottom row) -------------------------------------------------------
    lb_y = height - 1
    lb_x = int(round(cx - len(label) / 2.0))
    for j, ch in enumerate(label):
        put(lb_x + j, lb_y, ch, fg)

    # Assemble Rich Text -------------------------------------------------------
    out = Text(no_wrap=True)
    for y in range(height):
        for x in range(width):
            ch = chars[y][x]
            col = colors[y][x]
            out.append(ch, style=Style(color=col) if col else Style())
        if y < height - 1:
            out.append("\n")

    return out


# ── Textual widget ────────────────────────────────────────────────────────────

class ArcGauge(Widget):
    DEFAULT_CSS = """
    ArcGauge {
        padding: 0;
    }
    """

    def __init__(
        self,
        label: str,
        warn_at: float = 0.70,
        crit_at: float = 0.90,
        colors: dict | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.label = label
        self.warn_at = warn_at
        self.crit_at = crit_at
        self._colors: dict = colors or {}
        self._value: float = 0.0
        self._display: str = ""

    def set_value(self, value: float, display: str = "") -> None:
        self._value = max(0.0, min(1.0, value))
        self._display = display
        self.refresh()

    def render(self) -> Text:
        w, h = self.size.width, self.size.height
        if w < 6 or h < 5:
            return Text(self.label)
        c = self._colors
        return render_arc(
            value=self._value,
            width=w,
            height=h,
            label=self.label,
            display_str=self._display,
            accent=c.get("accent", "#7ca870"),
            warn_color=c.get("warn_color", "#c89858"),
            danger=c.get("danger", "#c87868"),
            muted=c.get("muted", "#8a7060"),
            fg=c.get("fg", "#e8d8b0"),
            warn_at=self.warn_at,
            crit_at=self.crit_at,
        )
