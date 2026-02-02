from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from domain.services.weather_calculator import WeatherCalculator

JST = ZoneInfo("Asia/Tokyo")


def _make_hourly_entry(jst_hour: int, temp: float) -> dict:
    """JST時刻を指定してhourlyエントリを作成（気温のみ）"""
    dt_jst = datetime(2026, 2, 2, jst_hour, 0, 0, tzinfo=JST)
    dt_utc = dt_jst.astimezone(timezone.utc)
    return {"dt": int(dt_utc.timestamp()), "temp": temp}


def _make_jma_pop(hour: int, pop: int) -> dict:
    """JMA形式のpopエントリを作成"""
    return {"time": datetime(2026, 2, 2, hour, 0, 0, tzinfo=JST), "pop": pop}


class TestWeatherCalculator:
    def setup_method(self):
        self.calculator = WeatherCalculator()

    def test_calculate_normal(self):
        hourly_data = [
            _make_hourly_entry(9, 18.0),
            _make_hourly_entry(12, 25.5),
            _make_hourly_entry(15, 22.0),
            _make_hourly_entry(18, 19.0),
        ]
        jma_pops = [
            _make_jma_pop(6, 10),
            _make_jma_pop(12, 30),
            _make_jma_pop(18, 70),
        ]
        weather = self.calculator.calculate(hourly_data, jma_pops)
        assert weather.max_temp == 25.5
        assert weather.min_temp == 18.0
        assert weather.pop == 70

    def test_filters_out_before_9(self):
        hourly_data = [
            _make_hourly_entry(6, 5.0),
            _make_hourly_entry(8, 8.0),
            _make_hourly_entry(9, 15.0),
            _make_hourly_entry(12, 20.0),
        ]
        jma_pops = [_make_jma_pop(6, 20), _make_jma_pop(12, 30), _make_jma_pop(18, 10)]
        weather = self.calculator.calculate(hourly_data, jma_pops)
        assert weather.min_temp == 15.0
        assert weather.max_temp == 20.0

    def test_filters_out_23_and_after(self):
        hourly_data = [
            _make_hourly_entry(21, 12.0),
            _make_hourly_entry(22, 10.0),
            _make_hourly_entry(23, 8.0),
            _make_hourly_entry(0, 6.0),
        ]
        jma_pops = [_make_jma_pop(6, 10), _make_jma_pop(12, 5), _make_jma_pop(18, 15)]
        weather = self.calculator.calculate(hourly_data, jma_pops)
        assert weather.max_temp == 12.0
        assert weather.min_temp == 10.0
        assert weather.pop == 15

    def test_boundary_hour_9_included(self):
        hourly_data = [_make_hourly_entry(9, 20.0)]
        jma_pops = [_make_jma_pop(6, 50), _make_jma_pop(12, 30), _make_jma_pop(18, 20)]
        weather = self.calculator.calculate(hourly_data, jma_pops)
        assert weather.max_temp == 20.0
        assert weather.pop == 50

    def test_boundary_hour_22_included(self):
        hourly_data = [_make_hourly_entry(22, 15.0)]
        jma_pops = [_make_jma_pop(6, 10), _make_jma_pop(12, 30), _make_jma_pop(18, 40)]
        weather = self.calculator.calculate(hourly_data, jma_pops)
        assert weather.max_temp == 15.0
        assert weather.pop == 40

    def test_empty_temp_data_raises(self):
        jma_pops = [_make_jma_pop(6, 10), _make_jma_pop(12, 30), _make_jma_pop(18, 20)]
        with pytest.raises(ValueError, match="気温データが存在しません"):
            self.calculator.calculate([], jma_pops)

    def test_no_temp_in_range_raises(self):
        hourly_data = [
            _make_hourly_entry(0, 5.0),
            _make_hourly_entry(3, 4.0),
            _make_hourly_entry(23, 8.0),
        ]
        jma_pops = [_make_jma_pop(6, 10), _make_jma_pop(12, 30), _make_jma_pop(18, 20)]
        with pytest.raises(ValueError, match="気温データが存在しません"):
            self.calculator.calculate(hourly_data, jma_pops)

    def test_no_relevant_pops_raises(self):
        hourly_data = [_make_hourly_entry(12, 20.0)]
        # 0:00 のブロックは 9:00〜23:00 に該当しない
        jma_pops = [_make_jma_pop(0, 50)]
        with pytest.raises(ValueError, match="降水確率データが存在しません"):
            self.calculator.calculate(hourly_data, jma_pops)

    def test_temp_rounding(self):
        hourly_data = [
            _make_hourly_entry(10, 18.456),
            _make_hourly_entry(14, 25.351),
        ]
        jma_pops = [_make_jma_pop(6, 10), _make_jma_pop(12, 20), _make_jma_pop(18, 5)]
        weather = self.calculator.calculate(hourly_data, jma_pops)
        assert weather.max_temp == 25.4
        assert weather.min_temp == 18.5

    def test_pop_is_max_of_relevant_blocks(self):
        hourly_data = [_make_hourly_entry(12, 20.0)]
        jma_pops = [
            _make_jma_pop(6, 10),
            _make_jma_pop(12, 80),
            _make_jma_pop(18, 30),
        ]
        weather = self.calculator.calculate(hourly_data, jma_pops)
        assert weather.pop == 80
