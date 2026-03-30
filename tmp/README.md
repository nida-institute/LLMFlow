# Paratext Back-Translation Pipeline

## Overview

This pipeline performs automated back-translation of Paratext Scripture projects using LLMFlow. It automatically extracts language metadata from the project's Scripture Burrito manifest (`metadata.json`) to provide context-aware back-translation.

## Features

- **Automatic Language Detection**: Reads language name and ISO code from Scripture Burrito metadata
- **Context-Aware Prompting**: Uses source language information to guide the LLM
- **Full Book Support**: Backs-translate any book in the Paratext project
- **USJ Format**: Works with structured JSON representation of Scripture text
- **Modern Metadata**: Uses Scripture Burrito standard for clean dict-based access

## Prerequisites

1. Set the `PARATEXT_DIR` environment variable to your Paratext projects directory:
   ```bash
   export PARATEXT_DIR="/Volumes/YourParatextMount"
   ```

   Or for the SMB share:
   ```bash
   export PARATEXT_DIR="/Volumes/Windows\\ 11\\ \\(I\\)/My\\ Paratext\\ 9\\ Projects"
   ```

2. Ensure you're in the hatch environment:
   ```bash
   hatch shell
   ```

## Usage

Run a back-translation for a specific project and book:

```bash
llmflow run tmp/backtranslation.yaml \
  --project_name "YourProjectName" \
  --book "LUK"
```

### Example

```bash
llmflow run tmp/backtranslation.yaml \
  --project_name "cebAPDv4" \
  --book "MRK"
```

This will:
1. Read project metadata from `cebAPDv4/Settings.xml` (language: Cebuano, ISO: ceb)
2. Load the book of Mark from the project in USJ format
3. Send it to GPT-4o with language-aware back-translation prompt
4. Save the result to: `outputs/backtranslation/cebAPDv4_MRK_backtrans.txt`

## Command-line Parameters

- `--project_name`: Name of the Paratext project directory (required)
- `--book`: 3-letter USFM book code (required)
  - Examples: `GEN`, `EXO`, `MAT`, `MRK`, `LUK`, `JHN`, `ACT`, `ROM`, `REV`
- `--paratext_dir`: Override the Paratext base directory (optional)

## Files

- `backtranslation.yaml` - Pipeline configuration
- `backtranslation.gpt` - Back-translation prompt (replace with Paul Liu prompt if available)
- Output: `outputs/backtranslation/{project}_{book}_backtrans.txt`

## Customization

To use the specific Paul Liu prompt, replace the content of `backtranslation.gpt` with the prompt from the backtranslation repository.

## Supported Book Codes

All standard USFM 3.1 book codes are supported. Common NT books:
- MAT, MRK, LUK, JHN (Gospels)
- ACT (Acts)
- ROM, 1CO, 2CO, GAL, EPH, PHP, COL, 1TH, 2TH, 1TI, 2TI, TIT, PHM (Paul's letters)
- HEB, JAS, 1PE, 2PE, 1JN, 2JN, 3JN, JUD, REV (General epistles and Revelation)

Common OT books:
- GEN, EXO, LEV, NUM, DEU (Torah)
- JOS, JDG, RUT, 1SA, 2SA, 1KI, 2KI (Historical)
- PSA, PRO, ECC, SNG (Wisdom)
- ISA, JER, EZK, DAN (Major Prophets)
