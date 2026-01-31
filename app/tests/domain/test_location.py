import pytest

from domain.value_objects.location import Location


class TestLocation:
    def test_create_valid_location(self):
        location = Location(city_name="渋谷区", latitude=35.6619, longitude=139.7041)
        assert location.city_name == "渋谷区"
        assert location.latitude == 35.6619
        assert location.longitude == 139.7041

    def test_frozen(self):
        location = Location(city_name="渋谷区", latitude=35.6619, longitude=139.7041)
        with pytest.raises(AttributeError):
            location.city_name = "新宿区"

    def test_empty_city_name_raises(self):
        with pytest.raises(ValueError, match="市区町村名は必須です"):
            Location(city_name="", latitude=35.6619, longitude=139.7041)

    def test_latitude_too_low_raises(self):
        with pytest.raises(ValueError, match="緯度は-90〜90"):
            Location(city_name="渋谷区", latitude=-91, longitude=139.7041)

    def test_latitude_too_high_raises(self):
        with pytest.raises(ValueError, match="緯度は-90〜90"):
            Location(city_name="渋谷区", latitude=91, longitude=139.7041)

    def test_longitude_too_low_raises(self):
        with pytest.raises(ValueError, match="経度は-180〜180"):
            Location(city_name="渋谷区", latitude=35.6619, longitude=-181)

    def test_longitude_too_high_raises(self):
        with pytest.raises(ValueError, match="経度は-180〜180"):
            Location(city_name="渋谷区", latitude=35.6619, longitude=181)

    def test_boundary_values(self):
        location = Location(city_name="テスト", latitude=-90, longitude=-180)
        assert location.latitude == -90
        assert location.longitude == -180

        location = Location(city_name="テスト", latitude=90, longitude=180)
        assert location.latitude == 90
        assert location.longitude == 180
