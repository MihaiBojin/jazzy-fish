"""
Jazzy Fish Tools
================

This package contains code that can process dictionaries and generate all combinations of wordlists, abbreviations of a given length,
and character positions chosen for the abbreviation. These can help users infer the best choice depending on their use-case.

Modules:
    clean_dictionary - Given a dictionary as an input directory, clean every list of word parts by removing invalid, non ASCII, non alpha words,
                       and inappropriate words (as defined by the `ignored.txt` list).
    generate_wordlists - Generates combinations of word parts of varied prefix lengths to help the user choose the best configuration
                         for their use-case.
    helpers - Various helper functions and jazzy_fish_tools settings, which can be tuned (if needed).

"""
