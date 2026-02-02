from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from domain.services.weather_calculator import WeatherCalculator

JST = ZoneInfo("Asia/Tokyo")


def _make_hourly_entry(jst_hour: int, temp: float, pop: float) -> dict:
    """JST時刻を指定してhourlyエントリを作成"""
    dt_jst = datetime(2026, 2, 2, jst_hour, 0, 0, tzinfo=JST)
    dt_utc = dt_jst.astimezone(timezone.utc)
    return {"dt": int(dt_utc.timestamp()), "temp": temp, "pop": pop}


class TestWeatherCalculator:
    def setup_method(self):
        self.calculator = WeatherCalculator()

    def test_calculate_normal(self):
        hourly_data = [
            _make_hourly_entry(9, 18.0, 0.1),
            _make_hourly_entry(12, 25.5, 0.3),
            _make_hourly_entry(15, 22.0, 0.7),
            _make_hourly_entry(18, 19.0, 0.2),
        ]
        weather = self.calculator.calculate(hourly_data)
        assert weather.max_temp == 25.5
        assert weather.min_temp == 18.0
        assert weather.pop == 70

    def test_filters_out_before_9(self):
        hourly_data = [
            _make_hourly_entry(6, 5.0, 0.0),
            _make_hourly_entry(8, 8.0, 0.0),
            _make_hourly_entry(9, 15.0, 0.2),
            _make_hourly_entry(12, 20.0, 0.5),
        ]
        weather = self.calculator.calculate(hourly_data)
        assert weather.min_temp == 15.0
        assert weather.max_temp == 20.0

    def test_filters_out_23_and_after(self):
        hourly_data = [
            _make_hourly_entry(21, 12.0, 0.1),
            _make_hourly_entry(22, 10.0, 0.0),
            _make_hourly_entry(23, 8.0, 0.9),
            _make_hourly_entry(0, 6.0, 0.8),
        ]
        weather = self.calculator.calculate(hourly_data)
        assert weather.max_temp == 12.0
        assert weather.min_temp == 10.0
        assert weather.pop == 10

    def test_boundary_hour_9_included(self):
        hourly_data = [_make_hourly_entry(9, 20.0, 0.5)]
        weather = self.calculator.calculate(hourly_data)
        assert weather.max_temp == 20.0
        assert weather.pop == 50

    def test_boundary_hour_22_included(self):
        hourly_data = [_make_hourly_entry(22, 15.0, 0.3)]
        weather = self.calculator.calculate(hourly_data)
        assert weather.max_temp == 15.0
        assert weather.pop == 30

    def test_empty_data_raises(self):
        with pytest.raises(ValueError, match="天気データが存在しません"):
            self.calculator.calculate([])

    def test_no_data_in_range_raises(self):
        hourly_data = [
            _make_hourly_entry(0, 5.0, 0.0),
            _make_hourly_entry(3, 4.0, 0.0),
            _make_hourly_entry(23, 8.0, 0.0),
        ]
        with pytest.raises(ValueError, match="天気データが存在しません"):
            self.calculator.calculate(hourly_data)

    def test_pop_floor(self):
        hourly_data = [_make_hourly_entry(12, 20.0, 0.456)]
        weather = self.calculator.calculate(hourly_data)
        assert weather.pop == 45

    def test_temp_rounding(self):
        hourly_data = [
            _make_hourly_entry(10, 18.456, 0.0),
            _make_hourly_entry(14, 25.351, 0.0),
        ]
        weather = self.calculator.calculate(hourly_data)
        assert weather.max_temp == 25.4
        assert weather.min_temp == 18.5
