"""Vector SVG icon loader with pure-Cairo vector fallback and theme-aware tinting."""

import math
import os
import re

import cairo
from gi.repository import GdkPixbuf

from .gtk import GLib, Gtk

ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")

NAMED_COLORS = {
    "white": "#FFFFFF",
    "black": "#000000",
    "gray": "#808080",
    "grey": "#808080",
    "red": "#FF0000",
    "green": "#00FF00",
    "blue": "#0000FF",
}

_SVG_LOADER_SUPPORTED = None
_ICON_CACHE = {}
_MAX_CACHE_ENTRIES = 256


def normalize_color_to_hex(color, fallback="#F5F5F7"):
    if not isinstance(color, str):
        return fallback
    raw = color.strip()
    if not raw:
        return fallback
    lower = raw.lower()
    if lower in NAMED_COLORS:
        return NAMED_COLORS[lower]
    if raw.startswith("#") and len(raw) == 7:
        try:
            int(raw[1:], 16)
            return raw.upper()
        except ValueError:
            return fallback
    if raw.startswith("#") and len(raw) == 4:
        try:
            r, g, b = raw[1], raw[2], raw[3]
            int(raw[1:], 16)
            return f"#{r}{r}{g}{g}{b}{b}".upper()
        except ValueError:
            return fallback
    match = re.match(r"^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", lower)
    if match:
        r, g, b = (max(0, min(255, int(match.group(i)))) for i in (1, 2, 3))
        return f"#{r:02X}{g:02X}{b:02X}"
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) == 3:
        try:
            r, g, b = (max(0, min(255, int(p))) for p in parts)
            return f"#{r:02X}{g:02X}{b:02X}"
        except ValueError:
            pass
    return fallback


def _hex_to_rgb_floats(hex_color):
    cleaned = normalize_color_to_hex(hex_color).lstrip("#")
    return (
        int(cleaned[0:2], 16) / 255.0,
        int(cleaned[2:4], 16) / 255.0,
        int(cleaned[4:6], 16) / 255.0,
    )


def get_svg_path(icon_name):
    return os.path.join(ICON_DIR, f"{icon_name}.svg")


def _load_svg_pixbuf(icon_name, size_px, hex_color):
    global _SVG_LOADER_SUPPORTED
    if _SVG_LOADER_SUPPORTED is False:
        return None

    svg_path = get_svg_path(icon_name)
    if not os.path.isfile(svg_path):
        return None

    try:
        with open(svg_path, "r", encoding="utf-8") as handle:
            svg_text = handle.read()
    except OSError:
        return None

    tinted_svg = svg_text.replace("currentColor", hex_color).encode("utf-8")
    try:
        loader = GdkPixbuf.PixbufLoader.new_with_type("svg")
        loader.set_size(size_px, size_px)
        loader.write(tinted_svg)
        loader.close()
        pixbuf = loader.get_pixbuf()
        if pixbuf is not None:
            _SVG_LOADER_SUPPORTED = True
            return pixbuf
    except GLib.Error:
        _SVG_LOADER_SUPPORTED = False
    except Exception:
        pass
    return None


def _draw_sun(cr, radius, inner_ray, outer_ray):
    cr.arc(12.0, 12.0, radius, 0, 2 * math.pi)
    cr.stroke()
    for step in range(8):
        angle = step * (math.pi / 4.0)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        cr.move_to(12.0 + cos_a * inner_ray, 12.0 + sin_a * inner_ray)
        cr.line_to(12.0 + cos_a * outer_ray, 12.0 + sin_a * outer_ray)
        cr.stroke()


def _draw_speaker_cone(cr, x_offset=0.0):
    cr.move_to(4.0 + x_offset, 9.5)
    cr.line_to(8.0 + x_offset, 9.5)
    cr.line_to(12.6 + x_offset, 5.5)
    cr.line_to(12.6 + x_offset, 18.5)
    cr.line_to(8.0 + x_offset, 14.5)
    cr.line_to(4.0 + x_offset, 14.5)
    cr.close_path()
    cr.stroke()


