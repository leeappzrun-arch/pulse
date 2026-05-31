"""Tests for the stats collector."""

import time
import pytest
from unittest.mock import patch, MagicMock

from pulse.utils.stats import StatsCollector, SystemStats


class TestFormatBytes:
    def test_bytes(self):
        assert StatsCollector.fmt_bytes(500) == "500 B/s"

    def test_kilobytes(self):
        assert StatsCollector.fmt_bytes(1_500) == "1.5 KB/s"

    def test_megabytes(self):
        assert StatsCollector.fmt_bytes(2_500_000) == "2.5 MB/s"

    def test_gigabytes(self):
        assert StatsCollector.fmt_bytes(1_200_000_000) == "1.2 GB/s"

    def test_zero(self):
        assert StatsCollector.fmt_bytes(0) == "0 B/s"


class TestStatsCollector:
    def test_collect_returns_dataclass(self):
        collector = StatsCollector()
        stats = collector.collect()
        assert isinstance(stats, SystemStats)

    def test_cpu_pct_range(self):
        stats = StatsCollector().collect()
        assert 0.0 <= stats.cpu_pct <= 100.0

    def test_ram_pct_range(self):
        stats = StatsCollector().collect()
        assert 0.0 <= stats.ram_pct <= 100.0

    def test_ram_used_leq_total(self):
        stats = StatsCollector().collect()
        assert stats.ram_used_gb <= stats.ram_total_gb

    def test_disk_pct_range(self):
        stats = StatsCollector().collect()
        assert 0.0 <= stats.disk_pct <= 100.0

    def test_disk_used_leq_total(self):
        stats = StatsCollector().collect()
        assert stats.disk_used_gb <= stats.disk_total_gb

    def test_net_bps_non_negative(self):
        collector = StatsCollector()
        collector.collect()  # prime
        stats = collector.collect()
        assert stats.net_up_bps >= 0.0
        assert stats.net_down_bps >= 0.0

    def test_net_peak_updates(self):
        collector = StatsCollector()
        collector.collect()
        # Inject a large transfer so peak rises
        import psutil
        original = psutil.net_io_counters

        call_count = 0
        base = original()

        def fake_net():
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                # Simulate 100 MB sent in the interval
                return MagicMock(
                    bytes_sent=base.bytes_sent + 100_000_000,
                    bytes_recv=base.bytes_recv,
                )
            return base

        with patch("pulse.utils.stats.psutil.net_io_counters", side_effect=fake_net):
            collector.collect()

        assert collector.net_peak_bps >= 1_000_000.0  # at least default minimum

    def test_cpu_temp_is_float_or_none(self):
        stats = StatsCollector().collect()
        assert stats.cpu_temp is None or isinstance(stats.cpu_temp, float)
