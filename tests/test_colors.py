from app.services.color_processor import contrast_ratio, process_colors, rgb_to_telegram_int


def test_argb_conversion_is_signed_decimal():
    assert rgb_to_telegram_int("#000000") == "-16777216"
    assert rgb_to_telegram_int("#FFFFFF") == "-1"


def test_contrast_ratio():
    assert contrast_ratio("#000000", "#FFFFFF") == 21.0


def test_text_color_has_good_contrast():
    result = process_colors({"primary": "#123456", "secondary": "#234567", "accent": "#FF0000", "background": "#FFFFFF"})
    assert contrast_ratio(result["text"], result["background"]) >= 4.5
