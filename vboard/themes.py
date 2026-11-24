"""Theme CSS generation for Vboard (Apple macOS Light/Dark, Onboard Droid, High Contrast TV, Enhanced, Classic)."""


def parse_hex_rgb(hex_color, fallback=(10, 132, 255)):
    if not isinstance(hex_color, str):
        return fallback
    cleaned = hex_color.strip().lstrip("#")
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


def parse_rgb_value(value, fallback=(0, 0, 0)):
    try:
        parts = [int(component.strip()) for component in value.split(",")]
        if len(parts) == 3:
            return tuple(max(0, min(255, component)) for component in parts)
    except (AttributeError, ValueError):
        pass
    return fallback


def adjust_rgb(rgb_values, amount):
    return tuple(max(0, min(255, component + amount)) for component in rgb_values)


def rgb_css(rgb_values):
    return f"{rgb_values[0]}, {rgb_values[1]}, {rgb_values[2]}"


def luminance(rgb_values):
    red, green, blue = rgb_values
    return 0.299 * red + 0.587 * green + 0.114 * blue


def contrast_text_rgb(rgb_values):
    return (28, 28, 28) if luminance(rgb_values) >= 128 else (255, 255, 255)


def accent_color_for_rgb(rgb_values):
    red, green, blue = rgb_values
    maximum = max(rgb_values)
    minimum = min(rgb_values)
    if maximum == 0 or (maximum - minimum) / maximum < 0.25:
        return "#000000" if luminance(rgb_values) >= 128 else "#FFFFFF"

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
):
    gnome_specific = "background-image: none;" if "GNOME" in desktop_env else ""
    accent_rgb = parse_hex_rgb(accent_hex, fallback=(10, 132, 255))
    accent_darker = adjust_rgb(accent_rgb, -24)
    accent_lighter = adjust_rgb(accent_rgb, 34)
    accent_text = "#1D1D1F" if luminance(accent_rgb) >= 185 else "#FFFFFF"
    key_radius = max(0, min(18, int(round(key_radius))))
    key_spacing = max(1, min(8, int(round(key_spacing))))
    btn_radius = max(4, min(14, key_radius))
    window_radius = max(8, min(20, key_radius + 6))
    header_btn_min_w = max(34, int(round(header_font_size * 3.1)))
    header_btn_min_h = max(24, int(round(header_font_size * 2.2)))

    def rgba(rgb_values, alpha_scale=1.0):
        red, green, blue = rgb_values
        alpha = max(0.0, min(1.0, theme_opacity * alpha_scale))
        return f"rgba({red}, {green}, {blue}, {alpha:.3f})"

    command_modifier_rgb = (
        (0, 0, 0)
        if style_variant == "classic" and bg_color == "255,0,0"
        else accent_rgb
    )

    # Shared responsive typography & Apple Accessibility toolbar rules appended to every theme.
    is_light_ui = style_variant == "apple_light" or (
        style_variant in ("enhanced", "classic")
        and luminance(parse_rgb_value(bg_color)) >= 145
    )
    toolbar_bg = (
        rgba((255, 255, 255), 0.72) if is_light_ui else rgba((32, 36, 44), 0.75)
    )
    toolbar_border = (
        rgba((185, 190, 200), 0.9) if is_light_ui else rgba((82, 92, 110), 0.75)
    )
    toolbar_text = "#1D1D1F" if is_light_ui else "#F2F4F8"
    media_btn_bg = (
        rgba((220, 224, 232), 0.96) if is_light_ui else rgba((52, 56, 66), 0.95)
    )
    media_btn_hover = (
        rgba((205, 210, 220), 1.0) if is_light_ui else rgba((72, 78, 92), 1.0)
    )
    media_btn_border = (
        rgba((175, 180, 190), 0.9) if is_light_ui else rgba((90, 98, 115), 0.85)
    )
    orange_hint = "#FF9500" if is_light_ui else "#FF9F0A"

    shared_responsive_css = f"""
        #vboard-main headerbar,
        #vboard-main headerbar label,
        #vboard-main headerbar button label,
        #vboard-main #combobox button.combo {{
            font-size: {header_font_size}px;
        }}

        #vboard-main #grid button label {{
            font-size: {key_font_size}px;
        }}

        #vboard-main #grid button.compact-label label,
        #vboard-main #grid button.modifier-key label,
        #vboard-main #grid button.sidebar-key label {{
            font-size: {secondary_key_font_size}px;
        }}

        #vboard-main #grid button.altgr-hint {{
            border: 2px solid {orange_hint};
        }}

        #vboard-main #grid button.locked-modifier {{
            border: 2px solid {rgba(accent_lighter, 1.0)};
            box-shadow: inset 0 -3px {orange_hint};
        }}

        #vboard-main #grid button.dwell-active {{
            border: 2px solid {rgba(accent_lighter, 1.0)};
        }}

        #vboard-main #current-text-bar {{
            background-color: {toolbar_bg};
            border: 1px solid {toolbar_border};
            border-radius: {btn_radius}px;
            padding: 2px 8px;
        }}

        #vboard-main #current-text-label {{
            color: {toolbar_text};
            font-size: {suggestion_font_size}px;
            font-weight: 500;
        }}

        #vboard-main #current-text-clear {{
            min-width: 24px;
            min-height: 20px;
            padding: 0px 6px;
            border: 1px solid {toolbar_border};
            border-radius: {max(4, btn_radius - 2)}px;
            background-color: transparent;
            background-image: none;
            color: {toolbar_text};
            font-size: {max(9, header_font_size - 1)}px;
        }}

        #vboard-main #media-bar {{
            background-color: transparent;
        }}

        #vboard-main #media-bar button {{
            min-width: 30px;
            min-height: {max(22, header_btn_min_h - 4)}px;
            padding: 0px 6px;
            border: 1px solid {media_btn_border};
            border-radius: {max(4, btn_radius - 1)}px;
            color: {toolbar_text};
            background-color: {media_btn_bg};
            background-image: none;
            box-shadow: none;
            transition: none;
        }}

        #vboard-main #media-bar button label {{
            font-size: {max(9, secondary_key_font_size)}px;
            font-weight: 600;
        }}

        #vboard-main #media-bar button:hover {{
            border: 1px solid {rgba(accent_rgb, 1.0)};
            background-color: {media_btn_hover};
        }}
    """

    if style_variant in ("apple_dark", "apple_light"):
        dark = style_variant == "apple_dark"
        win_bg_top = (36, 36, 40) if dark else (234, 236, 240)
        win_bg_bot = (26, 26, 30) if dark else (222, 225, 231)
        win_border = (70, 70, 78) if dark else (184, 188, 196)
        hdr_bg = (32, 32, 36) if dark else (226, 229, 235)
        hdr_border = (58, 58, 66) if dark else (196, 200, 208)
        key_bg = (74, 74, 80) if dark else (255, 255, 255)
        key_bg_hover = (92, 92, 100) if dark else (244, 246, 250)
        key_bg_active = accent_rgb
        key_border = (96, 96, 104) if dark else (194, 198, 206)
        key_shadow = (
            "0 1px 0 rgba(0, 0, 0, 0.55), inset 0 1px rgba(255, 255, 255, 0.08)"
            if dark
            else "0 1px 0 rgba(0, 0, 0, 0.22)"
        )
        mod_bg = (50, 50, 56) if dark else (206, 210, 218)
        mod_hover = (66, 66, 74) if dark else (194, 199, 209)
        hdr_btn_bg = (54, 54, 60) if dark else (246, 247, 250)
        hdr_btn_hover = (70, 70, 78) if dark else (232, 235, 242)
        fg_color = "#F5F5F7" if dark else "#1D1D1F"
        sugg_bg = (46, 46, 52) if dark else (242, 244, 248)
        sugg_active_bg = (64, 64, 72) if dark else (255, 255, 255)

        css = f"""
        #vboard-main {{
            background-color: {rgba(win_bg_bot, 1.0)};
            background-image: linear-gradient(
                to bottom,
                {rgba(win_bg_top, 1.0)},
                {rgba(win_bg_bot, 1.0)}
            );
            border: 1px solid {rgba(win_border, 0.95)};
            border-radius: {window_radius}px;
            color: {fg_color};
        }}

        #vboard-main headerbar {{
            background-color: {rgba(hdr_bg, 0.98)};
            background-image: none;
            border: 0px;
            border-bottom: 1px solid {rgba(hdr_border, 0.95)};
            box-shadow: none;
            padding: 4px 8px;
            color: {fg_color};
        }}

        #vboard-main headerbar .title {{
            color: {fg_color};
            font-weight: 600;
        }}

        #vboard-main headerbar button {{
            min-width: {header_btn_min_w}px;
            min-height: {header_btn_min_h}px;
            padding: 0px 8px;
            border: 1px solid {rgba(key_border, 0.95)};
            border-radius: {btn_radius}px;
            margin: 0px 2px;
            color: {fg_color};
            background-color: {rgba(hdr_btn_bg, 1.0)};
            background-image: none;
            box-shadow: {key_shadow};
            transition: none;
        }}

        #vboard-main headerbar .titlebutton {{
            min-width: 34px;
            min-height: 30px;
        }}

        #vboard-main headerbar button:hover,
        #vboard-main #combobox button.combo:hover {{
            background-color: {rgba(hdr_btn_hover, 1.0)};
            border: 1px solid {rgba(accent_rgb, 0.85)};
        }}

        #vboard-main #grid {{
            padding: {max(3, key_spacing + 1)}px;
            background-color: transparent;
        }}

        #vboard-main #grid button {{
            min-width: 0px;
            min-height: 0px;
            padding: 0px 2px;
            border: 1px solid {rgba(key_border, 0.95)};
            border-radius: {key_radius}px;
            color: {fg_color};
            background-color: {rgba(key_bg, 1.0)};
            background-image: none;
            box-shadow: {key_shadow};
            margin: {key_spacing}px;
            transition: none;
            {gnome_specific}
        }}

        #vboard-main #grid button label {{
            font-weight: 500;
            color: {fg_color};
        }}

        #vboard-main #grid button.modifier-key,
        #vboard-main #grid button.sidebar-key {{
            background-color: {rgba(mod_bg, 1.0)};
        }}

        #vboard-main #grid button.modifier-key:hover,
        #vboard-main #grid button.sidebar-key:hover {{
            background-color: {rgba(mod_hover, 1.0)};
        }}

        #vboard-main #grid button:hover {{
            border: 1px solid {rgba(accent_rgb, 0.85)};
            background-color: {rgba(key_bg_hover, 1.0)};
        }}

        #vboard-main #grid button:active,
        #vboard-main #grid button:active:hover {{
            border: 1px solid {rgba(accent_darker, 1.0)};
            background-color: {rgba(key_bg_active, 1.0)};
            color: {accent_text};
            box-shadow: none;
        }}

        #vboard-main #grid button:active label {{
            color: {accent_text};
        }}

        #vboard-main #grid button.active-modifier,
        #vboard-main #grid button.active-command-modifier,
        #vboard-main #grid button.sidebar-key.active-layer {{
            border: 1px solid {rgba(accent_darker, 1.0)};
            background-color: {rgba(accent_rgb, 1.0)};
            background-image: none;
            color: {accent_text};
        }}

        #vboard-main #grid button.active-modifier label,
        #vboard-main #grid button.active-command-modifier label,
        #vboard-main #grid button.sidebar-key.active-layer label {{
            color: {accent_text};
            font-weight: 600;
        }}

        #vboard-main #esc-button,
        #vboard-main #layout-button {{
            min-width: {max(44, header_btn_min_w + 8)}px;
            min-height: {header_btn_min_h}px;
            border: 1px solid {rgba(key_border, 0.95)};
            border-radius: {btn_radius}px;
            color: {fg_color};
            background-color: {rgba(hdr_btn_bg, 1.0)};
            background-image: none;
            box-shadow: {key_shadow};
            transition: none;
        }}

        #vboard-main #layout-button label {{
            font-weight: 700;
            color: {fg_color};
        }}

        #vboard-main #layout-button.active-layout {{
            border: 1px solid {rgba(accent_darker, 1.0)};
            background-color: {rgba(accent_rgb, 1.0)};
            background-image: none;
            color: {accent_text};
        }}

        #vboard-main #layout-button.active-layout label {{
            color: {accent_text};
        }}

        #vboard-main #combobox button.combo {{
            color: {fg_color};
            padding: 3px 8px;
            border: 1px solid {rgba(key_border, 0.95)};
            border-radius: {btn_radius}px;
            background-color: {rgba(hdr_btn_bg, 1.0)};
            background-image: none;
            box-shadow: {key_shadow};
        }}

        #vboard-main #suggestion-bar {{
            background-color: transparent;
        }}

        #vboard-main #suggestion-button {{
            border: 1px solid {rgba(key_border, 0.7)};
            border-radius: {btn_radius}px;
            background-color: {rgba(sugg_bg, 0.95)};
            background-image: none;
            box-shadow: none;
            min-height: 0px;
            padding: 2px 8px;
            transition: none;
        }}

        #vboard-main #suggestion-button label,
        #vboard-main #suggestion-button:disabled label {{
            color: {fg_color};
            font-size: {suggestion_font_size}px;
            font-weight: 500;
        }}

        #vboard-main #suggestion-button.has-suggestion {{
            border: 1px solid {rgba(key_border, 1.0)};
            background-color: {rgba(sugg_active_bg, 1.0)};
            box-shadow: {key_shadow};
        }}

        #vboard-main #suggestion-button.has-suggestion:hover {{
            border: 1px solid {rgba(accent_rgb, 1.0)};
            background-color: {rgba(accent_rgb, 0.18)};
        }}

        #vboard-main tooltip {{
            color: white;
            padding: 5px;
        }}
        """
        return css + shared_responsive_css

    if style_variant == "onboard":
        css = f"""
        #vboard-main {{
            background-color: {rgba((18, 24, 33), 1.0)};
            background-image: linear-gradient(
                to bottom,
                {rgba((28, 35, 46), 1.0)},
                {rgba((18, 24, 33), 1.0)}
            );
            border: 1px solid {rgba((7, 11, 18), 0.95)};
            border-radius: {window_radius}px;
            color: {rgba((239, 243, 250), 1.0)};
        }}

        #vboard-main headerbar {{
            background-color: {rgba((31, 39, 53), 0.96)};
            background-image: linear-gradient(
                to bottom,
                {rgba((52, 61, 78), 0.96)},
                {rgba((31, 39, 53), 0.96)}
            );
            border: 0px;
            border-bottom: 1px solid {rgba((8, 12, 19), 0.9)};
            box-shadow: none;
            padding: 4px 6px;
        }}

        #vboard-main headerbar button {{
            min-width: {header_btn_min_w}px;
            min-height: {header_btn_min_h}px;
            padding: 0px 8px;
            border: 1px solid {rgba((13, 21, 33), 1.0)};
            border-radius: {btn_radius}px;
            margin: 0px 2px;
            color: {rgba((239, 243, 250), 1.0)};
            background-color: {rgba((38, 49, 66), 1.0)};
            background-image: linear-gradient(
                to bottom,
                {rgba((69, 80, 101), 1.0)},
                {rgba((40, 50, 68), 1.0)}
            );
            box-shadow: inset 0 1px {rgba((255, 255, 255), 0.08)};
            transition: none;
            {gnome_specific}
        }}

        #vboard-main headerbar .titlebutton {{
            min-width: 44px;
            min-height: 36px;
        }}

        #vboard-main headerbar button:hover,
        #vboard-main #combobox button.combo:hover {{
            background-image: linear-gradient(
                to bottom,
                {rgba((81, 94, 118), 1.0)},
                {rgba((49, 59, 79), 1.0)}
            );
        }}

        #vboard-main #grid {{
            padding: {max(3, key_spacing + 1)}px;
            background-color: transparent;
        }}

        #vboard-main #grid button {{
            min-width: 0px;
            min-height: 0px;
            padding: 0px 2px;
            border: 1px solid {rgba((14, 21, 33), 1.0)};
            border-radius: {key_radius}px;
            color: {rgba((245, 247, 251), 1.0)};
            background-color: {rgba((48, 57, 74), 1.0)};
            background-image: linear-gradient(
                to bottom,
                {rgba((72, 83, 106), 1.0)},
                {rgba((43, 52, 70), 1.0)}
            );
            box-shadow: inset 0 1px {rgba((255, 255, 255), 0.09)},
                        0 1px 0 {rgba((5, 8, 13), 0.55)};
            margin: {key_spacing}px;
            transition: none;
            {gnome_specific}
        }}

        #vboard-main #grid button label {{
            font-weight: 500;
        }}

        #vboard-main #grid button.sidebar-key {{
            background-color: {rgba((35, 44, 61), 1.0)};
            background-image: linear-gradient(
                to bottom,
                {rgba((58, 69, 90), 1.0)},
                {rgba((33, 41, 57), 1.0)}
            );
        }}

        #vboard-main #grid button.sidebar-key.active-layer {{
            border: 1px solid {rgba(accent_lighter, 1.0)};
            background-image: linear-gradient(
                to bottom,
                {rgba(accent_rgb, 1.0)},
                {rgba(accent_darker, 1.0)}
            );
            color: {accent_text};
        }}

        #vboard-main #grid button:hover {{
            border: 1px solid {rgba((110, 126, 151), 1.0)};
            background-image: linear-gradient(
                to bottom,
                {rgba((86, 98, 123), 1.0)},
                {rgba((50, 60, 81), 1.0)}
            );
        }}

        #vboard-main #grid button:active,
        #vboard-main #grid button:active:hover {{
            border: 1px solid {rgba((141, 164, 196), 1.0)};
            background-image: linear-gradient(
                to bottom,
                {rgba((39, 48, 63), 1.0)},
                {rgba((70, 81, 106), 1.0)}
            );
        }}

        #vboard-main #grid button.active-modifier {{
            border: 1px solid {rgba((138, 163, 200), 1.0)};
            background-image: linear-gradient(
                to bottom,
                {rgba((96, 112, 141), 1.0)},
                {rgba((55, 69, 90), 1.0)}
            );
            {gnome_specific}
        }}

        #vboard-main #grid button.active-command-modifier {{
            border: 1px solid {rgba(accent_lighter, 1.0)};
            color: {accent_text};
            background-color: {rgba(accent_rgb, 1.0)};
            background-image: linear-gradient(
                to bottom,
                {rgba(accent_rgb, 0.95)},
                {rgba(accent_darker, 0.95)}
            );
            {gnome_specific}
        }}

        #vboard-main #grid button.active-command-modifier label {{
            color: {accent_text};
        }}

        #vboard-main #esc-button,
        #vboard-main #layout-button {{
            min-width: {max(48, header_btn_min_w + 10)}px;
            min-height: {header_btn_min_h}px;
            border: 1px solid {rgba((17, 24, 36), 1.0)};
            border-radius: {btn_radius}px;
            color: {rgba((247, 248, 251), 1.0)};
            background-color: {rgba((51, 64, 89), 1.0)};
            background-image: linear-gradient(
                to bottom,
                {rgba((86, 98, 123), 1.0)},
                {rgba((48, 58, 78), 1.0)}
            );
            box-shadow: inset 0 1px {rgba((255, 255, 255), 0.1)};
            transition: none;
        }}

        #vboard-main #layout-button label {{
            font-weight: 700;
        }}

        #vboard-main #esc-button:hover,
        #vboard-main #layout-button:hover {{
            border: 1px solid {rgba((142, 166, 199), 1.0)};
            background-image: linear-gradient(
                to bottom,
                {rgba((97, 112, 139), 1.0)},
                {rgba((54, 65, 86), 1.0)}
            );
        }}

        #vboard-main #layout-button.active-layout {{
            border: 1px solid {rgba(accent_lighter, 1.0)};
            background-image: linear-gradient(
                to bottom,
                {rgba(accent_rgb, 1.0)},
                {rgba(accent_darker, 1.0)}
            );
            color: {accent_text};
        }}

        #vboard-main #layout-button.active-layout label {{
            color: {accent_text};
        }}

        #vboard-main tooltip {{
            color: white;
            padding: 5px;
        }}

        #vboard-main #combobox button.combo {{
            color: {rgba((239, 243, 250), 1.0)};
            padding: 5px;
            border: 1px solid {rgba((13, 21, 33), 1.0)};
            border-radius: {btn_radius}px;
            background-image: linear-gradient(
                to bottom,
                {rgba((69, 80, 101), 1.0)},
                {rgba((40, 50, 68), 1.0)}
            );
        }}

        #vboard-main #suggestion-bar {{
            background-color: transparent;
        }}

        #vboard-main #suggestion-button {{
            border: 1px solid {rgba((17, 25, 37), 1.0)};
            border-radius: {btn_radius}px;
            background-color: {rgba((35, 45, 61), 0.94)};
            background-image: linear-gradient(
                to bottom,
                {rgba((52, 63, 84), 0.94)},
                {rgba((33, 42, 58), 0.94)}
            );
            box-shadow: inset 0 1px {rgba((255, 255, 255), 0.06)};
            min-height: 0px;
            padding: 2px 8px;
        }}

        #vboard-main #suggestion-button label,
        #vboard-main #suggestion-button:disabled label {{
            color: {rgba((245, 247, 251), 1.0)};
            font-size: {suggestion_font_size}px;
        }}

        #vboard-main #suggestion-button.has-suggestion {{
            border: 1px solid {rgba((88, 105, 133), 1.0)};
            background-image: linear-gradient(
                to bottom,
                {rgba((68, 81, 106), 1.0)},
                {rgba((44, 54, 73), 1.0)}
            );
        }}

        #vboard-main #suggestion-button.has-suggestion:hover {{
            border: 1px solid {rgba((132, 155, 189), 1.0)};
            background-image: linear-gradient(
                to bottom,
                {rgba((82, 96, 124), 1.0)},
                {rgba((52, 63, 85), 1.0)}
            );
        }}
        """
        return css + shared_responsive_css

    if style_variant == "high_contrast_tv":
        css = f"""
        #vboard-main {{
            background-color: {rgba((36, 36, 36), 1.0)};
            background-image: none;
            border: 2px solid {rgba((110, 110, 110), 1.0)};
            border-radius: {window_radius}px;
            color: #FFFFFF;
        }}

        #vboard-main headerbar {{
            background-color: {rgba((28, 28, 28), 0.98)};
            background-image: none;
            border: 0px;
            border-bottom: 2px solid {rgba((96, 96, 96), 1.0)};
            box-shadow: none;
            padding: 4px 6px;
        }}

        #vboard-main headerbar button {{
            min-width: {header_btn_min_w}px;
            min-height: {header_btn_min_h}px;
            padding: 0px 8px;
            border: 2px solid {rgba((150, 150, 150), 1.0)};
            border-radius: {btn_radius}px;
            margin: 0px 2px;
            color: #FFFFFF;
            background-color: {rgba((48, 48, 48), 1.0)};
            background-image: none;
            box-shadow: none;
            transition: none;
        }}

        #vboard-main headerbar .titlebutton {{
            min-width: 46px;
            min-height: 36px;
        }}

        #vboard-main headerbar button:hover,
        #vboard-main #combobox button.combo:hover {{
            border: 2px solid #FFD600;
            background-color: {rgba((78, 78, 78), 1.0)};
        }}

        #vboard-main #grid {{
            padding: {max(4, key_spacing + 1)}px;
            background-color: transparent;
        }}

        #vboard-main #grid button {{
            min-width: 0px;
            min-height: 0px;
            padding: 0px 2px;
            border: 2px solid {rgba((136, 136, 136), 1.0)};
            border-radius: {key_radius}px;
            color: #FFFFFF;
            background-color: {rgba((44, 44, 44), 1.0)};
            background-image: none;
            box-shadow: none;
            margin: {key_spacing}px;
            transition: none;
        }}

        #vboard-main #grid button label {{
            font-weight: 700;
        }}

        #vboard-main #grid button.sidebar-key {{
            border: 2px solid {rgba((165, 165, 165), 1.0)};
            background-color: {rgba((32, 37, 45), 1.0)};
        }}

        #vboard-main #grid button.sidebar-key.active-layer {{
            border: 2px solid #FFFFFF;
            background-color: {rgba(accent_rgb, 1.0)};
            color: {accent_text};
        }}

        #vboard-main #grid button:hover {{
            border: 2px solid #FFD600;
            background-color: {rgba((72, 72, 72), 1.0)};
        }}

        #vboard-main #grid button:active,
        #vboard-main #grid button:active:hover {{
            border: 2px solid #FFFFFF;
            background-color: {rgba(accent_rgb, 1.0)};
            color: {accent_text};
        }}

        #vboard-main #grid button.active-modifier {{
            border: 2px solid #FFD600;
            background-color: {rgba(accent_rgb, 1.0)};
            color: {accent_text};
        }}

        #vboard-main #grid button.active-command-modifier {{
            border: 2px solid #FFFFFF;
            color: #FFFFFF;
            background-color: {rgba((210, 42, 42), 1.0)};
            background-image: none;
        }}

        #vboard-main #grid button.active-command-modifier label {{
            color: #FFFFFF;
        }}

        #vboard-main #esc-button,
        #vboard-main #layout-button {{
            min-width: {max(50, header_btn_min_w + 10)}px;
            min-height: {header_btn_min_h}px;
            border: 2px solid {rgba((185, 185, 185), 1.0)};
            border-radius: {btn_radius}px;
            color: #FFFFFF;
            background-color: {rgba((56, 56, 56), 1.0)};
            background-image: none;
            box-shadow: none;
            transition: none;
        }}

        #vboard-main #layout-button label {{
            font-weight: 700;
        }}

        #vboard-main #esc-button:hover,
        #vboard-main #layout-button:hover {{
            border: 2px solid #FFD600;
            background-color: {rgba((82, 82, 82), 1.0)};
        }}

        #vboard-main #layout-button.active-layout {{
            border: 2px solid #FFFFFF;
            background-color: {rgba(accent_rgb, 1.0)};
            color: {accent_text};
        }}

        #vboard-main #layout-button.active-layout label {{
            color: {accent_text};
        }}

        #vboard-main tooltip {{
            color: #FFFFFF;
            padding: 5px;
        }}

        #vboard-main #combobox button.combo {{
            color: #FFFFFF;
            padding: 5px;
            border: 2px solid {rgba((150, 150, 150), 1.0)};
            border-radius: {btn_radius}px;
            background-color: {rgba((48, 48, 48), 1.0)};
            background-image: none;
        }}

        #vboard-main #suggestion-bar {{
            background-color: transparent;
        }}

        #vboard-main #suggestion-button {{
            border: 2px solid {rgba((110, 110, 110), 1.0)};
            border-radius: {btn_radius}px;
            background-color: {rgba((36, 36, 36), 1.0)};
            background-image: none;
            box-shadow: none;
            min-height: 0px;
            padding: 2px 8px;
        }}

        #vboard-main #suggestion-button label,
        #vboard-main #suggestion-button:disabled label {{
            color: #FFFFFF;
            font-size: {suggestion_font_size}px;
            font-weight: 700;
        }}

        #vboard-main #suggestion-button.has-suggestion {{
            border: 2px solid #FFFFFF;
            background-color: {rgba((56, 56, 56), 1.0)};
        }}

        #vboard-main #suggestion-button.has-suggestion:hover {{
            border: 2px solid #FFD600;
            background-color: {rgba(accent_rgb, 1.0)};
        }}
        """
        return css + shared_responsive_css

    if style_variant == "enhanced":
        base_rgb = parse_rgb_value(bg_color)
        is_light_theme = luminance(base_rgb) >= 128
        text_rgb = contrast_text_rgb(base_rgb)
        accent = accent_color_for_rgb(base_rgb)
        step = -18 if is_light_theme else 26
        header_rgb = adjust_rgb(base_rgb, -14 if is_light_theme else 14)
        key_rgb = adjust_rgb(base_rgb, step)
        hover_rgb = adjust_rgb(key_rgb, -18 if is_light_theme else 22)
        pressed_rgb = adjust_rgb(key_rgb, -34 if is_light_theme else 40)
        suggestion_rgb = adjust_rgb(base_rgb, -10 if is_light_theme else 18)

        css = f"""
        #vboard-main {{
            background-color: {rgba(base_rgb, 1.0)};
            background-image: none;
            border: 0px;
            border-radius: {window_radius}px;
            color: rgb({rgb_css(text_rgb)});
        }}

        #vboard-main headerbar {{
            background-color: {rgba(header_rgb, 1.0)};
            background-image: none;
            border: 0px;
            box-shadow: none;
            padding: 4px 6px;
        }}

        #vboard-main headerbar button {{
            min-width: {header_btn_min_w}px;
            min-height: {header_btn_min_h}px;
            padding: 0px 8px;
            border: 1px solid transparent;
            border-radius: {btn_radius}px;
            margin: 0px 2px;
            color: rgb({rgb_css(text_rgb)});
            background-color: transparent;
            background-image: none;
            box-shadow: none;
            transition: none;
            {gnome_specific}
        }}

        #vboard-main headerbar .titlebutton {{
            min-width: 44px;
            min-height: 36px;
        }}

        #vboard-main headerbar button:hover,
        #vboard-main #combobox button.combo:hover {{
            border: 1px solid {accent};
            background-color: {rgba(hover_rgb, 1.0)};
        }}

        #vboard-main #grid {{
            padding: {max(3, key_spacing + 1)}px;
            background-color: transparent;
        }}

        #vboard-main #grid button {{
            min-width: 0px;
            min-height: 0px;
            padding: 0px 2px;
            border: 1px solid transparent;
            border-radius: {key_radius}px;
            color: rgb({rgb_css(text_rgb)});
            background-color: {rgba(key_rgb, 1.0)};
            background-image: none;
            box-shadow: none;
            margin: {key_spacing}px;
            transition: none;
            {gnome_specific}
        }}

        #vboard-main #grid button.sidebar-key {{
            background-color: {rgba(header_rgb, 1.0)};
        }}

        #vboard-main #grid button.active-layer {{
            border: 1px solid {accent};
            background-color: {rgba(pressed_rgb, 1.0)};
        }}

        #vboard-main button {{
            background-color: transparent;
            color: rgb({rgb_css(text_rgb)});
        }}

        #vboard-main #grid button:hover {{
            border: 1px solid {accent};
            background-color: {rgba(hover_rgb, 1.0)};
        }}

        #vboard-main #grid button:active,
        #vboard-main #grid button:active:hover {{
            border: 1px solid rgb({rgb_css(text_rgb)});
            background-color: {rgba(pressed_rgb, 1.0)};
        }}

        #vboard-main #grid button.active-modifier {{
            border: 1px solid {accent};
            background-color: {rgba(pressed_rgb, 1.0)};
            {gnome_specific}
        }}

        #vboard-main #grid button.active-command-modifier {{
            border: 1px solid {rgba(command_modifier_rgb, 1.0)};
            color: {accent_text};
            background-color: {rgba(command_modifier_rgb, 1.0)};
            background-image: none;
            {gnome_specific}
        }}

        #vboard-main #grid button.active-command-modifier label {{
            color: {accent_text};
        }}

        #vboard-main #esc-button,
        #vboard-main #layout-button {{
            min-width: {max(48, header_btn_min_w + 10)}px;
            min-height: {header_btn_min_h}px;
            border: 1px solid transparent;
            border-radius: {btn_radius}px;
            color: rgb({rgb_css(text_rgb)});
            background-color: {rgba(key_rgb, 1.0)};
            background-image: none;
            transition: none;
        }}

        #vboard-main #layout-button label {{
            font-weight: 700;
        }}

        #vboard-main #esc-button:hover,
        #vboard-main #layout-button:hover {{
            border: 1px solid {accent};
            background-color: {rgba(hover_rgb, 1.0)};
        }}

        #vboard-main #layout-button.active-layout {{
            border: 1px solid {rgba(command_modifier_rgb, 1.0)};
            color: {accent_text};
            background-color: {rgba(command_modifier_rgb, 1.0)};
            background-image: none;
        }}

        #vboard-main #layout-button.active-layout label {{
            color: {accent_text};
        }}

        #vboard-main tooltip {{
            color: white;
            padding: 5px;
        }}

        #vboard-main #combobox button.combo {{
            color: rgb({rgb_css(text_rgb)});
            padding: 5px;
            border: 1px solid transparent;
            border-radius: {btn_radius}px;
            background-color: transparent;
            background-image: none;
        }}

        #vboard-main #suggestion-bar {{
            background-color: transparent;
        }}

        #vboard-main #suggestion-button {{
            border: 1px solid transparent;
            border-radius: {btn_radius}px;
            background-color: {rgba(suggestion_rgb, 1.0)};
            background-image: none;
            box-shadow: none;
            min-height: 0px;
            padding: 2px 8px;
        }}

        #vboard-main #suggestion-button label,
        #vboard-main #suggestion-button:disabled label {{
            color: rgb({rgb_css(text_rgb)});
            font-size: {suggestion_font_size}px;
        }}

        #vboard-main #suggestion-button.has-suggestion {{
            border: 1px solid {accent};
            background-color: {rgba(key_rgb, 1.0)};
        }}

        #vboard-main #suggestion-button.has-suggestion:hover {{
            border: 1px solid {accent};
            background-color: {rgba(hover_rgb, 1.0)};
        }}
        """
        return css + shared_responsive_css

    # Classic theme
    css = f"""
    #vboard-main {{
        background-color: rgba({bg_color}, {theme_opacity:.3f});
        color: {text_color};
    }}

    #vboard-main headerbar {{
        background-color: rgba({bg_color}, {theme_opacity:.3f});
        border: 0px;
        box-shadow: none;
    }}

    #vboard-main headerbar button {{
        min-width: {header_btn_min_w}px;
        min-height: {header_btn_min_h}px;
        padding: 0px 8px;
        border: 0px;
        margin: 0px;
        {gnome_specific}
    }}

    #vboard-main headerbar .titlebutton {{
        min-width: 44px;
        min-height: 36px;
    }}

    #vboard-main #grid button {{
        min-width: 0px;
        min-height: 0px;
        padding: 0px 2px;
        border: 1px solid rgba(84, 84, 84, 0.35);
        border-radius: {key_radius}px;
        margin: {key_spacing}px;
        transition: none;
        {gnome_specific}
    }}

    #vboard-main #grid button.active-layer {{
        border: 2px solid {rgba(accent_rgb, 1.0)};
    }}

    #vboard-main button {{
        background-color: transparent;
        color: {text_color};
    }}

    #vboard-main #grid button:hover {{
        border: 1px solid {rgba(accent_rgb, 1.0)};
    }}

    #vboard-main #grid button.pressed,
    #vboard-main #grid button.pressed:hover {{
        border: 1px solid {text_color};
    }}

    #vboard-main #grid button.active-modifier {{
        border: 1px solid {rgba(accent_rgb, 1.0)};
        {gnome_specific}
    }}

    #vboard-main #grid button.active-command-modifier {{
        border: 1px solid rgb({rgb_css(command_modifier_rgb)});
        color: {accent_text};
        background-color: {rgba(command_modifier_rgb, 1.0)};
        background-image: none;
        {gnome_specific}
    }}

    #vboard-main #grid button.active-command-modifier label {{
        color: {accent_text};
    }}

    #vboard-main #esc-button,
    #vboard-main #layout-button {{
        min-width: {max(48, header_btn_min_w + 10)}px;
        border: 1px solid {text_color};
        border-radius: {btn_radius}px;
        background-image: none;
        transition: none;
    }}

    #vboard-main #layout-button label {{
        font-weight: 700;
    }}

    #vboard-main #esc-button:hover,
    #vboard-main #layout-button:hover {{
        border: 1px solid {rgba(accent_rgb, 1.0)};
    }}

    #vboard-main #layout-button.active-layout {{
        border: 1px solid rgb({rgb_css(command_modifier_rgb)});
        color: {accent_text};
        background-color: {rgba(command_modifier_rgb, 1.0)};
        background-image: none;
    }}

    #vboard-main #layout-button.active-layout label {{
        color: {accent_text};
    }}

    #vboard-main tooltip {{
        color: white;
        padding: 5px;
    }}

    #vboard-main #combobox button.combo {{
        color: {text_color};
        padding: 5px;
    }}

    #vboard-main #suggestion-bar {{
        background-color: transparent;
    }}

    #vboard-main #suggestion-button {{
        border: 1px solid transparent;
        border-radius: {btn_radius}px;
        background-image: none;
        min-height: 0px;
        padding: 2px 8px;
    }}

    #vboard-main #suggestion-button label,
    #vboard-main #suggestion-button:disabled label {{
        color: {text_color};
        font-size: {suggestion_font_size}px;
    }}

    #vboard-main #suggestion-button.has-suggestion {{
        border: 1px solid {text_color};
    }}

    #vboard-main #suggestion-button.has-suggestion:hover {{
        border: 1px solid {rgba(accent_rgb, 1.0)};
    }}
    """
    return css + shared_responsive_css
