#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
divine.py — single-file app

Menu:
[1] Divine (generate)
[2] Show token base (777 words, seed 333)
[3] Settings (seed / token count / draws)
[0] Quit

Behavior:
- Tokens are read from ONE file: ../divine_build/lexicon.txt
  (this lexicon was built with seed=333).
- Default token base size used here: 777 (first 777 lines from the lexicon).
- Each run samples N=draws words with replacement.
- Words at positions 7, 14, 21, ... are highlighted in red and form the final sentence.
- Default draw-seed uses local date+time (America/Fortaleza) so every run differs.
"""

from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import random
import sys
import time

# ---------- Paths / Defaults ----------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEXICON_PATH = PROJECT_ROOT / "divine_build" / "lexicon.txt"

DEFAULT_TOKEN_COUNT = 777     # size of token base used from the lexicon
DEFAULT_DRAWS = 33            # number of words sampled each run
DEFAULT_SEED_MODE = "time"    # "time" or "fixed"
DEFAULT_FIXED_SEED = 333      # only used if seed mode = fixed

WORD_DELAY_SEC = 0.12         # slow paragraph printing (per word)
SLOW_MSG_DELAY = 0.15         # intro slow print (per char)

# ANSI colors
RED = "\033[31m"
RESET = "\033[0m"

# ---------- Utils ----------
def slow_print(msg: str, delay: float) -> None:
    for ch in msg:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")

def load_tokens(path: Path, k: int) -> list[str]:
    if not path.exists():
        print(f"[error] lexicon file not found: {path}", file=sys.stderr)
        sys.exit(2)
    out: list[str] = []
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            w = line.strip()
            if w:
                out.append(w)
            if len(out) >= k:
                break
    if len(out) < k:
        print(f"[error] lexicon has only {len(out)} tokens; need {k}", file=sys.stderr)
        sys.exit(3)
    return out

def selection_positions(draws: int, step: int = 7) -> list[int]:
    # 1-based positions: 7, 14, 21, ... <= draws
    return list(range(step, draws + 1, step))

def current_time_seed() -> int:
    now = datetime.now(ZoneInfo("America/Fortaleza"))
    return int(now.strftime("%Y%m%d%H%M%S"))

# ---------- Core run ----------
def run_once(token_count: int, draws: int, seed_mode: str, fixed_seed: int) -> None:
    base = load_tokens(LEXICON_PATH, token_count)
    # choose seed
    seed = current_time_seed() if seed_mode == "time" else int(fixed_seed)
    rng = random.Random(seed)

    # sample indices 1..N with replacement
    N = len(base)
    indices = [rng.randint(1, N) for _ in range(draws)]

    # positions to highlight / collect (7,14,21,...)
    sel_pos = selection_positions(draws)
    chosen_idx = [indices[p - 1] for p in sel_pos]
    chosen_words = [base[i - 1] for i in chosen_idx]

    # print paragraph slowly, words separated by single spaces
    sys.stdout.write("\n")
    for i, idx1 in enumerate(indices, start=1):
        w = base[idx1 - 1]
        if i in sel_pos:
            sys.stdout.write(f"{RED}{w}{RESET}")
        else:
            sys.stdout.write(w)
        if i < draws:
            sys.stdout.write(" ")
        sys.stdout.flush()
        time.sleep(WORD_DELAY_SEC)
    sys.stdout.write("\n\n")

    # final sentence from selected words
    sentence = " ".join(chosen_words)
    if sentence:
        sentence = sentence[0].upper() + sentence[1:] + "."
    sys.stdout.write(sentence + "\n")

# ---------- Views ----------
def show_tokens(token_count: int) -> None:
    base = load_tokens(LEXICON_PATH, token_count)
    print("\n=== TOKEN BASE ===")
    for i, w in enumerate(base, start=1):
        print(f"{i:3d}: {w}")
    print(f"\n[info] Tokens extracted from Authorized King James Version, using seed = 333.")
    print(f"[info] Total tokens in this base: {len(base)}")
    print(f"[info] This generator uses the local date-time as the default draw seed.\n")

def settings_menu(ctx: dict) -> None:
    while True:
        print("\n=== SETTINGS ===")
        print(f"Current token count: {ctx['token_count']}")
        print(f"Current draws:       {ctx['draws']}")
        print(f"Seed mode:           {ctx['seed_mode']} (fixed={ctx['fixed_seed']})")
        print("[1] Change token count")
        print("[2] Change draws")
        print("[3] Toggle seed mode (time/fixed)")
        print("[4] Set fixed seed value")
        print("[0] Back")
        op = input("> ").strip()
        if op == "1":
            v = input("New token count (>= 7): ").strip()
            try:
                n = int(v)
                if n >= 7:
                    ctx["token_count"] = n
                else:
                    print("[warn] must be >= 7")
            except:
                print("[warn] invalid integer")
        elif op == "2":
            v = input("New draws (>= 7): ").strip()
            try:
                n = int(v)
                if n >= 7:
                    ctx["draws"] = n
                else:
                    print("[warn] must be >= 7")
            except:
                print("[warn] invalid integer")
        elif op == "3":
            ctx["seed_mode"] = "fixed" if ctx["seed_mode"] == "time" else "time"
        elif op == "4":
            v = input("Fixed seed (integer): ").strip()
            try:
                ctx["fixed_seed"] = int(v)
            except:
                print("[warn] invalid integer")
        elif op == "0":
            return
        else:
            print("[!] Wrong option")

# ---------- Main Menu ----------
def menu():
    ctx = {
        "token_count": DEFAULT_TOKEN_COUNT,
        "draws": DEFAULT_DRAWS,
        "seed_mode": DEFAULT_SEED_MODE,
        "fixed_seed": DEFAULT_FIXED_SEED,
    }
    while True:
        print("")
        print("[1] Divine")
        print("[2] Text Used")
        print("[3] Settings")
        print("[0] Quit")
        op = input("> ").strip()
        if op == "1":
            run_once(ctx["token_count"], ctx["draws"], ctx["seed_mode"], ctx["fixed_seed"])
        elif op == "2":
            show_tokens(ctx["token_count"])
        elif op == "3":
            settings_menu(ctx)
        elif op == "0":
            return
        else:
            print("[!] Wrong option")

# ---------- Entry ----------
if __name__ == "__main__":
    intro = "Holy, holy, holy, is the Lord God Almighty, who was and is and is to come!"
    print("")
    slow_print(intro, delay=SLOW_MSG_DELAY)
    menu()

