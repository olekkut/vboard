import bisect
import os
import unicodedata

from .constants import SUGGESTION_LIMIT, SUPPORTED_WORD_CONNECTORS


BUNDLED_DICTIONARY_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "dictionaries"
)

LAYOUT_DICTIONARIES = {
    "ar": ("ar", "ar_SA", "ar_EG"),
    "de": ("de_DE", "de"),
    "en": ("en_US", "en_GB", "en"),
    "fr": ("fr_FR", "fr"),
    "pl": ("pl_PL", "pl"),
    "ru": ("ru_RU", "ru"),
    "sv": ("sv_SE", "sv"),
    "uk": ("uk_UA", "uk"),
}

XKB_DICTIONARY_ALIASES = {
    "us": "en",
    "gb": "en",
    "ua": "uk",
    "se": "sv",
}

_EXTRA_FOLD_MAP = str.maketrans(
    {
        "ł": "l",
        "đ": "d",
        "ø": "o",
        "æ": "ae",
        "œ": "oe",
        "ß": "ss",
        "ё": "е",
        "ї": "и",
        "і": "и",
        "є": "е",
        "ґ": "г",
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ة": "ه",
        "ى": "ي",
    }
)


def fold_diacritics(text):
    if not text:
        return ""
    # Preserve Cyrillic й/ё distinction carefully only when folded for loose search
    decomposed = unicodedata.normalize("NFKD", text.lower().translate(_EXTRA_FOLD_MAP))
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def damerau_levenshtein_bounded(first, second, max_distance):
    len_a = len(first)
    len_b = len(second)
    if abs(len_a - len_b) > max_distance:
        return max_distance + 1
    if first == second:
        return 0
    if not first:
        return len_b
    if not second:
        return len_a

    prev_prev = None
    prev = list(range(len_b + 1))
    for i in range(1, len_a + 1):
        curr = [i] + [max_distance + 1] * len_b
        row_min = i
        j_start = max(1, i - max_distance)
        j_end = min(len_b, i + max_distance)
        a_char = first[i - 1]
        for j in range(j_start, j_end + 1):
            cost = 0 if a_char == second[j - 1] else 1
            best = min(
                prev[j] + 1,
                curr[j - 1] + 1,
                prev[j - 1] + cost,
            )
            if (
                prev_prev is not None
                and i > 1
                and j > 1
                and a_char == second[j - 2]
                and first[i - 2] == second[j - 1]
            ):
                transposition = prev_prev[j - 2] + 1
                if transposition < best:
                    best = transposition
            curr[j] = best
            if best < row_min:
                row_min = best
        if row_min > max_distance:
            return max_distance + 1
        prev_prev = prev
        prev = curr
    return prev[len_b]


