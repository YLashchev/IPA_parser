"""Command-line interface entry point for ipa-parser.

Provides the ``ipa-parser`` console script with interactive and batch modes.
See ``README.md`` for full usage examples and flags.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import pandas as pd

from .config import load_language_config
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
    """Build and parse the command-line argument specification.

    Defines all supported arguments for the ``ipa-parser`` command and
    delegates parsing to ``argparse``. The function reads from ``sys.argv``
    by default.

    Arguments defined:

    - ``input`` (positional, optional): Path to the input Excel (``.xlsx``) file.
      When omitted, the user is prompted to select from available files in
      ``data/unprocessed/``.
    - ``--config``: Optional path to a TOML language configuration file.
      When omitted, the user is prompted to select from available configs in
      ``data/language_settings/``, or falls back to ``geminate=True`` and
      ``DEFAULT_CUSTOM_CHARS`` if no configs exist.
    - ``--geminate`` / ``--no-geminate``: Boolean flag that overrides the
      ``geminate`` setting from the config file when supplied explicitly.
    - ``--run``: When present, the pipeline executes immediately without
      entering the interactive menu. Requires an explicit ``input`` file path.
    - ``--output-csv``: Override path for CSV output. When omitted, the
      path is auto-generated as ``data/processed/YYYY-MM-DD_<stem>_auto.csv``.
    - ``--output-xlsx``: Override path for XLSX output. When omitted, the
      path is auto-generated as ``data/processed/YYYY-MM-DD_<stem>_auto.xlsx``.
    - ``--format``: Output format selection. One of ``csv``, ``xlsx``, or
      ``both`` (default). Controls which file(s) are written on export.

    Returns:
        An ``argparse.Namespace`` object whose attributes correspond to the
        argument names listed above (``input``, ``config``, ``geminate``,
        ``run``, ``output_csv``, ``output_xlsx``, ``format``).
    """
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
    """Display numbered list of files matching pattern, prompt for selection.

    Args:
        directory: Path to search (e.g., "data/unprocessed")
        extension: File extension without dot (e.g., "xlsx")
        label: Human-readable description (e.g., "input spreadsheet")

    Returns:
        Selected file path as string, or None if empty/cancelled
    """
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
    """Entry point for the ``ipa-parser`` console script.

    Orchestrates the full startup sequence:

    1. Parses command-line arguments via ``parse_args``.
    2. If ``input`` is not provided, prompts the user to select an Excel file
       from ``data/unprocessed/``. If ``--config`` is not provided, prompts for
       a TOML config from ``data/language_settings/``.
    3. Prints the ASCII art banner to standard output.
    4. Loads the input Excel file into a ``DataFrame`` via ``load_excel``.
    5. Resolves configuration: if ``--config`` is supplied, reads ``geminate``
       and custom characters from the TOML file; otherwise falls back to
       ``geminate=True`` and ``DEFAULT_CUSTOM_CHARS``. A ``--geminate`` /
       ``--no-geminate`` flag on the command line always takes precedence over
       the config file value.
    6. Registers custom characters with ``CustomCharacter`` via
       ``configure_custom_characters``.
    7. Branches on execution mode:

       - **Interactive** (``--run`` not set): delegates to ``run_interactive``
         and returns when the user quits.
       - **Batch** (``--run`` set): calls ``build_final_dataframe``, prints any
         word-alignment mismatches and the resulting ``DataFrame``, then writes
         to auto-generated paths in ``data/processed/`` (or custom paths if
         ``--output-csv`` / ``--output-xlsx`` are supplied).

    Returns:
        None
    """
    args = parse_args()

    if args.run and args.input is None:
        print("Error: --run requires explicit input file path", file=sys.stderr)
        sys.exit(1)

    if args.input is None:
        args.input = _select_file("data/unprocessed", "xlsx", "input spreadsheet")
        if args.input is None:
            print("No input file selected. Exiting.")
            sys.exit(0)

    if args.config is None:
        args.config = _select_file("data/language_settings", "toml", "language config")

    # Auto-generate output filenames from input: YYYY-MM-DD_<stem>_auto.{csv,xlsx}
    input_stem = Path(args.input).stem
    today = date.today().strftime("%Y-%m-%d")
    output_base = f"data/processed/{today}_{input_stem}_auto"
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
    """Write the DataFrame to disk in the requested format(s).

    Args:
        df: The final DataFrame to export.
        output_csv: Destination path for CSV output.
        output_xlsx: Destination path for XLSX output.
        output_format: One of ``'csv'``, ``'xlsx'``, or ``'both'``.

    Returns:
        A list of file paths that were written.

    Raises:
        ValueError: If ``output_format`` is not ``'csv'``, ``'xlsx'``, or
            ``'both'``.
    """
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
