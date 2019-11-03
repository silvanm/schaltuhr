from unittest.mock import patch

from schaltuhr import is_it_dark


@patch('schaltuhr.get_weather_page_content', )
def test_is_it_dark(get_content):
    get_content.return_value = ', Helvetica; color:#E1002D; font-size:15px; font-weight:bold;">0&nbsp;W/m²</span></td>'
    assert is_it_dark() is True

    get_content.return_value = ', Helvetica; color:#E1002D; font-size:15px; font-weight:bold;">3,4&nbsp;W/m²</span></td>'
    assert is_it_dark() is False
