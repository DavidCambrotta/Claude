# 8Clock

A desktop app for Bosch employees to calculate the exact clock-out time needed to complete an 8-hour workday, with optional auto-fetch of punch times directly from the Bosch Portal.

---

## Features

- **Auto-fetch** punch times from the Bosch Portal via browser automation (Playwright)
- **12h / 24h** toggle for time format preference
- **Clock-out calculator** — enter your 3 punch times and get the exact time to leave
- **Overtime indicator** — shows how much over your 8 hours you've already worked
- **Smart lunch fallback** — if only the morning punch exists and it's past 2:30 PM, automatically assumes a 1-hour lunch break (12:00–13:00)
- Custom avocado icon

---

## How it works

Provide three punch times:

| Field | Example |
|---|---|
| Morning clock-in | 8:41:00 AM |
| Clock-out for lunch | 12:30:00 PM |
| Clock-in after lunch | 1:15:00 PM |

The app calculates:
- **Clock-out target** — the time you need to leave to hit exactly 8 hours worked
- **Total time at office** — hours + minutes physically at the office (work + break)
- **Overtime** — how long past your target you've already stayed (live, updates on each calculation)

**Formula:**
```
remaining  = 8h - (lunch_out - morning_in)
clock_out  = lunch_in + remaining
```

---

## Getting started

### Run from source

```bash
pip install -r requirements.txt
playwright install chromium
python main.py
```

### Run the executable

Download `8Clock.exe` from the [Releases](../../releases) page and run it directly — no Python installation required.

---

## Portal fetch

Clicking **Fetch from Bosch Portal** opens a Chrome window and navigates to the time corrections page. If SSO login is required, you have up to 3 minutes to complete it. Once the page loads, the three punch times are read and filled in automatically.

> The browser window is visible so you can handle any MFA or SSO prompts.

---

## Requirements (source)

- Python 3.10+
- `customtkinter >= 5.2.0`
- `playwright >= 1.40.0`
- Google Chrome installed (used by Playwright)


## Build the executable (Windows)

Follow these steps to generate `8Clock.exe` from source.

### 1. Prerequisites

- Windows 10/11
- Python 3.10+ (check with `python --version`)
- Google Chrome or Microsoft Edge installed (used by Playwright at runtime)

### 2. Create a virtual environment

From the `8Clock` folder:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
pip install pyinstaller
```

### 4. Build

```bash
pyinstaller --noconfirm --onefile --windowed --name 8Clock --icon abacate.ico --add-data "abacate.ico;." --collect-all customtkinter --collect-all playwright main.py
```

What each option does:

| Option | Purpose |
|---|---|
| `--onefile` | Packs everything into a single `.exe` |
| `--windowed` | Hides the console window |
| `--name 8Clock` | Names the output `8Clock.exe` |
| `--icon abacate.ico` | Sets the file icon |
| `--add-data "abacate.ico;."` | Bundles the icon used by the window (`iconbitmap`) |
| `--collect-all customtkinter` | Includes CustomTkinter themes and assets |
| `--collect-all playwright` | Includes the Playwright driver |

### 5. Get the result

The executable is created at:

```
dist\8Clock.exe
```

The `build/` and `dist/` folders and the `.spec` file are generated automatically and ignored by git.

### 6. Test before sharing

1. Close the terminal and double-click `dist\8Clock.exe` (do not run it from the venv).
2. Click **Fetch from Bosch Portal (Chrome)** and confirm the times are filled in.
3. Try the 12h/24h toggle and **Calculate**.

### 7. Publish (optional)

Upload `dist\8Clock.exe` to the GitHub **Releases** page. The `.exe` is not committed to the repository.

> **Note:** the executable does not include browsers. The Chrome and Edge buttons use the browsers installed on the machine. The Firefox button also needs Playwright's Firefox, installed with `playwright install firefox`.

### Troubleshooting

- **Window opens and closes immediately:** rebuild without `--windowed` to see the error in the console.
- **Icon or theme missing:** make sure `--add-data` and `--collect-all customtkinter` were included.
- **Antivirus flags the `.exe`:** common with PyInstaller `--onefile` builds; rebuild with `--onedir` instead of `--onefile`.