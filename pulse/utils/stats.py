"""System stats collection via psutil."""

import time
import psutil
from dataclasses import dataclass
from typing import Optional


@dataclass
class SystemStats:
    cpu_pct: float
    ram_pct: float
    ram_used_gb: float
    ram_total_gb: float
    cpu_temp: Optional[float]   # °C, None if sensor unavailable
    disk_pct: float
    disk_used_gb: float
    disk_total_gb: float
    net_up_bps: float
    net_down_bps: float


# Ordered list of sensor names to try for CPU temperature
_TEMP_SENSORS = ("coretemp", "k10temp", "zenpower", "cpu_thermal", "acpitz")


class StatsCollector:
    def __init__(self, disk_path: str = "/"):
        self._disk_path = disk_path
        self._last_net = psutil.net_io_counters()
        self._last_time = time.monotonic()
        self._net_up_bps = 0.0
        self._net_down_bps = 0.0
        # Rolling peak used to scale the network gauges (minimum 1 MB/s)
        self._net_peak_bps = 1_000_000.0

    # ── public ───────────────────────────────────────────────────────────────

    def collect(self) -> SystemStats:
        cpu_pct = psutil.cpu_percent(interval=None)

        mem = psutil.virtual_memory()
        ram_pct = mem.percent
        ram_used_gb = mem.used / 1e9
        ram_total_gb = mem.total / 1e9

        cpu_temp = self._read_cpu_temp()

        disk = self._read_disk()

        self._update_net()

        return SystemStats(
            cpu_pct=cpu_pct,
            ram_pct=ram_pct,
            ram_used_gb=ram_used_gb,
            ram_total_gb=ram_total_gb,
            cpu_temp=cpu_temp,
            disk_pct=disk[0],
            disk_used_gb=disk[1],
            disk_total_gb=disk[2],
            net_up_bps=self._net_up_bps,
            net_down_bps=self._net_down_bps,
        )

    @property
    def net_peak_bps(self) -> float:
        return self._net_peak_bps

    @staticmethod
    def fmt_bytes(bps: float) -> str:
        if bps >= 1e9:
            return f"{bps / 1e9:.1f} GB/s"
        if bps >= 1e6:
            return f"{bps / 1e6:.1f} MB/s"
        if bps >= 1e3:
            return f"{bps / 1e3:.1f} KB/s"
        return f"{bps:.0f} B/s"

    # ── internals ────────────────────────────────────────────────────────────

    def _read_cpu_temp(self) -> Optional[float]:
        try:
            all_temps = psutil.sensors_temperatures()
        except (AttributeError, Exception):
            return None

        for name in _TEMP_SENSORS:
            readings = all_temps.get(name, [])
            if readings:
                return max(r.current for r in readings)

        # Fall back to first available sensor
        for readings in all_temps.values():
            if readings:
                return max(r.current for r in readings)

        return None

    def _read_disk(self) -> tuple[float, float, float]:
        try:
            d = psutil.disk_usage(self._disk_path)
            return d.percent, d.used / 1e9, d.total / 1e9
        except Exception:
            return 0.0, 0.0, 0.0

    def _update_net(self) -> None:
        now = time.monotonic()
        net = psutil.net_io_counters()
        dt = now - self._last_time
        if dt > 0:
            self._net_up_bps = (net.bytes_sent - self._last_net.bytes_sent) / dt
            self._net_down_bps = (net.bytes_recv - self._last_net.bytes_recv) / dt
        self._last_net = net
        self._last_time = now

        peak = max(self._net_up_bps, self._net_down_bps)
        if peak > self._net_peak_bps:
            self._net_peak_bps = peak
