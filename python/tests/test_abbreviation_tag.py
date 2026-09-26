import unittest

from jazzy_fish.encoder import EncoderException, WordEncoder, Wordlist, _wordlist_tag

SHIPPED = ("012_8562fb9", "024_84f184f", "01234_f233650")


class TestAbbreviationTag(unittest.TestCase):
    def _encoder(self, name: str, **kwargs: object) -> WordEncoder:
        wordlist = Wordlist.load(f"resources/{name}", "jazzy_fish")
        return WordEncoder(wordlist, 4, **kwargs)  # type: ignore[arg-type]

    def test_shipped_wordlists_have_distinct_tags(self):
        tags = {_wordlist_tag(name) for name in SHIPPED}
        self.assertEqual(len(tags), len(SHIPPED))

    def test_tag_is_derived_from_the_whole_name(self):
        # 012_8562fb9 and 024_84f184f share a leading checksum character, so a tag
        # sliced from the checksum alone would collide and protect nothing.
        self.assertNotEqual(_wordlist_tag("012_8562fb9"), _wordlist_tag("024_84f184f"))

    def test_tag_is_stable(self):
        self.assertEqual(_wordlist_tag("012_8562fb9"), _wordlist_tag("012_8562fb9"))

    def test_abbreviation_round_trips_with_its_tag(self):
        encoder = self._encoder("012_8562fb9")
        for value in (0, 1, 1234567, encoder.get_max() - 1):
            encoded = encoder.encode(value)
            self.assertEqual(encoder.decode_abbr(encoded.abbr), value)

    def test_keyphrase_is_unaffected(self):
        tagged = self._encoder("012_8562fb9")
        plain = self._encoder("012_8562fb9", tag_abbreviations=False)
        for value in (0, 1234567, tagged.get_max() - 1):
            self.assertEqual(
                tagged.encode(value).keyphrase, plain.encode(value).keyphrase
            )

    def test_foreign_abbreviation_is_rejected(self):
        source = self._encoder("012_8562fb9")
        other = self._encoder("024_84f184f")
        rejected = 0
        for value in range(0, 2000):
            try:
                other.decode_abbr(source.encode(value).abbr)
            except EncoderException:
                rejected += 1
        self.assertEqual(rejected, 2000)

    def test_untagged_mode_still_works(self):
        encoder = self._encoder("012_8562fb9", tag_abbreviations=False)
        encoded = encoder.encode(1234567)
        self.assertFalse(encoded.abbr.endswith(encoder._wordlist.tag))
        self.assertEqual(encoder.decode_abbr(encoded.abbr), 1234567)

    def test_wordlist_name_is_exposed(self):
        self.assertEqual(self._encoder("012_8562fb9").wordlist_name, "012_8562fb9")


if __name__ == "__main__":
    unittest.main()
