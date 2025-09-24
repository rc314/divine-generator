```
# Divine Generator

This project has two parts:

1. **build_lexicon.py**  
   A deterministic script that constructs a clean lexicon (one token per line) from input `.txt` files.  
   Features:
   - Accent stripping and lowercase normalization
   - Optional hyphen retention
   - True de-duplication (no artificial variants)
   - Deterministic shuffling with configurable seed
   - Target size option with padding by real duplicates
   - Support for extra token lists

2. **divine.py**  
   A single-file app that consumes the generated `lexicon.txt` and produces randomized “divinations”:  
   - Loads the first 777 tokens by default  
   - Samples 33 words each run (configurable)  
   - Highlights every 7th word in red and composes them into a final sentence  
   - Uses current datetime (America/Fortaleza) as default RNG seed for variation  

---

## How to build the lexicon

Run `build_lexicon.py` with your text sources and an output file:

```

python build\_lexicon.py ./texts ./divine\_build/lexicon.txt

```

Optional arguments:
- `--target N` : force lexicon to have exactly N tokens  
- `--extras FILE` : add extra tokens (one per line)  
- `--keep-hyphens` : allow hyphens in tokens  
- `--min-len N` / `--max-len N` : control token length  
- `--seed N` : deterministic shuffle seed (default 333)  
- `--allow-duplicates` : pad with real duplicates if target cannot be reached  
- `--verbose` : detailed logs  

---

## How to run the generator

After building the lexicon, run:

```

python divine.py

```

You will see a menu with options to generate a divination, inspect the token base, and change settings (token count, draws, seed mode).

---

## Example

```

Holy, holy, holy, is the Lord God Almighty, who was and is and is to come!

\[1] Divine
\[2] Text Used
\[3] Settings
\[0] Quit

```

Selecting **1** prints a paragraph of sampled words, with every 7th word highlighted, and then a final sentence built from those highlights.

---

## Requirements

- Python 3.10+
- Standard library only (no external packages)

---
```
