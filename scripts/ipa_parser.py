"""Alternative entry point for running ``ipa-parser`` without the console script.

See ``src/ipa/cli.py`` for supported arguments.
"""

from ipa.cli import main


if __name__ == "__main__":
    main()
