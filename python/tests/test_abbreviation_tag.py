import unittest

from jazzy_fish import EncoderException, WordEncoder, Wordlist


SHIPPED = ("012_80a1774", "024_e4d0f5e", "01234_011cf27")


class TestAbbreviationTag(unittest.TestCase):
    def encoder(
        self, name: str = SHIPPED[0], min_phrase_size: int | None = None
    ) -> WordEncoder:
        return WordEncoder(
            Wordlist.load(f"resources/{name}", "jazzy_fish"), min_phrase_size
        )

    def test_encode_returns_all_three_forms(self):
        encoded = self.encoder().encode(1234567)
        self.assertEqual(encoded.keyphrase, "abjectly-abashed-moodier-gopher")
        self.assertEqual(encoded.abbr, "abj-aba-moo-gop")
        self.assertTrue(hasattr(encoded, "verified_abbr"))
        self.assertEqual(len(encoded.verified_abbr), len(encoded.abbr) + 2)
        self.assertTrue(encoded.verified_abbr.startswith(encoded.abbr))

    def test_decode_accepts_plain_abbreviation(self):
        self.assertEqual(self.encoder().decode("abj-aba-moo-gop"), 1234567)

    def test_all_forms_round_trip_for_each_wordlist_and_phrase_size(self):
        for name in SHIPPED:
            for size in range(1, 5):
                encoder = self.encoder(name, min_phrase_size=size)
                for value in (0, 1, 1702, 1234567, encoder.get_max() - 1):
                    with self.subTest(name=name, size=size, value=value):
                        encoded = encoder.encode(value)
                        for form in (
                            encoded.keyphrase,
                            encoded.abbr,
                            encoded.verified_abbr,
                        ):
                            self.assertEqual(encoder.decode(form), value)
                        for form in (encoded.abbr, encoded.verified_abbr):
                            self.assertEqual(encoder.decode_abbr(form), value)

    def test_foreign_tag_is_rejected(self):
        for source_name in SHIPPED:
            source = self.encoder(source_name)
            for target_name in SHIPPED:
                if source_name == target_name:
                    continue
                target = self.encoder(target_name)
                for decode in (target.decode, target.decode_abbr):
                    with self.subTest(source=source_name, target=target_name):
                        with self.assertRaises(EncoderException):
                            decode(source.encode(1234567).verified_abbr)

    def test_altered_tag_is_rejected(self):
        encoder = self.encoder()
        encoded = encoder.encode(1234567)
        for suffix in (
            "!!",
            "00",
            encoded.verified_abbr[-1],
            encoded.verified_abbr[-2:] + "x",
        ):
            for decode in (encoder.decode, encoder.decode_abbr):
                with self.subTest(suffix=suffix, decode=decode.__name__):
                    with self.assertRaises(EncoderException):
                        decode(encoded.abbr + suffix)

    def test_foreign_tag_is_rejected_even_when_the_payload_is_valid(self):
        encoder = self.encoder()
        payload = encoder.encode(1234567).abbr
        foreign_tag = self.encoder(SHIPPED[1]).encode(0).verified_abbr[-2:]
        for decode in (encoder.decode, encoder.decode_abbr):
            with self.assertRaisesRegex(EncoderException, "wordlist tag"):
                decode(payload + foreign_tag)

    def test_plain_abbreviation_ending_in_the_tag_is_not_stripped(self):
        wordlist = Wordlist(SHIPPED[0], [["amjword"]], verify_checksum=False)
        encoder = WordEncoder(wordlist)
        encoded = encoder.encode(0)
        self.assertEqual(encoded.abbr, "amj")
        for form in (encoded.abbr, encoded.verified_abbr):
            self.assertEqual(encoder.decode(form), 0)
            self.assertEqual(encoder.decode_abbr(form), 0)

    def test_keyphrases_do_not_verify_the_wordlist(self):
        source = self.encoder()
        other = self.encoder(SHIPPED[1])
        self.assertEqual(source.encode(2).keyphrase, "abjectly-abashed-abased-abbess")
        self.assertEqual(other.decode(source.encode(2).keyphrase), 4)

    def test_valid_tag_does_not_allow_unknown_parts_or_wrong_phrase_size(self):
        encoder = self.encoder()
        encoded = encoder.encode(1234567)
        tag = encoded.verified_abbr[-2:]
        for abbr in (
            "zzz-aba-moo-gop",
            "aba-moo-gop",
            "abj-abj-aba-moo-gop",
            "",
            "abj--moo-gop",
        ):
            for decode in (encoder.decode, encoder.decode_abbr):
                with self.subTest(abbr=abbr, decode=decode.__name__):
                    with self.assertRaises(EncoderException):
                        decode(abbr + tag)

    def test_custom_separators_including_tag_characters(self):
        wordlist = Wordlist(
            SHIPPED[0],
            [["absurdly"], ["abandoned"], ["able"], ["apple", "cat"]],
            verify_checksum=False,
        )
        for separator in ("_", " ", "m", "j"):
            encoder = WordEncoder(wordlist, separator=separator)
            encoded = encoder.encode(1)
            for form in (encoded.keyphrase, encoded.abbr, encoded.verified_abbr):
                with self.subTest(separator=separator, form=form):
                    self.assertEqual(encoder.decode(form), 1)
            self.assertEqual(encoder.decode_abbr(encoded.verified_abbr), 1)

    def test_shipped_tags_are_stable_and_distinct(self):
        for name, tag in zip(SHIPPED, ("mj", "1t", "gn")):
            self.assertTrue(self.encoder(name).encode(0).verified_abbr.endswith(tag))

    def test_one_character_prefix_with_separator_in_tag(self):
        wordlist = Wordlist(
            "0_NOVERIFY", [["apple", "bird"], ["cat", "dog"]], verify_checksum=False
        )
        for size in (1, 2):
            encoder = WordEncoder(wordlist, min_phrase_size=size, separator="9")
            for value in range(encoder.get_max()):
                encoded = encoder.encode(value)
                for form in (encoded.abbr, encoded.verified_abbr):
                    with self.subTest(size=size, value=value, form=form):
                        self.assertEqual(encoder.decode(form), value)
                        self.assertEqual(encoder.decode_abbr(form), value)

    def test_wordlist_name_is_exposed(self):
        for name in SHIPPED:
            self.assertEqual(self.encoder(name).wordlist_name, name)
