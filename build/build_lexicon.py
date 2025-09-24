#!/usr/bin/env python3
# build_lexicon.py
# Deterministically builds a clean word lexicon from one or more input texts.

"""
Purpose
-------
Create a newline-delimited lexicon (one token per line) from .txt sources with:
- Accent stripping (Unicode NFKD) and lowercase normalization
- Optional hyphen retention (letters only otherwise)
- True de-duplication (no artificial variants)
- Deterministic shuffling via --seed (default 333)
- Optional completion to a target size (--target) with *real* duplicates only
- Optional “extras” list to supplement tokens

High-level flow
---------------
1) Discover inputs:
   - Any file paths are read directly.
   - Any directories are recursively scanned for *.txt.

2) Tokenization:
   - Broad split on non [\w'-] boundaries to over-capture candidates.
   - Normalization:
     a) Strip accents (NFKD, drop combining marks)
     b) Keep only letters (A–Z, a–z) and optional hyphen (-)
     c) Lowercase
     d) Enforce length bounds [--min-len, --max-len]
     e) Discard tokens with no alphabetic characters

3) De-duplication while preserving first-seen order.

4) Optional extras:
   - Read one term per line from --extras, normalize with same rules,
     merge into the unique set.

5) Shuffle:
   - Deterministic shuffle with --seed (default 333).

6) Target sizing:
   - If --target is set:
     - If we have >= target unique tokens, truncate to target.
     - Else:
       - If --allow-duplicates is given, pad by reusing real tokens,
         then reshuffle to avoid clustering duplicates.
       - Otherwise, fail with a clear error.

7) Output:
   - Write the final list to --output (parents created if needed).

CLI examples
------------
# Minimal: build lexicon from a folder of .txt into lexicon.txt
python build_lexicon.py ./corpus ./divine_build/lexicon.txt

# Fixed size of 5000, deterministic seed 42, allow real duplicates if needed
python build_lexicon.py ./corpus ./divine_build/lexicon.txt --target 5000 --seed 42 --allow-duplicates

# Add extras (one term per line), keep hyphens, verbose logs
python build_lexicon.py ./corpus ./divine_build/lexicon.txt --extras extras.txt --keep-hyphens -v
"""

import argparse
import pathlib
import random
import re
import sys
import unicodedata
from collections import OrderedDict

# ---------------------
# Utilities
# ---------------------

def _strip_accents(s: str) -> str:
    """Remove diacritics: NFKD normalize + drop combining marks."""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))

def _keep_char(ch: str, keep_hyphens: bool) -> bool:
    """Allow letters; optionally allow hyphen."""
    if ch.isalpha():
        return True
    if keep_hyphens and ch == "-":
        return True
    return False

def normalize_token(tok: str, keep_hyphens: bool) -> str:
    """Normalize a raw token:
       1) strip accents, 2) keep letters (+ hyphen if allowed), 3) lowercase."""
    s = _strip_accents(tok)
    s = "".join(ch for ch in s if _keep_char(ch, keep_hyphens))
    return s.lower()

# Broad split; \w includes digits/underscore which are filtered later by normalize_token.
WORD_SPLIT_RE = re.compile(r"[^\w'-]+", re.UNICODE)

def tokenize_text(text: str) -> list[str]:
    """Split text into raw token candidates before normalization."""
    return [t for t in WORD_SPLIT_RE.split(text) if t]

def iter_input_files(inputs: list[str]) -> list[pathlib.Path]:
    """Collect .txt files from given paths; recurse into directories."""
    files = []
    for p in inputs:
        path = pathlib.Path(p)
        if path.is_dir():
            files.extend(sorted(f for f in path.rglob("*.txt")))
        elif path.is_file():
            files.append(path)
        else:
            print(f"[warn] ignoring non-existent path: {p}", file=sys.stderr)
    return files

def load_extras(path: str | None, keep_hyphens: bool, min_len: int, max_len: int) -> list[str]:
    """Load extra tokens (one per line), apply same normalization and filters."""
    if not path:
        return []
    out = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            t = line.strip()
            if not t:
                continue
            t = normalize_token(t, keep_hyphens)
            if not t:
                continue
            if not any(c.isalpha() for c in t):
                continue
            if not (min_len <= len(t) <= max_len):
                continue
            out.append(t)
    return out

# ---------------------
# Core
# ---------------------

