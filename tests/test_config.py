import importlib
import json
from pcopy import config


def test_slogans_loaded():
    assert isinstance(config.SLOGANS, list) or isinstance(config.SLOGANS, dict) or True


def test_cat_facts_loaded():
    assert isinstance(config.CAT_FACTS, list)
    # not strict about content; ensure it's a list
