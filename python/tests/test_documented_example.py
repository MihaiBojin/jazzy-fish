import textwrap
import unittest

import jazzy_fish


class TestDocumentedExample(unittest.TestCase):
    def test_package_docstring_example_runs(self):
        """
        The package docstring is what help(jazzy_fish) prints and the first code a
        new user meets. It used to call encoded.key_phrase, a field that does not
        exist, so copying it raised AttributeError.
        """

        docstring = jazzy_fish.__doc__ or ""
        self.assertIn("Usage:", docstring)

        body = docstring.split("Usage:\n", 1)[1]
        source = textwrap.dedent(body)
        source = "\n".join(
            line
            for line in source.splitlines()
            if not line.strip().startswith("Import the package")
        )

        exec(compile(source, "<jazzy_fish docstring>", "exec"), {})


if __name__ == "__main__":
    unittest.main()
