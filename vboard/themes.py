"""Theme palette resolution and GTK3 CSS generation for Vboard."""

from .constants import (
    DEFAULT_ACCENT_COLOR,
    DEFAULT_CUSTOM_KEY_BG,
    DEFAULT_CUSTOM_KEY_BORDER_COLOR,
    DEFAULT_CUSTOM_MODIFIER_BG,
    DEFAULT_CUSTOM_TEXT_COLOR,
    DEFAULT_CUSTOM_WINDOW_BG,
    DEFAULT_FONT_WEIGHT,
    DEFAULT_KEY_BORDER_WIDTH,
    DEFAULT_KEY_SHADOW_ENABLED,
    DEFAULT_WINDOW_BORDER_COLOR,
    DEFAULT_WINDOW_BORDER_WIDTH,
)


def parse_hex_rgb(hex_color, fallback=(10, 132, 255)):
    if not isinstance(hex_color, str):
        return fallback
    cleaned = hex_color.strip().lstrip("#")
    if len(cleaned) == 3:
        cleaned = "".join(ch * 2 for ch in cleaned)
    if len(cleaned) != 6:
        return fallback
    try:
        return (
            int(cleaned[0:2], 16),
            int(cleaned[2:4], 16),
            int(cleaned[4:6], 16),
        )
    except ValueError:
        return fallback


def rgb_to_hex(rgb_values):
    r, g, b = (max(0, min(255, int(round(c)))) for c in rgb_values)
    return f"#{r:02X}{g:02X}{b:02X}"


def parse_rgb_value(value, fallback=(0, 0, 0)):
    if isinstance(value, str) and value.strip().startswith("#"):
        return parse_hex_rgb(value, fallback=fallback)
    try:
        parts = [int(component.strip()) for component in value.split(",")]
        if len(parts) == 3:
            return tuple(max(0, min(255, component)) for component in parts)
    except (AttributeError, ValueError):
        pass
    return fallback


def adjust_rgb(rgb_values, amount):
    return tuple(max(0, min(255, int(component) + amount)) for component in rgb_values)


def rgb_css(rgb_values):
    return f"{rgb_values[0]}, {rgb_values[1]}, {rgb_values[2]}"


def luminance(rgb_values):
    red, green, blue = rgb_values
    return 0.299 * red + 0.587 * green + 0.114 * blue


def contrast_text_rgb(rgb_values):
    return (28, 28, 28) if luminance(rgb_values) >= 128 else (245, 245, 247)


def accent_color_for_rgb(rgb_values):
    red, green, blue = rgb_values
    maximum = max(rgb_values)
    minimum = min(rgb_values)
    if maximum == 0 or (maximum - minimum) / maximum < 0.25:
        return "#1D1D1F" if luminance(rgb_values) >= 128 else "#FFFFFF"

    color_range = maximum - minimum
    if maximum == red:
        hue = ((green - blue) / color_range) % 6
    elif maximum == green:
        hue = (blue - red) / color_range + 2
    else:
        hue = (red - green) / color_range + 4
    hue /= 6.0

    sector = int(hue * 6)
    fraction = hue * 6 - sector
    palette = (
        (1, fraction, 0),
        (1 - fraction, 1, 0),
        (0, 1, fraction),
        (0, 1 - fraction, 1),
        (fraction, 0, 1),
        (1, 0, 1 - fraction),
    )
    accent_rgb = palette[sector % 6]
    return "#{:02X}{:02X}{:02X}".format(
        int(accent_rgb[0] * 255),
        int(accent_rgb[1] * 255),
        int(accent_rgb[2] * 255),
    )


def normalize_style_variant(style_variant):
    legacy_map = {
        "apple_dark": "graphite_dark",
        "apple_light": "frost_light",
    }
    normalized = legacy_map.get(style_variant, style_variant)
    if normalized in (
        "graphite_dark",
        "frost_light",
        "onboard",
        "high_contrast_tv",
        "enhanced",
        "classic",
    ):
        return normalized
    return "graphite_dark"


