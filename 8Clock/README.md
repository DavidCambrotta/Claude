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
