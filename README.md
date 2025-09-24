
# Divine Generator

This project contains two main scripts:

## 1. build_lexicon.py
A deterministic script that constructs a clean lexicon (one token per line) from input `.txt` files.

### Features
- Accent stripping and lowercase normalization  
- Optional hyphen retention  
- True de-duplication (no artificial variants)  
- Deterministic shuffling with configurable seed  
- Target size option with padding by real duplicates  
- Support for extra token lists  

### Usage
```bash
python build_lexicon.py ./texts ./divine_build/lexicon.txt
````

#### Optional arguments

* `--target N` : force lexicon to have exactly N tokens
* `--extras FILE` : add extra tokens (one per line)
* `--keep-hyphens` : allow hyphens in tokens
* `--min-len N` / `--max-len N` : control token length
* `--seed N` : deterministic shuffle seed (default 333)
* `--allow-duplicates` : pad with real duplicates if target cannot be reached
* `--verbose` : detailed logs

---

## 2. divine.py

A single-file app that consumes the generated `lexicon.txt` and produces randomized “divinations”.

### Behavior

* Loads the first 777 tokens by default
* Samples 33 words each run (configurable)
* Highlights every 7th word in red and composes them into a final sentence
* Uses current datetime (America/Fortaleza) as default RNG seed for variation

### Usage

```bash
python divine.py
```

You will see a menu:

```
[1] Divine
[2] Text Used
[3] Settings
[0] Quit
```

Option **1** prints a paragraph of sampled words (every 7th word highlighted) and a final sentence built from those highlights.


## Example Run

```text
Holy, holy, holy, is the Lord God Almighty, who was and is and is to come!

[1] Divine
[2] Text Used
[3] Settings
[0] Quit
```

---

## Requirements

* Python 3.10+
* No external dependencies (standard library only)