def get_base_theme_colors(style_variant, bg_color="0,0,0", text_color="white"):
    """Return editable hex defaults matching a built-in theme base."""
    variant = normalize_style_variant(style_variant)
    if variant == "graphite_dark":
        return {
            "window_bg": "#1E1E22",
            "key_bg": "#48484E",
            "modifier_bg": "#323238",
            "text_color": "#F5F5F7",
            "key_border_color": "#64646E",
            "window_border_color": "#FFFFFF",
        }
    if variant == "frost_light":
        return {
            "window_bg": "#E4E7EE",
            "key_bg": "#FFFFFF",
            "modifier_bg": "#CED3DC",
            "text_color": "#1D1D1F",
            "key_border_color": "#C2C7D0",
            "window_border_color": "#8E94A0",
        }
    if variant == "onboard":
        return {
            "window_bg": "#141A24",
            "key_bg": "#364156",
            "modifier_bg": "#252F42",
            "text_color": "#F2F5FA",
            "key_border_color": "#162032",
            "window_border_color": "#FFFFFF",
        }
    if variant == "high_contrast_tv":
        return {
            "window_bg": "#222222",
            "key_bg": "#2E2E2E",
            "modifier_bg": "#20252D",
            "text_color": "#FFFFFF",
            "key_border_color": "#969696",
            "window_border_color": "#FFFFFF",
        }
    base_rgb = parse_rgb_value(bg_color, fallback=(24, 24, 28))
    is_light = luminance(base_rgb) >= 135
    key_rgb = adjust_rgb(base_rgb, -18 if is_light else 28)
    mod_rgb = adjust_rgb(base_rgb, -28 if is_light else 14)
    border_rgb = adjust_rgb(base_rgb, -46 if is_light else 56)
    fg_rgb = contrast_text_rgb(base_rgb)
    return {
        "window_bg": rgb_to_hex(base_rgb),
        "key_bg": rgb_to_hex(key_rgb),
        "modifier_bg": rgb_to_hex(mod_rgb),
        "text_color": rgb_to_hex(fg_rgb),
        "key_border_color": rgb_to_hex(border_rgb),
        "window_border_color": "#7E8490" if is_light else "#FFFFFF",
    }


