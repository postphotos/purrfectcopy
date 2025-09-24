from pcopy.runner import main


def test_main_help():
    # calling main with --help should exit with SystemExit
    try:
        main(['--help'])
    except SystemExit:
        pass
