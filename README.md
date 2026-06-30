# Invoice Generator

One-click monthly invoice PDF generator. Double-click `GENERATE_INVOICE.bat` to create a professional invoice.

## Quick Start (3 steps)

### 1. Install Python

Download and install Python 3.10+ from [python.org](https://www.python.org/downloads/).

**Important:** Check "Add Python to PATH" during installation.

### 2. Run Setup

Double-click **`SETUP.bat`** — it installs the required package and creates your `.env` file.

Or run manually:
```
pip install fpdf2
copy .env.example .env
```

Then edit `.env` with your real company/banking data.

### 3. Generate Invoice

Double-click **`GENERATE_INVOICE.bat`**

It will ask you:
1. **Amount** — type the number (e.g. `6250`)
2. **Date** — press ENTER for today, or type `MM.DD.YYYY` (e.g. `06.30.2026`)

The PDF opens automatically after generation.

## Files

| File | Purpose |
|------|---------|
| `GENERATE_INVOICE.bat` | Double-click to generate invoice (Windows) |
| `SETUP.bat` | First-time setup (installs dependencies, creates .env) |
| `generate_monthly_invoice.py` | Main script (called by BAT) |
| `.env.example` | Template — copy to `.env` and fill in your data |
| `.env` | Your real data (never shared, never committed) |
| `output/` | Generated invoices go here (INV-0001.pdf, INV-0002.pdf...) |

## How It Works

- Company info, banking details, and client data are stored in `.env` (fixed, set once)
- Each month you only enter: **amount** and **date**
- Invoice numbers auto-increment: INV-0001, INV-0002, INV-0003...
- Outputs: PDF (for sending) + HTML (editable backup)
- PDF opens automatically on Windows

## Date Formats Accepted

| Input | Result |
|-------|--------|
| *(press Enter)* | Today's date |
| `06.30.2026` | June 30, 2026 |
| `06/30/2026` | June 30, 2026 |
| `06-30-2026` | June 30, 2026 |

## Requirements

- Python 3.10+
- fpdf2 (auto-installed by SETUP.bat)
- Windows (for BAT files; Python script works on any OS)
