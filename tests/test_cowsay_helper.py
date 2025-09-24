from pcopy import cowsay_helper


def test_cowsay_art_fallback():
    art = cowsay_helper.cowsay_art('hello', cow='nonexistent')
    assert isinstance(art, str)
    assert 'hello' in art
