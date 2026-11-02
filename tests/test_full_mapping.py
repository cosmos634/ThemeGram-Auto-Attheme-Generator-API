import json

from app.config import settings
from app.services.attheme_generator import generate_attheme
from app.services.color_processor import contrast_ratio, process_colors


def test_all_399_template_keys_are_generated():
    mapping = json.loads(settings.mapping_path.read_text(encoding="utf-8"))
    assert len(mapping) == 399

    colors = process_colors({
        "primary": "#6A4C93",
        "secondary": "#1982C4",
        "accent": "#FF595E",
        "background": "#F4F2F8",
    })
    output = generate_attheme(settings.template_path, settings.mapping_path, colors)
    entries = [
        line for line in output.decode("utf-8").splitlines()
        if line and not line.startswith("#") and "=" in line
    ]

    assert len(entries) == 399
    assert {line.split("=", 1)[0] for line in entries} == set(mapping)
    assert all(line.split("=", 1)[1] != "-1" for line in entries)


def test_three_dot_popup_menu_text_contrasts_with_its_background():
    mapping = json.loads(settings.mapping_path.read_text(encoding="utf-8"))
    colors = process_colors({
        "primary": "#6A4C93",
        "secondary": "#1982C4",
        "accent": "#FF595E",
        "background": "#F4F2F8",
    })
    assert mapping["actionBarDefaultSubmenuBackground"] == "primary"
    assert mapping["actionBarDefaultSubmenuItem"] == "on_primary"
    assert contrast_ratio(colors["on_primary"], colors["primary"]) >= 4.5
