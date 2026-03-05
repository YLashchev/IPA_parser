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


def test_toml_tiebar_sequence_roundtrip():
    """Verify tie-bar sequence (U+0361) survives TOML save/load round-trip."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as tmp:
        config_path = tmp.name
        # Save config with upper tie-bar (U+0361)
        save_language_config(config_path, True, [("t\u0361s", "AFFRICATE", 1)])

        # Reload and verify byte-for-byte match
        geminate, custom_chars = load_language_config(config_path)
        assert geminate is True
        assert len(custom_chars) == 1
        assert custom_chars[0] == ("t\u0361s", "AFFRICATE", 1)
        assert custom_chars[0][0] == "t\u0361s"  # Exact sequence with U+0361


def test_toml_tiebar_with_lower_tiebar_roundtrip():
    """Verify lower tie-bar sequence (U+035C) survives TOML save/load round-trip."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as tmp:
        config_path = tmp.name
        # Save config with lower tie-bar (U+035C)
        save_language_config(config_path, True, [("t\u035cs", "AFFRICATE", 1)])

        # Reload and verify byte-for-byte match
        geminate, custom_chars = load_language_config(config_path)
        assert geminate is True
        assert len(custom_chars) == 1
        assert custom_chars[0] == ("t\u035cs", "AFFRICATE", 1)
        assert custom_chars[0][0] == "t\u035cs"  # Exact sequence with U+035C


def test_toml_multiple_tiebar_entries():
    """Verify multiple tie-bar entries survive save/load round-trip."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as tmp:
        config_path = tmp.name
        entries = [
            ("t\u0361s", "AFFRICATE", 1),
            ("d\u0361z", "AFFRICATE", 1),
            ("t\u0361\u0283", "AFFRICATE", 1),
            ("a\u0361\u026a", "DIPHTHONG", 1),
        ]
        save_language_config(config_path, False, entries)

        # Reload and verify all entries present with exact sequences
        geminate, custom_chars = load_language_config(config_path)
        assert geminate is False
        assert len(custom_chars) == 4
        for expected in entries:
            assert expected in custom_chars


def test_toml_tiebar_escaped_correctly():
    """Verify TOML file contains tie-bar character as-is (not escaped/mojibake)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as tmp:
        config_path = tmp.name
        tiebar_sequence = "t\u0361s"
        save_language_config(config_path, True, [(tiebar_sequence, "AFFRICATE", 1)])

        # Read the raw TOML file and verify tie-bar is present
        with open(config_path, "r", encoding="utf-8") as f:
            toml_content = f.read()

        # Verify the tie-bar character (U+0361) is in the file
        assert "\u0361" in toml_content, "Tie-bar character U+0361 not found in TOML file"
        # Verify the sequence is present in the file
        assert tiebar_sequence in toml_content, "Tie-bar sequence not found in TOML file"


def test_append_tiebar_custom_char():
    """Verify append_custom_char() adds tie-bar entries and survives reload."""
    from ipa.config import append_custom_char

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as tmp:
        config_path = tmp.name
        # Start with an existing entry
        save_language_config(config_path, True, [("ts", "CONSONANT", 1)])

        # Append a tie-bar entry
        tiebar_sequence = "d\u0361z"
        geminate, custom_chars = append_custom_char(config_path, tiebar_sequence, "AFFRICATE", 1)

        # Verify return value
        assert geminate is True
        assert len(custom_chars) == 2
        assert (tiebar_sequence, "AFFRICATE", 1) in custom_chars

        # Verify reload persists the tie-bar entry
        geminate_reload, custom_chars_reload = load_language_config(config_path)
        assert geminate_reload is True
        assert len(custom_chars_reload) == 2
        assert (tiebar_sequence, "AFFRICATE", 1) in custom_chars_reload
