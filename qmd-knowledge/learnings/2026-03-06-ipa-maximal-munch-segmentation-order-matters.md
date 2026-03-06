# Learning: IPA maximal munch segmentation order matters

**Date:** 2026-03-06 01:52:49

## Context

The IPAString class segments IPA transcription strings into individual
characters using a maximal munch algorithm. When adding new CustomCharacter
entries (e.g., language-specific digraphs like prenasalized stops), the order
in which symbols are checked against the input string determines whether
longer multi-character sequences are recognized correctly.

## Learning

Maximal munch means the parser always tries to match the longest possible
symbol first. If the symbol table is checked in an order where shorter
symbols come first, a digraph like "mb" could be incorrectly split into
"m" + "b" instead of being recognized as a single prenasalized stop.

The IPA symbol table in `ipa_symbols.json` and any CustomCharacter entries
must be sorted by descending length so that longer symbols are attempted
before shorter ones. The segmentation algorithm in `src/ipa/ipa_string.py`
relies on this ordering.

## Application

When adding new CustomCharacter entries for a language config:

1. Ensure multi-character symbols (digraphs, trigraphs) are listed before
   their component single characters.
2. Test segmentation with strings that contain both the digraph and its
   component characters to verify correct splitting.
3. Do not reorder `ipa_symbols.json` entries without understanding the
   impact on maximal munch behavior.

---

*Recorded by qmd-knowledge skill*
