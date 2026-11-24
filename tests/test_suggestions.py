import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from vboard.suggestions import HunspellSuggestionEngine


class HunspellSuggestionEngineTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.home = Path(self.temp_dir.name)
        self.dictionary_dir = self.home / ".local" / "share" / "hunspell"
        self.dictionary_dir.mkdir(parents=True)
        (self.dictionary_dir / "uk_UA.dic").write_text(
            "4\nпривіт\nпривітний/A\nприв'язка\nУкраїна\n",
            encoding="utf-8",
        )
        (self.dictionary_dir / "pl_PL.dic").write_text(
            "3\ndziękuję\nżółć\nPolska\n",
            encoding="utf-8",
        )
        (self.dictionary_dir / "ru_RU.dic").write_text(
            "4\nпривет\nприветствие/A\nёлка\nкто-то\n",
            encoding="utf-8",
        )
        (self.dictionary_dir / "de_DE.dic").write_text(
            "2\nStraße\nStraßenbahn\n",
            encoding="utf-8",
        )
        (self.dictionary_dir / "en_US.dic").write_text(
            "3\nhello\nhelp\nworld\n",
            encoding="utf-8",
        )
        self.home_patch = mock.patch.dict(os.environ, {"HOME": str(self.home)})
        self.home_patch.start()
        self.addCleanup(self.home_patch.stop)

    def test_ukrainian_unicode_suggestions(self):
        engine = HunspellSuggestionEngine("uk")

        self.assertEqual(engine.normalize_word("ПРИВʼЯЗКА"), "прив'язка")
        self.assertEqual(
            engine.get_suggestions("прив", 5),
            ["привіт", "прив'язка", "привітний"],
        )
        self.assertEqual(engine.dictionary_path, str(self.dictionary_dir / "uk_UA.dic"))

    def test_polish_diacritic_suggestions(self):
        engine = HunspellSuggestionEngine("pl")

        self.assertEqual(engine.get_suggestions("dzięk", 5), ["dziękuję"])
        self.assertEqual(engine.get_suggestions("żó", 5), ["żółć"])

    def test_russian_unicode_suggestions(self):
        engine = HunspellSuggestionEngine("ru")

        self.assertEqual(
            engine.get_suggestions("прив", 5),
            ["привет", "приветствие"],
        )
        self.assertEqual(engine.get_suggestions("ёл", 5), ["ёлка"])
        self.assertEqual(engine.get_suggestions("кто-", 5), ["кто-то"])
        self.assertEqual(engine.dictionary_path, str(self.dictionary_dir / "ru_RU.dic"))

    def test_german_eszett_is_preserved(self):
        engine = HunspellSuggestionEngine("de")

        self.assertEqual(engine.normalize_word("Straße"), "straße")
        self.assertEqual(engine.get_suggestions("straß", 5), ["straße", "straßenbahn"])

    def test_layout_switch_reloads_matching_dictionary(self):
        engine = HunspellSuggestionEngine("uk")
        engine.ensure_loaded()

        engine.set_layout("en")

        self.assertFalse(engine.loaded)
        self.assertEqual(engine.get_suggestions("hel", 5), ["help", "hello"])
        self.assertEqual(engine.dictionary_path, str(self.dictionary_dir / "en_US.dic"))

    def test_non_word_characters_are_rejected(self):
        engine = HunspellSuggestionEngine("uk")

        self.assertIsNone(engine.normalize_word("слово123"))
        self.assertIsNone(engine.normalize_word("--"))

    def test_non_utf8_hunspell_dictionaries_from_aff_charset(self):
        (self.dictionary_dir / "pl_PL.aff").write_text(
            "SET ISO8859-2\n", encoding="ascii"
        )
        (self.dictionary_dir / "pl_PL.dic").write_bytes(
            "2\nżółć/A\nżółty/B\n".encode("iso-8859-2")
        )
        pl_engine = HunspellSuggestionEngine("pl")
        self.assertEqual(pl_engine.get_suggestions("żół", 5), ["żółć", "żółty"])

        (self.dictionary_dir / "ru_RU.aff").write_text(
            "SET KOI8-R\n", encoding="ascii"
        )
        (self.dictionary_dir / "ru_RU.dic").write_bytes(
            "2\nпривет/A\nпример/B\n".encode("koi8-r")
        )
        ru_engine = HunspellSuggestionEngine("ru")
        self.assertEqual(ru_engine.get_suggestions("при", 5), ["привет", "пример"])

    def test_spell_check_typo_and_diacritic_corrections(self):
        en_engine = HunspellSuggestionEngine("en")
        self.assertIn("hello", en_engine.get_suggestions("helo", 5))
        self.assertIn("world", en_engine.get_suggestions("wrold", 5))

        pl_engine = HunspellSuggestionEngine("pl")
        self.assertIn("dziękuję", pl_engine.get_suggestions("dziek", 5))
        self.assertIn("żółć", pl_engine.get_suggestions("zolc", 5))

    def test_bundled_fallback_dictionaries_for_all_five_languages(self):
        for lang, query, expected in (
            ("en", "keyb", "keyboard"),
            ("pl", "dziek", "dziękuję"),
            ("uk", "прив", "привіт"),
            ("ru", "прив", "привет"),
            ("ar", "مرح", "مرحبا"),
        ):
            engine = HunspellSuggestionEngine(lang)
            with mock.patch.object(engine, "find_dictionary_path", return_value=None):
                suggestions = engine.get_suggestions(query, 5)
            self.assertIsNotNone(engine.dictionary_path)
            self.assertTrue(engine.dictionary_path.endswith(f"{lang}.txt"))
            self.assertIn(expected, suggestions)


if __name__ == "__main__":
    unittest.main()