class HunspellSuggestionEngine:
    def __init__(self, layout_id="en"):
        self.layout_id = layout_id
        self.words = []
        self._word_set = set()
        self._common_words = set()
        self._folded_entries = []
        self._folded_keys = []
        self._by_first_and_len = {}
        self._by_last_and_len = {}
        self.dictionary_path = None
        self.loaded = False

    def set_layout(self, layout_id):
        if layout_id == self.layout_id:
            return

        self.layout_id = layout_id
        self.words = []
        self._word_set = set()
        self._common_words = set()
        self._folded_entries = []
        self._folded_keys = []
        self._by_first_and_len = {}
        self._by_last_and_len = {}
        self.dictionary_path = None
        self.loaded = False

    def _load_common_words(self):
        common = set()
        bundled_path = self.find_bundled_dictionary_path()
        if bundled_path is None:
            return common
        try:
            with open(bundled_path, "r", encoding="utf-8", errors="ignore") as handle:
                for line in handle:
                    word = self.parse_dictionary_line(line)
                    if word is not None:
                        common.add(word)
        except OSError:
            pass
        return common

    def _rebuild_indexes(self, words_iterable):
        self.words = sorted(words_iterable)
        self._word_set = set(self.words)
        self._common_words = self._load_common_words() & self._word_set
        folded_pairs = []
        by_first_and_len = {}
        by_last_and_len = {}
        for word in self.words:
            folded = fold_diacritics(word)
            folded_pairs.append((folded, word))
            wlen = len(word)
            if folded:
                by_first_and_len.setdefault((folded[0], wlen), []).append(word)
                by_last_and_len.setdefault((folded[-1], wlen), []).append(word)
        folded_pairs.sort(key=lambda pair: (pair[0], len(pair[1]), pair[1]))
        self._folded_entries = folded_pairs
        self._folded_keys = [pair[0] for pair in folded_pairs]
        self._by_first_and_len = by_first_and_len
        self._by_last_and_len = by_last_and_len

    @staticmethod
    def detect_dictionary_encoding(dic_path):
        aff_path = os.path.splitext(dic_path)[0] + ".aff"
        if not os.path.isfile(aff_path):
            return "utf-8"

        aliases = {
            "UTF-8": "utf-8",
            "UTF8": "utf-8",
            "ISO8859-1": "iso-8859-1",
            "ISO8859-2": "iso-8859-2",
            "ISO8859-5": "iso-8859-5",
            "ISO8859-6": "iso-8859-6",
            "ISO8859-15": "iso-8859-15",
            "KOI8-R": "koi8-r",
            "KOI8-U": "koi8-u",
            "MICROSOFT-CP1251": "cp1251",
            "CP1251": "cp1251",
            "WINDOWS-1251": "cp1251",
            "MICROSOFT-CP1252": "cp1252",
            "CP1252": "cp1252",
            "MICROSOFT-CP1256": "cp1256",
            "CP1256": "cp1256",
            "WINDOWS-1256": "cp1256",
        }
        try:
            with open(aff_path, "r", encoding="ascii", errors="ignore") as aff_handle:
                for line in aff_handle:
                    stripped = line.strip()
                    if stripped.startswith("SET "):
                        raw_charset = stripped.split(None, 1)[1].strip().upper()
                        encoding = aliases.get(raw_charset, raw_charset.lower())
                        try:
                            "".encode(encoding)
                            return encoding
                        except LookupError:
                            return "utf-8"
        except OSError:
            pass
        return "utf-8"

    def ensure_loaded(self):
        if self.loaded:
            return

        self.loaded = True
        self.dictionary_path = self.find_dictionary_path()
        if self.dictionary_path is None:
            self.dictionary_path = self.find_bundled_dictionary_path()
        if self.dictionary_path is None:
            return

        encoding = (
            "utf-8"
            if self.dictionary_path.endswith(".txt")
            else self.detect_dictionary_encoding(self.dictionary_path)
        )
        words = set()
        try:
            with open(self.dictionary_path, "r", encoding=encoding, errors="ignore") as handle:
                for index, line in enumerate(handle):
                    if index == 0 and line.strip().isdigit():
                        continue

                    word = self.parse_dictionary_line(line)
                    if word is not None:
                        words.add(word)
        except OSError as exc:
            print(f"Warning: Could not read dictionary ({exc}). Suggestions disabled.")
            self.dictionary_path = None
            return

        self._rebuild_indexes(words)

    def _collect_spell_corrections(self, prefix, limit, exclude, common_only=False):
        if len(prefix) < 3 or limit <= 0:
            return []

        max_dist = 1 if (common_only or len(prefix) <= 5) else 2
        folded_prefix = fold_diacritics(prefix)
        if not folded_prefix:
            return []

        seen = set(exclude)
        seen.add(prefix)
        target_len = len(prefix)
        min_len = max(2, target_len - max_dist)
        max_len = target_len + max_dist

        if common_only:
            bucket_words = [
                word
                for word in self._common_words
                if min_len <= len(word) <= max_len
            ]
        else:
            bucket_words = []
            for length in range(min_len, max_len + 1):
                bucket_words.extend(
                    self._by_first_and_len.get((folded_prefix[0], length), ())
                )
                if len(folded_prefix) >= 3:
                    bucket_words.extend(
                        self._by_last_and_len.get((folded_prefix[-1], length), ())
                    )

        max_scan = 2500
        scanned = 0
        scored = []
        for word in bucket_words:
            if word in seen:
                continue
            seen.add(word)
            scanned += 1
            if scanned > max_scan:
                break

            folded_word = fold_diacritics(word)
            dist = damerau_levenshtein_bounded(prefix, word, max_dist)
            if dist > max_dist and folded_word != word:
                folded_dist = damerau_levenshtein_bounded(
                    folded_prefix, folded_word, max_dist
                )
                if folded_dist <= max_dist:
                    dist = folded_dist + 0.25
            if dist <= max_dist:
                same_first = 0 if folded_word[:1] == folded_prefix[:1] else 1
                is_rare = 0 if word in self._common_words else 1
                scored.append(
                    (is_rare, dist, same_first, abs(len(word) - target_len), word)
                )

        scored.sort(key=lambda item: (item[0], item[1], item[2], item[3], item[4]))
        return [item[4] for item in scored[:limit]]

    def get_suggestions(self, prefix, limit=SUGGESTION_LIMIT):
        prefix = self.normalize_word(prefix)
        if not prefix:
            return []

        self.ensure_loaded()
        if not self.words:
            return []

        start_index = bisect.bisect_left(self.words, prefix)
        matches = []
        for word in self.words[start_index:]:
            if not word.startswith(prefix):
                break
            if word == prefix:
                continue
            matches.append(word)
            if len(matches) >= 80:
                break

        matches.sort(
            key=lambda word: (
                0 if word in self._common_words else 1,
                len(word),
                word,
            )
        )

        # If typed word is misspelled (not in dictionary) and has no common prefix matches
        # (e.g. "helo" matching only obscure "helot"/"heloise"), surface common distance-1 fixes first!
        has_common_prefix = any(word in self._common_words for word in matches)
        results = []
        seen = set()
        if (
            len(prefix) >= 4
            and prefix not in self._word_set
            and not has_common_prefix
            and self._common_words
        ):
            for correction in self._collect_spell_corrections(
                prefix, min(3, limit), seen, common_only=True
            ):
                results.append(correction)
                seen.add(correction)

        for word in matches:
            if len(results) >= limit:
                break
            if word not in seen:
                results.append(word)
                seen.add(word)

        # Diacritic-insensitive prefix completions (e.g. "dziek" -> "dziękuję", "zolc" -> "żółć")
        if len(results) < limit:
            folded_prefix = fold_diacritics(prefix)
            if folded_prefix:
                f_start = bisect.bisect_left(self._folded_keys, folded_prefix)
                folded_matches = []
                for idx in range(f_start, len(self._folded_entries)):
                    f_key, orig_word = self._folded_entries[idx]
                    if not f_key.startswith(folded_prefix):
                        break
                    if orig_word == prefix or orig_word in seen:
                        continue
                    folded_matches.append(orig_word)
                    if len(folded_matches) >= 40:
                        break
                folded_matches.sort(
                    key=lambda w: (0 if w in self._common_words else 1, len(w), w)
                )
                for word in folded_matches:
                    if len(results) >= limit:
                        break
                    results.append(word)
                    seen.add(word)

        # Full dictionary spell-check fallback when no prefix matches were found at all
        if len(results) < limit and prefix not in self._word_set and not matches:
            corrections = self._collect_spell_corrections(
                prefix, limit - len(results), seen, common_only=False
            )
            results.extend(corrections)

        return results[:limit]

    def _resolved_base_lang(self):
        lookup_id = self.layout_id or "en"
        if lookup_id.startswith("xkb:"):
            xkb_lang = lookup_id.split(":", 2)[1]
            lookup_id = XKB_DICTIONARY_ALIASES.get(xkb_lang, xkb_lang)
        return XKB_DICTIONARY_ALIASES.get(lookup_id, lookup_id)

    def find_bundled_dictionary_path(self):
        if not os.path.isdir(BUNDLED_DICTIONARY_DIR):
            return None
        base_lang = self._resolved_base_lang()
        candidate_names = [base_lang]
        if "_" in base_lang:
            candidate_names.append(base_lang.split("_", 1)[0])
        if "-" in base_lang:
            candidate_names.append(base_lang.split("-", 1)[0])
        for name in candidate_names:
            path = os.path.join(BUNDLED_DICTIONARY_DIR, f"{name}.txt")
            if os.path.isfile(path):
                return path
        return None

    def find_dictionary_path(self):
        candidates = self.get_dictionary_candidates()
        search_dirs = [
            os.path.expanduser("~/.local/share/hunspell"),
            os.path.expanduser("~/.hunspell"),
            "/usr/share/hunspell",
            "/usr/share/myspell",
            "/usr/share/myspell/dicts",
        ]

        for directory in search_dirs:
            if not os.path.isdir(directory):
                continue

            for candidate in candidates:
                path = os.path.join(directory, f"{candidate}.dic")
                if os.path.isfile(path):
                    return path

        return None

    def get_dictionary_candidates(self):
        lookup_id = self._resolved_base_lang()

        if lookup_id in LAYOUT_DICTIONARIES:
            return list(LAYOUT_DICTIONARIES[lookup_id])

        candidates = []
        if lookup_id and lookup_id.isalpha() and len(lookup_id) == 2:
            candidates.extend([f"{lookup_id}_{lookup_id.upper()}", lookup_id])

        for value in (
            os.environ.get("LC_ALL", ""),
            os.environ.get("LC_MESSAGES", ""),
            os.environ.get("LC_CTYPE", ""),
            os.environ.get("LANG", ""),
            os.environ.get("LANGUAGE", ""),
        ):
            for locale_name in value.split(":"):
                locale_name = locale_name.strip()
                if not locale_name:
                    continue

                locale_name = locale_name.split(".", 1)[0]
                locale_name = locale_name.split("@", 1)[0]
                if not locale_name:
                    continue

                candidates.append(locale_name)
                if "_" in locale_name:
                    candidates.append(locale_name.split("_", 1)[0])

        ordered = []
        seen = set()
        for candidate in candidates:
            if candidate not in seen:
                ordered.append(candidate)
                seen.add(candidate)
        return ordered

    def parse_dictionary_line(self, line):
        token = line.strip()
        if not token:
            return None

        token = token.split(maxsplit=1)[0]
        if not token:
            return None

        word_chars = []
        escaped = False
        for char in token:
            if escaped:
                word_chars.append(char)
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == "/":
                break
            word_chars.append(char)

        return self.normalize_word("".join(word_chars))

    def normalize_word(self, word):
        if not word:
            return None

        normalized = word.strip().lower().replace("\u2019", "'").replace("\u02bc", "'")
        if len(normalized) < 2:
            return None
        if any(
            not char.isalpha() and char not in SUPPORTED_WORD_CONNECTORS
            for char in normalized
        ):
            return None
        if not any(char.isalpha() for char in normalized):
            return None
        return normalized