def build_lexicon(
    inputs: list[str],
    extras_path: str | None,
    output_path: str,
    target: int | None,
    keep_hyphens: bool,
    min_len: int,
    max_len: int,
    seed: int,
    allow_duplicates: bool,
    verbose: bool,
):
    files = iter_input_files(inputs)
    if not files:
        print("[error] no input files found.", file=sys.stderr)
        sys.exit(2)

    if verbose:
        print(f"[info] input files: {len(files)}")

    # Ordered dictionary to preserve first occurrence order
    seen = OrderedDict()

    # Read inputs
    for fp in files:
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                txt = f.read()
        except Exception as e:
            print(f"[warn] failed to read {fp}: {e}", file=sys.stderr)
            continue

        for raw in tokenize_text(txt):
            norm = normalize_token(raw, keep_hyphens)
            if not norm:
                continue
            # discard tokens without letters (e.g., numbers-only)
            if not any(c.isalpha() for c in norm):
                continue
            if not (min_len <= len(norm) <= max_len):
                continue
            seen.setdefault(norm, None)

    base_words = list(seen.keys())

    if verbose:
        print(f"[info] unique tokens from inputs: {len(base_words)}")

    # Optional extras (trusted terms, one per line)
    if extras_path:
        extras = load_extras(extras_path, keep_hyphens, min_len, max_len)
        if verbose:
            print(f"[info] extras loaded: {len(extras)}")
        for w in extras:
            if w not in seen:
                seen[w] = None
        base_words = list(seen.keys())
        if verbose:
            print(f"[info] total after extras (unique): {len(base_words)}")

    # Deterministic shuffle
    rng = random.Random(seed)
    rng.shuffle(base_words)

    # Target policy
    if target is not None:
        if len(base_words) >= target:
            lex = base_words[:target]
            if verbose:
                print(f"[info] reached target with unique tokens: {len(lex)}")
        else:
            deficit = target - len(base_words)
            if not allow_duplicates:
                print(
                    f"[error] insufficient unique tokens for --target {target}: "
                    f"only {len(base_words)} available. No artificial variants. "
                    f"Use --allow-duplicates or provide --extras.",
                    file=sys.stderr,
                )
                sys.exit(3)
            # Complete with real duplicates (no made-up tokens)
            if verbose:
                print(f"[info] missing {deficit}; completing with real duplicates")
            padding = [base_words[i % len(base_words)] for i in range(deficit)]
            rng.shuffle(padding)
            lex = base_words + padding
            # Final shuffle to avoid duplicate clustering
            rng.shuffle(lex)
    else:
        lex = base_words

    # Write output
    outp = pathlib.Path(output_path)
    outp.parent.mkdir(parents=True, exist_ok=True)
    with open(outp, "w", encoding="utf-8") as f:
        for w in lex:
            f.write(w + "\n")

    if verbose:
        print(f"[ok] written: {outp} ({len(lex)} lines)")

# ---------------------
# CLI
# ---------------------

def main():
    ap = argparse.ArgumentParser(
        description="Build a clean, deterministic lexicon from text files (no artificial variants)."
    )
    ap.add_argument("inputs", nargs="+", help="Input .txt files and/or directories (recursive)")
    ap.add_argument("output", help="Output file path (e.g., divine_build/lexicon.txt)")
    ap.add_argument("--target", type=int, help="Desired lexicon size (truncate or pad as needed)")
    ap.add_argument("--extras", help="Optional extras file (one term per line) to supplement")
    ap.add_argument("--keep-hyphens", action="store_true", help="Allow hyphens in tokens")
    ap.add_argument("--min-len", type=int, default=2, help="Minimum token length")
    ap.add_argument("--max-len", type=int, default=32, help="Maximum token length")
    ap.add_argument("--seed", type=int, default=333, help="Shuffle seed (default: 333)")
    ap.add_argument(
        "--allow-duplicates",
        action="store_true",
        help="Allow real duplicates to reach --target (no invented tokens)"
    )
    ap.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = ap.parse_args()

    build_lexicon(
        inputs=args.inputs,
        extras_path=args.extras,
        output_path=args.output,
        target=args.target,
        keep_hyphens=args.keep_hyphens,
        min_len=args.min_len,
        max_len=args.max_len,
        seed=args.seed,
        allow_duplicates=args.allow_duplicates,
        verbose=args.verbose,
    )

if __name__ == "__main__":
    main()