def _draw_vector_icon_cairo(cr, icon_name):
    cr.set_line_width(1.85)
    cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.set_line_join(cairo.LINE_JOIN_ROUND)

    if icon_name == "brightness-down":
        _draw_sun(cr, 3.4, 5.4, 6.9)
    elif icon_name == "brightness-up":
        _draw_sun(cr, 4.2, 6.8, 9.5)
    elif icon_name == "media-previous":
        cr.move_to(5.0, 6.5)
        cr.line_to(5.0, 17.5)
        cr.stroke()
        for tip_x, base_x in ((6.6, 12.5), (13.5, 19.4)):
            cr.move_to(base_x, 6.8)
            cr.line_to(tip_x, 12.0)
            cr.line_to(base_x, 17.2)
            cr.close_path()
            cr.stroke()
    elif icon_name == "media-play-pause":
        cr.move_to(4.5, 6.8)
        cr.line_to(12.2, 12.0)
        cr.line_to(4.5, 17.2)
        cr.close_path()
        cr.stroke()
        cr.move_to(15.5, 6.8)
        cr.line_to(15.5, 17.2)
        cr.move_to(19.5, 6.8)
        cr.line_to(19.5, 17.2)
        cr.stroke()
    elif icon_name == "media-next":
        for base_x, tip_x in ((4.6, 10.5), (11.5, 17.4)):
            cr.move_to(base_x, 6.8)
            cr.line_to(tip_x, 12.0)
            cr.line_to(base_x, 17.2)
            cr.close_path()
            cr.stroke()
        cr.move_to(19.0, 6.5)
        cr.line_to(19.0, 17.5)
        cr.stroke()
    elif icon_name == "audio-mute":
        _draw_speaker_cone(cr, 0.0)
        cr.move_to(16.0, 9.2)
        cr.line_to(20.8, 14.8)
        cr.move_to(20.8, 9.2)
        cr.line_to(16.0, 14.8)
        cr.stroke()
    elif icon_name == "audio-low":
        _draw_speaker_cone(cr, 0.5)
        cr.arc(13.8, 12.0, 4.3, -math.pi / 3.2, math.pi / 3.2)
        cr.stroke()
    elif icon_name == "audio-high":
        _draw_speaker_cone(cr, -0.5)
        cr.arc(12.6, 12.0, 4.2, -math.pi / 3.2, math.pi / 3.2)
        cr.stroke()
        cr.arc(12.6, 12.0, 7.6, -math.pi / 3.0, math.pi / 3.0)
        cr.stroke()
    elif icon_name == "screenshot":
        cr.move_to(4.0, 8.5)
        cr.line_to(7.2, 8.5)
        cr.line_to(8.8, 6.0)
        cr.line_to(15.2, 6.0)
        cr.line_to(16.8, 8.5)
        cr.line_to(20.0, 8.5)
        cr.arc(20.0, 10.0, 1.5, -math.pi / 2.0, 0.0)
        cr.line_to(21.5, 18.0)
        cr.arc(20.0, 18.0, 1.5, 0.0, math.pi / 2.0)
        cr.line_to(4.0, 19.5)
        cr.arc(4.0, 18.0, 1.5, math.pi / 2.0, math.pi)
        cr.line_to(2.5, 10.0)
        cr.arc(4.0, 10.0, 1.5, math.pi, 1.5 * math.pi)
        cr.close_path()
        cr.stroke()
        cr.arc(12.0, 13.8, 3.1, 0, 2 * math.pi)
        cr.stroke()
    elif icon_name == "backspace":
        cr.move_to(8.5, 6.0)
        cr.line_to(20.5, 6.0)
        cr.line_to(20.5, 18.0)
        cr.line_to(8.5, 18.0)
        cr.line_to(3.0, 12.0)
        cr.close_path()
        cr.stroke()
        cr.move_to(11.8, 9.5)
        cr.line_to(16.8, 14.5)
        cr.move_to(16.8, 9.5)
        cr.line_to(11.8, 14.5)
        cr.stroke()
    elif icon_name == "settings":
        cr.arc(12.0, 12.0, 3.1, 0, 2 * math.pi)
        cr.stroke()
        cr.arc(12.0, 12.0, 6.6, 0, 2 * math.pi)
        cr.stroke()
        for step in range(8):
            angle = step * (math.pi / 4.0)
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            cr.move_to(12.0 + cos_a * 6.8, 12.0 + sin_a * 6.8)
            cr.line_to(12.0 + cos_a * 9.3, 12.0 + sin_a * 9.3)
            cr.stroke()
    elif icon_name == "menu":
        cr.set_line_width(2.0)
        for y in (7.0, 12.0, 17.0):
            cr.move_to(4.5, y)
            cr.line_to(19.5, y)
            cr.stroke()
    elif icon_name == "clear":
        cr.set_line_width(2.0)
        cr.move_to(6.5, 6.5)
        cr.line_to(17.5, 17.5)
        cr.move_to(17.5, 6.5)
        cr.line_to(6.5, 17.5)
        cr.stroke()
    elif icon_name == "resize-grip":
        cr.set_line_width(1.9)
        cr.move_to(8.0, 20.0)
        cr.line_to(20.0, 8.0)
        cr.move_to(13.0, 20.0)
        cr.line_to(20.0, 13.0)
        cr.move_to(18.0, 20.0)
        cr.line_to(20.0, 18.0)
        cr.stroke()
    else:
        cr.arc(12.0, 12.0, 6.0, 0, 2 * math.pi)
        cr.stroke()


def _render_cairo_surface(icon_name, size_px, hex_color):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, size_px, size_px)
    cr = cairo.Context(surface)
    cr.set_antialias(cairo.ANTIALIAS_BEST)
    scale = size_px / 24.0
    cr.scale(scale, scale)
    r, g, b = _hex_to_rgb_floats(hex_color)
    cr.set_source_rgba(r, g, b, 1.0)
    _draw_vector_icon_cairo(cr, icon_name)
    surface.flush()
    return surface


def render_icon_image(icon_name, size_px=16, color="#F5F5F7"):
    size_px = max(10, min(48, int(round(size_px))))
    hex_color = normalize_color_to_hex(color)
    cache_key = (icon_name, size_px, hex_color)
    cached = _ICON_CACHE.get(cache_key)
    if cached is None:
        if len(_ICON_CACHE) >= _MAX_CACHE_ENTRIES:
            _ICON_CACHE.clear()
        pixbuf = _load_svg_pixbuf(icon_name, size_px, hex_color)
        if pixbuf is not None:
            cached = ("pixbuf", pixbuf)
        else:
            cached = ("surface", _render_cairo_surface(icon_name, size_px, hex_color))
        _ICON_CACHE[cache_key] = cached

    kind, asset = cached
    if kind == "pixbuf":
        image = Gtk.Image.new_from_pixbuf(asset)
    else:
        image = Gtk.Image.new_from_surface(asset)
    image.show()
    return image


def set_button_vector_icon(button, icon_name, size_px=16, color="#F5F5F7"):
    image = render_icon_image(icon_name, size_px=size_px, color=color)
    button.set_label("")
    button.set_image(image)
    button.set_always_show_image(True)
    return image