def resolve_theme_palette(
    *,
    style_variant,
    bg_color="0,0,0",
    text_color="white",
    accent_hex=DEFAULT_ACCENT_COLOR,
    use_custom_colors=False,
    custom_window_bg=DEFAULT_CUSTOM_WINDOW_BG,
    custom_key_bg=DEFAULT_CUSTOM_KEY_BG,
    custom_modifier_bg=DEFAULT_CUSTOM_MODIFIER_BG,
    custom_text_color=DEFAULT_CUSTOM_TEXT_COLOR,
    custom_key_border_color=DEFAULT_CUSTOM_KEY_BORDER_COLOR,
    window_border_color=DEFAULT_WINDOW_BORDER_COLOR,
):
    """Resolve full color palette (including foreground/icon hex) for any theme or custom colors."""
    variant = normalize_style_variant(style_variant)
    accent_rgb = parse_hex_rgb(accent_hex, fallback=(10, 132, 255))
    accent_text = "#1D1D1F" if luminance(accent_rgb) >= 185 else "#FFFFFF"

    base_colors = get_base_theme_colors(variant, bg_color, text_color)
    if use_custom_colors:
        win_rgb = parse_hex_rgb(custom_window_bg, fallback=parse_hex_rgb(base_colors["window_bg"]))
        key_rgb = parse_hex_rgb(custom_key_bg, fallback=parse_hex_rgb(base_colors["key_bg"]))
        mod_rgb = parse_hex_rgb(custom_modifier_bg, fallback=parse_hex_rgb(base_colors["modifier_bg"]))
        fg_rgb = parse_hex_rgb(custom_text_color, fallback=parse_hex_rgb(base_colors["text_color"]))
        key_border_rgb = parse_hex_rgb(
            custom_key_border_color, fallback=parse_hex_rgb(base_colors["key_border_color"])
        )
        win_border_rgb = parse_hex_rgb(
            window_border_color, fallback=parse_hex_rgb(base_colors["window_border_color"])
        )
    else:
        win_rgb = parse_hex_rgb(base_colors["window_bg"])
        key_rgb = parse_hex_rgb(base_colors["key_bg"])
        mod_rgb = parse_hex_rgb(base_colors["modifier_bg"])
        fg_rgb = parse_hex_rgb(base_colors["text_color"])
        key_border_rgb = parse_hex_rgb(base_colors["key_border_color"])
        win_border_rgb = parse_hex_rgb(
            window_border_color or base_colors["window_border_color"],
            fallback=parse_hex_rgb(base_colors["window_border_color"]),
        )

    is_light = luminance(win_rgb) >= 135
    fg_hex = rgb_to_hex(fg_rgb)
    win_top = adjust_rgb(win_rgb, 6 if not is_light else 8)
    win_bot = adjust_rgb(win_rgb, -6 if not is_light else -6)
    hdr_bg = adjust_rgb(win_rgb, 4 if not is_light else -4)
    hdr_border = adjust_rgb(win_rgb, -24 if is_light else 26)
    key_hover = adjust_rgb(key_rgb, -14 if is_light else 18)
    mod_hover = adjust_rgb(mod_rgb, -14 if is_light else 18)
    hdr_btn_bg = adjust_rgb(mod_rgb, 14 if is_light else 6)
    hdr_btn_hover = adjust_rgb(hdr_btn_bg, -14 if is_light else 18)
    sugg_bg = adjust_rgb(win_rgb, -6 if is_light else 14)
    sugg_active_bg = key_rgb
    hover_border_rgb = (255, 214, 0) if variant == "high_contrast_tv" and not use_custom_colors else accent_rgb
    cmd_mod_rgb = (
        (210, 42, 42)
        if variant == "high_contrast_tv" and not use_custom_colors
        else accent_rgb
    )
    cmd_mod_text = "#1D1D1F" if luminance(cmd_mod_rgb) >= 185 else "#FFFFFF"
    orange_hint = "#FF9500" if is_light else "#FF9F0A"

    return {
        "variant": variant,
        "is_light": is_light,
        "win_rgb": win_rgb,
        "win_top": win_top,
        "win_bot": win_bot,
        "win_border_rgb": win_border_rgb,
        "hdr_bg": hdr_bg,
        "hdr_border": hdr_border,
        "hdr_btn_bg": hdr_btn_bg,
        "hdr_btn_hover": hdr_btn_hover,
        "key_rgb": key_rgb,
        "key_hover": key_hover,
        "key_border_rgb": key_border_rgb,
        "mod_rgb": mod_rgb,
        "mod_hover": mod_hover,
        "sugg_bg": sugg_bg,
        "sugg_active_bg": sugg_active_bg,
        "fg_rgb": fg_rgb,
        "fg_hex": fg_hex,
        "icon_color": fg_hex,
        "accent_rgb": accent_rgb,
        "accent_darker": adjust_rgb(accent_rgb, -24),
        "accent_lighter": adjust_rgb(accent_rgb, 34),
        "accent_text": accent_text,
        "hover_border_rgb": hover_border_rgb,
        "cmd_mod_rgb": cmd_mod_rgb,
        "cmd_mod_text": cmd_mod_text,
        "orange_hint": orange_hint,
    }


