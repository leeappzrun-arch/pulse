# Pulse

A terminal system-monitor dashboard with speedometer-style arc gauges.

```
██████╗ ██╗   ██╗██╗     ███████╗███████╗
██╔══██╗██║   ██║██║     ██╔════╝██╔════╝
██████╔╝██║   ██║██║     ███████╗█████╗
██╔═══╝ ██║   ██║██║     ╚════██║██╔══╝
██║     ╚██████╔╝███████╗███████║███████╗
╚═╝      ╚═════╝ ╚══════╝╚══════╝╚══════╝
              system monitor
```

Reads your current KDE / GTK desktop theme at startup and applies its colours
to the logo, gauges, and background. Press `r` at any time to reload the theme.

## Gauges

| Gauge | Arc fills to… | Centre text |
|---|---|---|
| CPU USAGE | CPU% | `45%` |
| RAM USAGE | RAM% | `7.2/16.0G` |
| CPU TEMP | temp/100°C | `67°C` (N/A if no sensor) |
| DISK USAGE | used% | `18/50G` |
| NET UPLOAD | rate vs rolling peak | `1.2 MB/s` |
| NET DOWNLOAD | rate vs rolling peak | `3.4 MB/s` |

Gauge colours: green → amber (70%) → red (90%).

## Run

```sh
./run.sh
```

The first run creates `.venv/` and installs dependencies automatically.

## Key bindings

| Key | Action |
|---|---|
| `q` | Quit |
| `r` | Reload desktop theme |

## Tests

```sh
./test.sh
```

Or, once the venv exists:

```sh
.venv/bin/pytest -q
```
