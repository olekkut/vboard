"""User preset storage and management for Vboard customization profiles."""

import json
import os
import re

PRESET_KEYS = (
    "style_variant",
    "bg_color",
    "text_color",
    "opacity",
    "accent_color",
    "font_scale",
    "font_weight",
    "key_corner_radius",
    "key_spacing",
    "key_border_width",
    "window_border_width",
    "window_border_color",
    "key_shadow_enabled",
    "use_custom_colors",
    "custom_window_bg",
    "custom_key_bg",
    "custom_modifier_bg",
    "custom_text_color",
    "custom_key_border_color",
    "keyboard_mode",
    "show_media_row",
    "show_current_text_bar",
    "show_fast_layout_bar",
    "show_modifier_hints",
    "text_prediction_enabled",
)


def sanitize_preset_filename(name):
    cleaned = re.sub(r"[^\w\-. ]+", "", (name or "").strip(), flags=re.UNICODE)
    cleaned = re.sub(r"\s+", "_", cleaned).strip("._-")
    if not cleaned:
        return "custom_preset"
    return cleaned[:64]


class UserPresetManager:
    def __init__(self, presets_dir):
        self.presets_dir = presets_dir

    def ensure_dir(self):
        os.makedirs(self.presets_dir, exist_ok=True)

    def _preset_path(self, name):
        return os.path.join(self.presets_dir, f"{sanitize_preset_filename(name)}.json")

    def list_presets(self):
        """Return list of (preset_name, preset_dict) sorted by name."""
        if not os.path.isdir(self.presets_dir):
            return []
        presets = []
        for filename in sorted(os.listdir(self.presets_dir)):
            if not filename.endswith(".json"):
                continue
            path = os.path.join(self.presets_dir, filename)
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                if not isinstance(payload, dict):
                    continue
                name = str(payload.get("name") or os.path.splitext(filename)[0]).strip()
                settings = payload.get("settings")
                if not name or not isinstance(settings, dict):
                    continue
                presets.append((name, settings))
            except (OSError, ValueError):
                continue
        presets.sort(key=lambda item: item[0].lower())
        return presets

    def load_preset(self, name):
        for preset_name, settings in self.list_presets():
            if preset_name == name:
                return dict(settings)
        path = self._preset_path(name)
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                if isinstance(payload, dict) and isinstance(payload.get("settings"), dict):
                    return dict(payload["settings"])
            except (OSError, ValueError):
                return None
        return None

    def save_preset(self, name, settings):
        cleaned_name = (name or "").strip()
        if not cleaned_name:
            raise ValueError("Preset name cannot be empty")
        self.ensure_dir()
        filtered = {
            key: settings[key]
            for key in PRESET_KEYS
            if key in settings
        }
        payload = {
            "name": cleaned_name,
            "settings": filtered,
        }
        path = self._preset_path(cleaned_name)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
        return path

    def delete_preset(self, name):
        if not os.path.isdir(self.presets_dir):
            return False
        removed = False
        for filename in os.listdir(self.presets_dir):
            if not filename.endswith(".json"):
                continue
            path = os.path.join(self.presets_dir, filename)
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                if isinstance(payload, dict) and str(payload.get("name", "")).strip() == name:
                    os.remove(path)
                    removed = True
            except (OSError, ValueError):
                continue
        if not removed:
            fallback_path = self._preset_path(name)
            if os.path.isfile(fallback_path):
                try:
                    os.remove(fallback_path)
                    removed = True
                except OSError:
                    pass
        return removed