def build_theme_css(
    *,
    style_variant,
    bg_color,
    text_color,
    theme_opacity,
    desktop_env,
    accent_hex,
    key_font_size,
    secondary_key_font_size,
    header_font_size,
    suggestion_font_size,
    key_radius,
    key_spacing,
    font_weight=DEFAULT_FONT_WEIGHT,
    key_border_width=DEFAULT_KEY_BORDER_WIDTH,
    window_border_width=DEFAULT_WINDOW_BORDER_WIDTH,
    window_border_color=DEFAULT_WINDOW_BORDER_COLOR,
    key_shadow_enabled=DEFAULT_KEY_SHADOW_ENABLED,
    use_custom_colors=False,
    custom_window_bg=DEFAULT_CUSTOM_WINDOW_BG,
    custom_key_bg=DEFAULT_CUSTOM_KEY_BG,
    custom_modifier_bg=DEFAULT_CUSTOM_MODIFIER_BG,
    custom_text_color=DEFAULT_CUSTOM_TEXT_COLOR,
    custom_key_border_color=DEFAULT_CUSTOM_KEY_BORDER_COLOR,
):
    palette = resolve_theme_palette(
        style_variant=style_variant,
        bg_color=bg_color,
        text_color=text_color,
        accent_hex=accent_hex,
        use_custom_colors=use_custom_colors,
        custom_window_bg=custom_window_bg,
        custom_key_bg=custom_key_bg,
        custom_modifier_bg=custom_modifier_bg,
        custom_text_color=custom_text_color,
        custom_key_border_color=custom_key_border_color,
        window_border_color=window_border_color,
    )

    gnome_specific = "background-image: none;" if "GNOME" in desktop_env else ""
    key_radius = max(0, min(18, int(round(key_radius))))
    key_spacing = max(1, min(8, int(round(key_spacing))))
    btn_radius = max(4, min(14, key_radius))
    window_radius = max(6, min(20, key_radius + 4))
    window_border_w = max(0, min(4, int(round(window_border_width))))
    key_border_w = max(0, min(3, int(round(key_border_width))))
    inner_radius = max(0, window_radius - window_border_w)
    header_btn_min_w = max(24, int(round(header_font_size * 2.1)))
    header_btn_min_h = max(22, int(round(header_font_size * 2.0)))
    layout_btn_min_w = max(30, header_btn_min_w + 4)

    try:
        fw_int = int(str(font_weight))
        if fw_int not in (400, 500, 600, 700):
            fw_int = 500
    except ValueError:
        fw_int = 500

    def rgba(rgb_values, alpha_scale=1.0):
        red, green, blue = rgb_values
        alpha = max(0.0, min(1.0, theme_opacity * alpha_scale))
        return f"rgba({red}, {green}, {blue}, {alpha:.3f})"

    fg_hex = palette["fg_hex"]
    is_light = palette["is_light"]
    variant = palette["variant"]
    accent_rgb = palette["accent_rgb"]
    accent_darker = palette["accent_darker"]
    accent_lighter = palette["accent_lighter"]
    accent_text = palette["accent_text"]
    hover_border_rgb = palette["hover_border_rgb"]
    cmd_mod_rgb = palette["cmd_mod_rgb"]
    cmd_mod_text = palette["cmd_mod_text"]
    orange_hint = palette["orange_hint"]

    if key_shadow_enabled:
        key_shadow = (
            "0 1px 0 rgba(0, 0, 0, 0.22)"
            if is_light
            else "0 1px 0 rgba(0, 0, 0, 0.55), inset 0 1px rgba(255, 255, 255, 0.08)"
        )
    else:
        key_shadow = "none"

    use_gradient = variant in ("graphite_dark", "frost_light", "onboard") and not use_custom_colors
    if variant == "onboard" and not use_custom_colors:
        key_bg_image = (
            f"linear-gradient(to bottom, {rgba(adjust_rgb(palette['key_rgb'], 18), 1.0)}, "
            f"{rgba(adjust_rgb(palette['key_rgb'], -10), 1.0)})"
        )
        key_hover_image = (
            f"linear-gradient(to bottom, {rgba(adjust_rgb(palette['key_hover'], 16), 1.0)}, "
            f"{rgba(adjust_rgb(palette['key_hover'], -8), 1.0)})"
        )
        mod_bg_image = (
            f"linear-gradient(to bottom, {rgba(adjust_rgb(palette['mod_rgb'], 16), 1.0)}, "
            f"{rgba(adjust_rgb(palette['mod_rgb'], -8), 1.0)})"
        )
    else:
        key_bg_image = "none"
        key_hover_image = "none"
        mod_bg_image = "none"

    win_bg_image = (
        f"linear-gradient(to bottom, {rgba(palette['win_top'], 1.0)}, {rgba(palette['win_bot'], 1.0)})"
        if use_gradient
        else "none"
    )

    win_border_color_rgba = f"rgba({rgb_css(palette['win_border_rgb'])}, 0.92)"
    win_border_side = (
        f"{window_border_w}px solid {win_border_color_rgba}"
        if window_border_w > 0
        else "0px solid transparent"
    )
    key_border_css = (
        f"{key_border_w}px solid {rgba(palette['key_border_rgb'], 0.95)}"
        if key_border_w > 0
        else "1px solid transparent"
    )
    active_border_w = max(1, key_border_w)

    toolbar_bg = rgba(palette["sugg_bg"], 0.92)
    toolbar_border = rgba(palette["key_border_rgb"], 0.85)
    media_btn_bg = rgba(palette["mod_rgb"], 0.96)
    media_btn_hover = rgba(palette["mod_hover"], 1.0)
    media_btn_border = rgba(palette["key_border_rgb"], 0.88)

    return f"""
        window#vboard-main,
        window#vboard-main.background,
        window#vboard-main.csd,
        window#vboard-main.solid-csd {{
            background-color: {rgba(palette['win_bot'], 1.0)};
            background-image: {win_bg_image};
            border-top: 0px;
            border-left: {win_border_side};
            border-right: {win_border_side};
            border-bottom: {win_border_side};
            border-top-left-radius: 0px;
            border-top-right-radius: 0px;
            border-bottom-left-radius: {window_radius}px;
            border-bottom-right-radius: {window_radius}px;
            padding: 0px;
            margin: 0px;
            box-shadow: none;
            color: {fg_hex};
        }}

        window#vboard-main decoration,
        window#vboard-main.csd decoration,
        window#vboard-main.solid-csd decoration {{
            background-color: transparent;
            background-image: none;
            border: 0px;
            border-radius: {window_radius}px;
            padding: 0px;
            margin: 0px;
            box-shadow: none;
        }}

        window#vboard-main #vboard-content {{
            background-color: transparent;
            background-image: none;
            border: 0px;
            padding: 0px;
            margin: 0px;
            border-radius: 0px 0px {inner_radius}px {inner_radius}px;
        }}

        window#vboard-main label {{
            color: {fg_hex};
        }}

        window#vboard-main headerbar,
        window#vboard-main headerbar.titlebar,
        window#vboard-main.solid-csd headerbar,
        window#vboard-main.csd headerbar {{
            background-color: {rgba(palette['hdr_bg'], 0.98)};
            background-image: none;
            border-top: {win_border_side};
            border-left: {win_border_side};
            border-right: {win_border_side};
            border-bottom: 1px solid {rgba(palette['hdr_border'], 0.95)};
            border-top-left-radius: {window_radius}px;
            border-top-right-radius: {window_radius}px;
            border-bottom-left-radius: 0px;
            border-bottom-right-radius: 0px;
            box-shadow: none;
            margin: 0px;
            padding: 3px 6px;
            min-height: 0px;
            color: {fg_hex};
        }}

        window#vboard-main headerbar .title,
        window#vboard-main headerbar label {{
            color: {fg_hex};
            font-size: {header_font_size}px;
            font-weight: 600;
        }}

        window#vboard-main headerbar button,
        window#vboard-main #headbar-button {{
            min-width: {header_btn_min_w}px;
            min-height: {header_btn_min_h}px;
            padding: 0px 6px;
            border: {key_border_css};
            border-radius: {btn_radius}px;
            margin: 0px 1px;
            color: {fg_hex};
            background-color: {rgba(palette['hdr_btn_bg'], 1.0)};
            background-image: none;
            box-shadow: {key_shadow};
            transition: none;
            {gnome_specific}
        }}

        window#vboard-main headerbar button label,
        window#vboard-main #headbar-button label,
        window#vboard-main headerbar button image,
        window#vboard-main headerbar .titlebutton,
        window#vboard-main headerbar .titlebutton image {{
            color: {fg_hex};
            font-size: {header_font_size}px;
            font-weight: 600;
        }}

        window#vboard-main headerbar .titlebutton {{
            min-width: 26px;
            min-height: 24px;
            padding: 0px 4px;
        }}

        window#vboard-main headerbar button:hover,
        window#vboard-main #combobox button.combo:hover {{
            background-color: {rgba(palette['hdr_btn_hover'], 1.0)};
            border: {active_border_w}px solid {rgba(hover_border_rgb, 0.95)};
        }}

        window#vboard-main #esc-button,
        window#vboard-main #layout-button {{
            min-width: {layout_btn_min_w}px;
            min-height: {header_btn_min_h}px;
            padding: 0px 6px;
            border: {key_border_css};
            border-radius: {btn_radius}px;
            color: {fg_hex};
            background-color: {rgba(palette['hdr_btn_bg'], 1.0)};
            background-image: none;
            box-shadow: {key_shadow};
            transition: none;
        }}

        window#vboard-main #esc-button label,
        window#vboard-main #layout-button label {{
            color: {fg_hex};
            font-size: {header_font_size}px;
            font-weight: 700;
        }}

        window#vboard-main #esc-button:hover,
        window#vboard-main #layout-button:hover {{
            background-color: {rgba(palette['hdr_btn_hover'], 1.0)};
            border: {active_border_w}px solid {rgba(hover_border_rgb, 0.95)};
        }}

        window#vboard-main #layout-button.active-layout {{
            border: {active_border_w}px solid {rgba(accent_darker, 1.0)};
            background-color: {rgba(accent_rgb, 1.0)};
            background-image: none;
            color: {accent_text};
        }}

        window#vboard-main #layout-button.active-layout label {{
            color: {accent_text};
        }}

        window#vboard-main #combobox button.combo {{
            color: {fg_hex};
            padding: 2px 6px;
            min-height: {header_btn_min_h}px;
            border: {key_border_css};
            border-radius: {btn_radius}px;
            background-color: {rgba(palette['hdr_btn_bg'], 1.0)};
            background-image: none;
            box-shadow: {key_shadow};
            font-size: {header_font_size}px;
        }}

        window#vboard-main #combobox button.combo cellview,
        window#vboard-main #combobox button.combo label,
        window#vboard-main #combobox button.combo arrow {{
            color: {fg_hex};
            font-size: {header_font_size}px;
        }}

        window#vboard-main #grid {{
            padding: {max(2, key_spacing + 1)}px;
            background-color: transparent;
        }}

        window#vboard-main #grid button {{
            min-width: 0px;
            min-height: 0px;
            padding: 0px 2px;
            border: {key_border_css};
            border-radius: {key_radius}px;
            color: {fg_hex};
            background-color: {rgba(palette['key_rgb'], 1.0)};
            background-image: {key_bg_image};
            box-shadow: {key_shadow};
            margin: {key_spacing}px;
            transition: none;
            {gnome_specific}
        }}

        window#vboard-main #grid button label {{
            color: {fg_hex};
            font-size: {key_font_size}px;
            font-weight: {fw_int};
        }}

        window#vboard-main #grid button.compact-label label,
        window#vboard-main #grid button.modifier-key label,
        window#vboard-main #grid button.sidebar-key label {{
            color: {fg_hex};
            font-size: {secondary_key_font_size}px;
        }}

        window#vboard-main #grid button.modifier-key,
        window#vboard-main #grid button.sidebar-key {{
            background-color: {rgba(palette['mod_rgb'], 1.0)};
            background-image: {mod_bg_image};
        }}

        window#vboard-main #grid button.modifier-key:hover,
        window#vboard-main #grid button.sidebar-key:hover {{
            background-color: {rgba(palette['mod_hover'], 1.0)};
            background-image: {key_hover_image};
        }}

        window#vboard-main #grid button:hover {{
            border: {active_border_w}px solid {rgba(hover_border_rgb, 0.95)};
            background-color: {rgba(palette['key_hover'], 1.0)};
            background-image: {key_hover_image};
        }}

        window#vboard-main #grid button:active,
        window#vboard-main #grid button:active:hover {{
            border: {active_border_w}px solid {rgba(accent_darker, 1.0)};
            background-color: {rgba(accent_rgb, 1.0)};
            background-image: none;
            color: {accent_text};
            box-shadow: none;
        }}

        window#vboard-main #grid button:active label,
        window#vboard-main #grid button:active:hover label {{
            color: {accent_text};
        }}

        window#vboard-main #grid button.active-modifier,
        window#vboard-main #grid button.sidebar-key.active-layer {{
            border: {active_border_w}px solid {rgba(accent_darker, 1.0)};
            background-color: {rgba(accent_rgb, 1.0)};
            background-image: none;
            color: {accent_text};
        }}

        window#vboard-main #grid button.active-modifier label,
        window#vboard-main #grid button.sidebar-key.active-layer label {{
            color: {accent_text};
            font-weight: 700;
        }}

        window#vboard-main #grid button.active-command-modifier {{
            border: {active_border_w}px solid {rgba(accent_lighter, 1.0)};
            background-color: {rgba(cmd_mod_rgb, 1.0)};
            background-image: none;
            color: {cmd_mod_text};
        }}

        window#vboard-main #grid button.active-command-modifier label {{
            color: {cmd_mod_text};
            font-weight: 700;
        }}

        window#vboard-main #grid button.altgr-hint {{
            border: 2px solid {orange_hint};
        }}

        window#vboard-main #grid button.locked-modifier {{
            border: 2px solid {rgba(accent_lighter, 1.0)};
            box-shadow: inset 0 -3px {orange_hint};
        }}

        window#vboard-main #grid button.dwell-active {{
            border: 2px solid {rgba(accent_lighter, 1.0)};
        }}

        window#vboard-main #suggestion-bar {{
            background-color: transparent;
        }}

        window#vboard-main #suggestion-button {{
            border: 1px solid {rgba(palette['key_border_rgb'], 0.72)};
            border-radius: {btn_radius}px;
            background-color: {rgba(palette['sugg_bg'], 0.95)};
            background-image: none;
            box-shadow: none;
            min-width: 0px;
            min-height: 0px;
            padding: 3px 6px;
            transition: none;
        }}

        window#vboard-main #suggestion-button label,
        window#vboard-main #suggestion-button:disabled label {{
            color: {fg_hex};
            font-size: {suggestion_font_size}px;
            font-weight: {fw_int};
        }}

        window#vboard-main #suggestion-button.has-suggestion {{
            border: 1px solid {rgba(palette['key_border_rgb'], 1.0)};
            background-color: {rgba(palette['sugg_active_bg'], 1.0)};
            box-shadow: {key_shadow};
        }}

        window#vboard-main #suggestion-button.has-suggestion:hover {{
            border: 1px solid {rgba(hover_border_rgb, 1.0)};
            background-color: {rgba(accent_rgb, 0.22)};
        }}

        window#vboard-main #current-text-bar {{
            background-color: {toolbar_bg};
            border: 1px solid {toolbar_border};
            border-radius: {btn_radius}px;
            padding: 2px 8px;
        }}

        window#vboard-main #current-text-label {{
            color: {fg_hex};
            font-size: {suggestion_font_size}px;
            font-weight: 500;
        }}

        window#vboard-main #current-text-clear {{
            min-width: 24px;
            min-height: 20px;
            padding: 0px 4px;
            border: 1px solid {toolbar_border};
            border-radius: {max(4, btn_radius - 2)}px;
            background-color: transparent;
            background-image: none;
            color: {fg_hex};
        }}

        window#vboard-main #current-text-clear label {{
            color: {fg_hex};
            font-size: {max(9, header_font_size - 1)}px;
        }}

        window#vboard-main #media-bar {{
            background-color: transparent;
        }}

        window#vboard-main #media-bar button {{
            min-width: 24px;
            min-height: {max(22, header_btn_min_h - 2)}px;
            padding: 2px 4px;
            border: 1px solid {media_btn_border};
            border-radius: {max(4, btn_radius - 1)}px;
            color: {fg_hex};
            background-color: {media_btn_bg};
            background-image: none;
            box-shadow: none;
            transition: none;
        }}

        window#vboard-main #media-bar button label {{
            color: {fg_hex};
            font-size: {max(9, secondary_key_font_size)}px;
            font-weight: 600;
        }}

        window#vboard-main #media-bar button:hover {{
            border: 1px solid {rgba(hover_border_rgb, 1.0)};
            background-color: {media_btn_hover};
        }}

        window#vboard-main #resize-grip {{
            min-width: 16px;
            min-height: 16px;
            padding: 0px;
            margin: 0px 2px 2px 0px;
            border: 0px;
            background-color: transparent;
            background-image: none;
            box-shadow: none;
            opacity: 0.72;
        }}

        window#vboard-main #resize-grip:hover {{
            opacity: 1.0;
        }}

        window#vboard-main tooltip,
        window#vboard-main tooltip label {{
            color: #FFFFFF;
            padding: 4px;
        }}
    """
