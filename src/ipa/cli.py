"""CLI entry point for ipa-parser."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import pandas as pd

from .config import load_language_config

# Resolve data paths relative to repo root, not CWD
_REPO_ROOT = Path(__file__).resolve().parents[2]
from .interactive import run_interactive
from .pipeline import build_final_dataframe, configure_custom_characters, load_excel


DEFAULT_CUSTOM_CHARS = [
    ("OP", "PAUSE", 0),
    ("SP", "PAUSE", 0),
]

BANNER = "\n".join(
    [
        " ________  _________   ",
        "|\\   __  \\|\\___   ___\\ ",
        "\\ \\  \\|\\  \\|___ \\  \\_| ",
        " \\ \\   _  _\\   \\ \\  \\  ",
        "  \\ \\  \\\\  \\|   \\ \\  \\ ",
        "   \\ \\__\\\\ _\\    \\ \\__\\",
        "    \\|__|\\|__|    \\|__|",
    ]
)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run IPA parsing pipeline")
    parser.add_argument(
        "input",
        nargs="?",
        default=None,
        help="Path to input Excel file (optional - will prompt if omitted)",
    )
    parser.add_argument("--config", help="Path to TOML language config")
    parser.add_argument(
        "--geminate",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Override geminate handling",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run pipeline directly (skip interactive menu)",
    )
    parser.add_argument("--output-csv", default=None, help="Override CSV output path")
    parser.add_argument("--output-xlsx", default=None, help="Override XLSX output path")
    parser.add_argument(
        "--format",
        default="both",
        choices=["csv", "xlsx", "both"],
        help="Output format: csv, xlsx, or both (default: both)",
    )
    return parser.parse_args()


def _select_file(directory: str, extension: str, label: str) -> str | None:
    """Prompt user to pick a file from a directory listing."""
    files = sorted(Path(directory).glob(f"*.{extension}"))

    if not files:
        print(f"No .{extension} files found in {directory}/")
        return None

    print(f"\nAvailable {label} files:")
    for idx, f in enumerate(files, start=1):
        print(f"  {idx}) {f.name}")

    while True:
        try:
            choice = input(f"\nSelect {label} (number, or 'q' to quit): ").strip()
            if choice.lower() == "q":
                return None
            idx = int(choice)
            if 1 <= idx <= len(files):
                return str(files[idx - 1])
            print(f"Please enter a number between 1 and {len(files)}")
        except (ValueError, KeyboardInterrupt):
            print("\nCancelled.")
            return None


def main() -> None:
    """Run the ipa-parser CLI (interactive or batch)."""
    args = parse_args()

    if args.run and args.input is None:
        print("Error: --run requires explicit input file path", file=sys.stderr)
        sys.exit(1)

    if args.input is None:
        args.input = _select_file(str(_REPO_ROOT / "data" / "unprocessed"), "xlsx", "input spreadsheet")
        if args.input is None:
            print("No input file selected. Exiting.")
            sys.exit(0)

    if args.config is None:
        args.config = _select_file(str(_REPO_ROOT / "data" / "language_settings"), "toml", "language config")

    # Auto-generate output filenames from input: YYYY-MM-DD_<stem>_auto.{csv,xlsx}
    input_stem = Path(args.input).stem
    today = date.today().strftime("%Y-%m-%d")
    output_base = str(_REPO_ROOT / "data" / "processed" / f"{today}_{input_stem}_auto")
    output_csv = args.output_csv or f"{output_base}.csv"
    output_xlsx = args.output_xlsx or f"{output_base}.xlsx"

    print(BANNER)
    df = load_excel(args.input)

    if args.config:
        config_geminate, custom_chars = load_language_config(args.config)
        geminate = config_geminate
    else:
        geminate = True
        custom_chars = DEFAULT_CUSTOM_CHARS
        print(
            "Warning: No --config specified. Multi-character sequences "
            "(affricates, diphthongs, language-specific clusters) will not "
            "be recognized and the pipeline may fail.",
            file=sys.stderr,
        )

    if args.geminate is not None:
        geminate = args.geminate

    configure_custom_characters(custom_chars)

    output_format = args.format

    if not args.run:
        run_interactive(
            df,
            geminate=geminate,
            config_path=args.config,
            output_csv=output_csv,
            output_xlsx=output_xlsx,
            output_format=output_format,
        )
        return

    final_df, mismatches = build_final_dataframe(df, geminate=geminate, fill_na=True)

    if mismatches:
        print(mismatches)

    print(final_df)

    exported = _export(final_df, output_csv, output_xlsx, output_format)
    print(f"\nExported {', '.join(exported)}")


def _export(
    df: pd.DataFrame,
    output_csv: str,
    output_xlsx: str,
    output_format: str,
) -> list[str]:
    """Write DataFrame to CSV/XLSX and return paths written."""
    if output_format not in ("csv", "xlsx", "both"):
        raise ValueError(f"Invalid output_format: {output_format}")

    exported: list[str] = []
    if output_format in ("csv", "both"):
        Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_csv, index=False)
        exported.append(output_csv)
    if output_format in ("xlsx", "both"):
        Path(output_xlsx).parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(output_xlsx, index=False)
        exported.append(output_xlsx)
    return exported
