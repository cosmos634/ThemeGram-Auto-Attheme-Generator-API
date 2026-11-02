from app.services.color_processor import contrast_ratio, process_colors, rgb_to_telegram_int


def test_argb_conversion_is_signed_decimal():
    assert rgb_to_telegram_int("#000000") == "-16777216"
    assert rgb_to_telegram_int("#FFFFFF") == "-1"


def test_contrast_ratio():
    assert contrast_ratio("#000000", "#FFFFFF") == 21.0


def test_text_color_has_good_contrast():
    result = process_colors({"primary": "#123456", "secondary": "#234567", "accent": "#FF0000", "background": "#FFFFFF"})
    assert contrast_ratio(result["text"], result["background"]) >= 4.5


def test_all_surface_text_pairs_are_readable():
    result = process_colors({
        "primary": "#777777",
        "secondary": "#888888",
        "accent": "#999999",
        "background": "#777777",
    })
    assert contrast_ratio(result["text"], result["background"]) >= 4.5
    assert contrast_ratio(result["text_on_primary"], result["primary"]) >= 4.5
    assert contrast_ratio(result["text_on_secondary"], result["secondary"]) >= 4.5
    assert contrast_ratio(result["text_on_accent"], result["accent"]) >= 4.5


def test_semantic_roles_cover_chat_surfaces_and_avatar_palette():
    result = process_colors({
        "primary": "#6A4C93",
        "secondary": "#1982C4",
        "accent": "#FF595E",
        "background": "#F4F2F8",
    })
    required = {
        "incoming_bg", "incoming_text", "outgoing_bg", "outgoing_text",
        "incoming_accent", "outgoing_accent", "surface", "surface_alt",
        "selected", "shadow", "divider", "avatar_red", "avatar_orange",
        "avatar_green", "avatar_cyan", "avatar_blue", "avatar_violet",
        "avatar_pink", "avatar_saved",
    }
    assert required.issubset(result)
    assert contrast_ratio(result["incoming_text"], result["incoming_bg"]) >= 4.5
    assert contrast_ratio(result["outgoing_text"], result["outgoing_bg"]) >= 4.5


def test_argb_conversion_preserves_transparency():
    assert rgb_to_telegram_int("#33000000") == "855638016"
