# Jazzy Fish - Sufficiently-large, unique, human-friendly identifiers

![Build Status](https://github.com/jazzy-fish/jazzy-fish/actions/workflows/python-tests.yml/badge.svg)
[![PyPI version](https://badge.fury.io/py/jazzy-fish.svg)](https://badge.fury.io/py/jazzy-fish)
[![Python Versions](https://img.shields.io/pypi/pyversions/jazzy-fish.svg)](https://pypi.org/project/jazzy-fish/)
[![License](https://img.shields.io/github/license/jazzy-fish/jazzy-fish.svg)](LICENSE)

> ⚠️ **Warning:** This library is **in development** and not yet ready for production. Its API is not yet stable
> and might (and probably _will_) still change. Follow repository [issues](https://github.com/jazzy-fish/jazzy-fish/issues) for more information.

Jazzy Fish is a library that helps you generate a sufficient number of identifiers, with a human-friendly kick.

This is not a new idea and similar implementation can be found in various places
(i.e., GitHub new repository name [suggestions](https://github.com/new)).

Jazzy Fish is able to map a large integer solution space to unique keyphrases that can be used as human-friendly identifiers.
Each keyphrase also has a fixed-length (character-based) abbreviated form that can be used as a short-form identifier.

The implementation roughly works as follows:

- configure a `Generator` (details below)
- call `generator.next_id()`, which returns a unique, ever-increasing integer value
- call `Encoder.encode(id)`, which returns a `keyphrase`
- decode a _Keyphrase_ into its integer from by calling `Encoder.decode(keyphrase)`

## Terminology

- `word part`: parts of speech used in the English language that can be used to form sentences/phrases: adverbs, verbs, adjectives, and nouns
- `dictionary`: a list of English words categorized by _word part_, which is used to generate _wordlists_
- `wordlist`: a list of *word part*s that can be combined to generate a large number of *key phrase*s
- `keyphrase`: a uniquely ordered sequence of words, each of a certain _word part_, which can be mapped to a unique integer identifier
  (e.g., `niftier engine`)
- `(keyphrase) abbreviations`: a fixed-length (ASCII character) representation of the keyphrase, which can be used
  as a non-numerical identifier (e.g., `nif-eng`)
- `identifier`: a numerical (integer) value that can be used to represent unique entities (e.g., `12040320103821`)

## Quickstart

The project is published to <https://pypi.org/project/jazzy-fish/>.
Install it via:

```shell
pip install jazzy-fish

# or alternatively, directly from git
pip install "git+https://github.com/jazzy-fish/jazzy-fish@main#subdirectory=python"
```

The implementation roughly works as follows:

- configure a `Generator` (details below)
- call `generator.next_id()`, which returns a unique, ever-increasing integer value
- call `Encoder.encode(id)`, which returns a `keyphrase`
- decode a _Keyphrase_ into its integer from by calling `Encoder.decode(keyphrase)`

## Configuring a Generator

Integer IDs are constructed by combining 3 parts:

- a `timestamp`: can be relative to the UNIX epoch, or a custom epoch - to maximize the possible solution size;
  the timestamp can be chosen between seconds and milliseconds, in increments of 1/10ms (1s, 1/10s, 1/100s, 1ms)
- a `machine id`: since it may be necessary to run multiple generators (i.e., in distributed systems), the solution domain can be partitioned by multiple 'machines'
- a `sequence id`: representing a number of identifiers that can be generated, all things being equal (e.g., same time, same machine)

Thus, the algorithm is configurable enough to split a solution domain (e.g., N potential word combinations, where N is a large integer) into smaller partitions, that can be reasoned about in terms of: `For how many years can IDs/word sequences be generated before the implementation needs to be changed?`

The idea behind this implementation is also inspired from Bitcoin's Improvement Proposal [39](https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki).

Note: The BIP39 implementation uses a single word list to convert 12 or 24 unique words out of a total of 2048 words into a very large integer that can be used to derive secret keys.

Jazzy Fish different from BIP39 in that it uses multiple word lists (specifically, adverbs, verbs, adjectives, and nouns) to generate word sequences that are similar to natural (English) language, with the assumption that sequences such as `yellow cat`, `hectic fish`, `dreadful elephant` (while somewhat nonsensical) are easy to memorize by humans used to combining word parts. So, the aim of this library is to choose sufficiently-large word lists that can generate sufficiently-large unique word sequences, for a reasonable duration (i.e., several years or more).

Another relevant detail of this algorithm, is its ability to map chosen word sequences to smaller prefixes that can be used to form constant-length identifiers.
While each sequence maps to an integer, remembering integers is hard for most humans. Thus, based on this implementation's assumption that humans can remember structured sentences, it selects the input wordlists in such a way that, for a given and pre-configured prefix length, there exists a single word that corresponds to that prefix.

For example, given a prefix length of size=1, `yellow cat` can be encoded to `yc` and then decoded back to the same two words. In this example, `yellow` is an adjective, and `cat` is a noun. There do not exist any other adjectives that start with `y`, nor nouns that start with `c` in our input word lists.

The reference implementation of the algorithm comes with a default wordlist of prefix 3, containing adverbs, verbs, adjectives, and nouns.

It can map the following solution domains:

- 2,178,560 unique combinations of `adjective noun`
- 2,740,628,480 unique combinations of `verb adjective noun`
- 1,205,876,531,200 unique combinations of `adverb verb adjective noun`

Two-word sequences may be impractical for sustained identifier generation, however, three word and four word sequences can sustain 87 and 38,238 years respectively at a rate of 1 identifier generated per second, using a single machine.

If the default wordlists are unsuitable, they can be changed. Consult the [Generate wordlists](#generate-wordlists) section for details.

## Contents

This directory contains the following resources:

- [src/jazzy_fish](./src/jazzy_fish): Python code that generates unique identifiers and can encode/decode them to keyphrases;
  this is the main package a client implementation needs to generate jazzy-fish keyphrases.
- [src/jazzy_fish_tools](./src/jazzy_fish_tools): Utility that works with wordlists, cleaning up input words (removing invalid or inappropriate words) and generating various combinations that allow a user to create new input wordlists with different capabilities.

## Jazzy Fish Tools

The library also provides tooling that can generate all combinations of wordlists, abbreviations of a given length,
and character positions chosen for the abbreviation.

```shell
generate-wordlists $PATH_TO_REPO/dictionary/5
```

These can help users infer the best choice depending on their use-case.

You may replace the wordlist, with a directory of your choosing, as long as it contains the same file structure - four files named after the relevant four parts in the English language:

- adverb.txt
- adjective.txt
- verb.txt
- noun.txt

After running this command, you can examine all outputs in the `out/processed` directory and you can see a high-level comparison by running `scripts/show-stats.bash`.

## Developers

Unless you are interested in contributing to this code (or are curious about this library's development processes), you can stop reading here.

### Publishing

#### GitHub-based version publishing

The simplest way to publish a new version (if you have committer rights) is to tag a commit and push it to the repo:

```shell
# At a certain commit, ideally after merging a PR to main
git tag v0.1.x
git push origin v0.1.x
```

A [GitHub Action](https://github.com/jazzy-fish/jazzy-fish/actions) will run, build the library and publish it to the PyPI repositories.

#### Manual

These steps can also be performed locally. For these commands to work, you will need to export two environment variables:

```shell
export TESTPYPI_PASSWORD=... # token for https://test.pypi.org/legacy/
export PYPI_PASSWORD=... # token for https://upload.pypi.org/legacy/
```

The `Makefile` passes these to `uv publish` as `UV_PUBLISH_TOKEN`; the test index is defined as
`testpypi` under `[[tool.uv.index]]` in `pyproject.toml`.

First, publish to the test repo and inspect the package:

```shell
make publish-test
```

If correct, distribute the wheel to the PyPI index:

```shell
make publish
```

Verify the distributed code

```shell
make publish-verify
```

### Generate wordlists

The [jazzy_fish_tools](src/jazzy_fish_tools) package contains code that can process dictionaries and generate all combinations of wordlists, abbreviations of a given length, and character positions chosen for the abbreviation. These can help users infer the best choice depending on their use-case.

First, install CLI dependencies:

```shell
pip install jazzy-fish[cli]
```

Then, call [generate-wordlists PATH_TO_DICTIONARY_DIR](python/src/jazzy_fish_tools/generate_wordlists.py) to generate all possible combinations.
The resulting wordlists will be stored in `out/processed`.

If you want to generate wordlists using a dictionary of your choosing, use the [clean-dictionary PATH_TO_DICTIONARY_DIR](python/src/jazzy_fish_tools/clean_dictionary.py)
script to sanitize the inputs (in-place). Consult one of the included dictionaries ([dictionary/](dictionary/)) to determine the required file structure.
