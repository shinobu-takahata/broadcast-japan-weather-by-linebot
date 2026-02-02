import pytest

from domain.value_objects.weather import Weather


class TestWeather:
    def test_create_valid_weather(self):
        weather = Weather(max_temp=25.3, min_temp=18.1, pop=60)
        assert weather.max_temp == 25.3
        assert weather.min_temp == 18.1
        assert weather.pop == 60

    def test_frozen(self):
        weather = Weather(max_temp=25.3, min_temp=18.1, pop=60)
        with pytest.raises(AttributeError):
            weather.max_temp = 30.0  # type: ignore[misc]

    def test_pop_below_zero(self):
        with pytest.raises(ValueError, match="降水確率"):
            Weather(max_temp=25.0, min_temp=18.0, pop=-1)

    def test_pop_above_100(self):
        with pytest.raises(ValueError, match="降水確率"):
            Weather(max_temp=25.0, min_temp=18.0, pop=101)

    def test_max_temp_less_than_min_temp(self):
        with pytest.raises(ValueError, match="最高気温"):
            Weather(max_temp=10.0, min_temp=20.0, pop=50)

    def test_same_max_min_temp(self):
        weather = Weather(max_temp=20.0, min_temp=20.0, pop=0)
        assert weather.max_temp == weather.min_temp

    def test_pop_boundary_zero(self):
        weather = Weather(max_temp=25.0, min_temp=18.0, pop=0)
        assert weather.pop == 0

    def test_pop_boundary_100(self):
        weather = Weather(max_temp=25.0, min_temp=18.0, pop=100)
        assert weather.pop == 100
