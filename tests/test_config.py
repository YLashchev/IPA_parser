import tempfile

from ipa.config import (
    load_language_config,
    remove_custom_char,
    save_language_config,
)


def test_remove_custom_char_removes_existing_sequence():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as tmp:
        tmp.write("geminate = true\n\n")
        tmp.write("[[custom_chars]]\n")
        tmp.write('sequence = "ts"\n')
        tmp.write('category = "CONSONANT"\n')
        tmp.write("rank = 1\n\n")
        tmp.write("[[custom_chars]]\n")
        tmp.write('sequence = "OP"\n')
        tmp.write('category = "PAUSE"\n')
        tmp.write("rank = 0\n")
        tmp.flush()

        geminate, custom_chars = remove_custom_char(tmp.name, "ts")

        assert geminate is True
        assert len(custom_chars) == 1
        assert custom_chars[0] == ("OP", "PAUSE", 0)

        geminate_verify, custom_chars_verify = load_language_config(tmp.name)
        assert geminate_verify is True
        assert len(custom_chars_verify) == 1
        assert custom_chars_verify[0] == ("OP", "PAUSE", 0)


def test_remove_custom_char_raises_valueerror_when_not_found():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as tmp:
        tmp.write("geminate = true\n\n")
        tmp.write("[[custom_chars]]\n")
        tmp.write('sequence = "ts"\n')
        tmp.write('category = "CONSONANT"\n')
        tmp.write("rank = 1\n")
        tmp.flush()

        try:
            remove_custom_char(tmp.name, "dz")
            assert False, "Expected ValueError"
        except ValueError as exc:
            assert "not found" in str(exc).lower()


def test_remove_custom_char_round_trip():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as tmp:
        config_path = tmp.name
        save_language_config(
            config_path, True, [("ts", "CONSONANT", 1), ("dz", "CONSONANT", 1), ("OP", "PAUSE", 0)]
        )

        geminate, custom_chars = remove_custom_char(config_path, "dz")

        assert geminate is True
        assert len(custom_chars) == 2
        assert ("ts", "CONSONANT", 1) in custom_chars
        assert ("OP", "PAUSE", 0) in custom_chars
        assert ("dz", "CONSONANT", 1) not in custom_chars

        geminate_reload, custom_chars_reload = load_language_config(config_path)
        assert geminate_reload is True
        assert len(custom_chars_reload) == 2
        assert ("ts", "CONSONANT", 1) in custom_chars_reload
        assert ("OP", "PAUSE", 0) in custom_chars_reload


def test_remove_custom_char_leaves_geminate_unchanged():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as tmp:
        config_path = tmp.name
        save_language_config(config_path, False, [("ts", "CONSONANT", 1)])

        geminate, custom_chars = remove_custom_char(config_path, "ts")

        assert geminate is False
        assert len(custom_chars) == 0

        geminate_reload, custom_chars_reload = load_language_config(config_path)
        assert geminate_reload is False
        assert len(custom_chars_reload) == 0
