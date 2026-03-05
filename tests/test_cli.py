import sys

import pandas as pd

from ipa import cli


def test_warns_without_config(monkeypatch, capsys):
    dummy_df = pd.DataFrame({"Phoneme": []})

    monkeypatch.setattr(cli, "load_excel", lambda _path: dummy_df)
    monkeypatch.setattr(cli, "configure_custom_characters", lambda _chars: None)
    monkeypatch.setattr(cli, "_select_file", lambda *args: None)

    def fake_build_final_dataframe(_df, geminate=True, fill_na=True):
        return dummy_df, []

    monkeypatch.setattr(cli, "build_final_dataframe", fake_build_final_dataframe)
    monkeypatch.setattr(cli, "_export", lambda *_args, **_kwargs: ["dummy.csv"])
    monkeypatch.setattr(sys, "argv", ["ipa-parser", "fake.xlsx", "--run", "--format", "csv"])

    cli.main()

    captured = capsys.readouterr()
    assert "Warning: No --config specified" in captured.err


def test_format_xlsx(monkeypatch):
    dummy_df = pd.DataFrame({"Phoneme": []})

    monkeypatch.setattr(cli, "load_excel", lambda _path: dummy_df)
    monkeypatch.setattr(cli, "configure_custom_characters", lambda _chars: None)
    monkeypatch.setattr(cli, "_select_file", lambda *args: None)

    def fake_build_final_dataframe(_df, geminate=True, fill_na=True):
        return dummy_df, []

    export_calls = []

    def fake_export(_df, output_csv, output_xlsx, output_format):
        export_calls.append((output_csv, output_xlsx, output_format))
        return [output_xlsx]

    monkeypatch.setattr(cli, "build_final_dataframe", fake_build_final_dataframe)
    monkeypatch.setattr(cli, "_export", fake_export)
    monkeypatch.setattr(sys, "argv", ["ipa-parser", "fake.xlsx", "--run", "--format", "xlsx"])

    cli.main()

    assert export_calls
    _, output_xlsx, output_format = export_calls[0]
    assert output_format == "xlsx"
    assert output_xlsx.endswith("_auto.xlsx")


def test_select_file_finds_toml_configs():
    from pathlib import Path

    files = sorted(Path("data/language_settings").glob("*.toml"))
    assert len(files) == 4, f"Expected 4 TOML files, found {len(files)}"


def test_batch_mode_without_input_fails():
    import subprocess

    result = subprocess.run([".venv/bin/ipa-parser", "--run"], capture_output=True, text=True)
    assert result.returncode != 0, "Should exit with error code"
    assert "Error" in result.stderr or "error" in result.stderr
