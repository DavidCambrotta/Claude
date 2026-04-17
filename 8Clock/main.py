import ctypes
import os
import threading
import customtkinter as ctk
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

PORTAL_URL = (
    "https://inside.bosch.com/irj/portal/fiori"
    "#HR_CORE_MyTimeEventsExt-manageCorrections"
)
PORTAL_SELECTORS = [
    "#__identifier2-__xmlview0--idEventsTable-0-text",
    "#__identifier2-__xmlview0--idEventsTable-1-text",
    "#__identifier2-__xmlview0--idEventsTable-2-text",
]
LOGIN_TIMEOUT_MS = 180_000   # 3 min for SSO login
ELEMENT_TIMEOUT_MS = 30_000

PLACEHOLDERS = {
    "12h": ("e.g. 8:41:00 AM", "e.g. 12:30:00 PM", "e.g. 1:15:00 PM"),
    "24h": ("e.g. 08:41:00",   "e.g. 12:30:00",    "e.g. 13:15:00"),
}


class BoschWatch(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BoschWatch")
        self.geometry("420x720")
        self.resizable(False, False)
        self.iconbitmap(os.path.join(os.path.dirname(__file__), "abacate.ico"))

        self._fmt = "12h"

        # ── Header ──────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="BoschWatch",
            font=ctk.CTkFont(size=30, weight="bold")
        ).pack(pady=(35, 8))

        # ── Format toggle ────────────────────────────────────────
        self.toggle = ctk.CTkSegmentedButton(
            self, values=["12h", "24h"],
            command=self._on_toggle,
            font=ctk.CTkFont(size=13, weight="bold"),
            width=120, height=30,
        )
        self.toggle.set("12h")
        self.toggle.pack(pady=(0, 16))

        ctk.CTkLabel(
            self, text="Calculate your 8-hour clock-out time",
            font=ctk.CTkFont(size=13), text_color="gray"
        ).pack(pady=(0, 16))

        # ── Fetch button ─────────────────────────────────────────
        self.btn_fetch = ctk.CTkButton(
            self, text="Fetch from Bosch Portal",
            command=self._fetch_start,
            font=ctk.CTkFont(size=13),
            height=36, corner_radius=10,
            fg_color="#1e5f8e", hover_color="#174d75",
        )
        self.btn_fetch.pack(padx=30, fill="x")

        self.lbl_status = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=11), text_color="gray"
        )
        self.lbl_status.pack(pady=(4, 8))

        # ── Input card ──────────────────────────────────────────
        card = ctk.CTkFrame(self, corner_radius=16)
        card.pack(padx=30, fill="x")

        ph = PLACEHOLDERS["12h"]
        self.entry_morning_in = self._row(card, "Morning clock in",     ph[0])
        self.entry_lunch_out  = self._row(card, "Clock out for lunch",  ph[1])
        self.entry_lunch_in   = self._row(card, "Clock in after lunch", ph[2])

        # ── Calculate button ────────────────────────────────────
        ctk.CTkButton(
            self, text="Calculate", command=self.calculate,
            font=ctk.CTkFont(size=15, weight="bold"),
            height=46, corner_radius=12
        ).pack(padx=30, pady=18, fill="x")

        # ── Result card ─────────────────────────────────────────
        result_card = ctk.CTkFrame(self, corner_radius=16)
        result_card.pack(padx=30, fill="x")

        self.lbl_time = ctk.CTkLabel(
            result_card, text="--:--",
            font=ctk.CTkFont(size=48, weight="bold"),
            text_color="#4fc3f7"
        )
        self.lbl_time.pack(pady=(18, 2))

        self.lbl_sub = ctk.CTkLabel(
            result_card, text="clock-out target",
            font=ctk.CTkFont(size=12), text_color="gray"
        )
        self.lbl_sub.pack(pady=(0, 6))

        self.lbl_detail = ctk.CTkLabel(
            result_card, text="",
            font=ctk.CTkFont(size=12), text_color="gray"
        )
        self.lbl_detail.pack(pady=(0, 6))

        self.lbl_overtime = ctk.CTkLabel(
            result_card, text=" ",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#66bb6a"
        )
        self.lbl_overtime.pack(pady=(0, 16))

    # ── helpers ─────────────────────────────────────────────────
    def _row(self, parent, label: str, placeholder: str) -> ctk.CTkEntry:
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.pack(padx=22, pady=9, fill="x")
        ctk.CTkLabel(wrap, text=label, font=ctk.CTkFont(size=13), anchor="w").pack(fill="x")
        entry = ctk.CTkEntry(
            wrap, placeholder_text=placeholder,
            height=38, corner_radius=8, font=ctk.CTkFont(size=14)
        )
        entry.pack(fill="x", pady=(3, 0))
        return entry

    def _set_status(self, msg: str, color: str = "gray"):
        self.lbl_status.configure(text=msg, text_color=color)

    def _on_toggle(self, value: str):
        self._fmt = value
        ph = PLACEHOLDERS[value]
        self.entry_morning_in.configure(placeholder_text=ph[0])
        self.entry_lunch_out.configure(placeholder_text=ph[1])
        self.entry_lunch_in.configure(placeholder_text=ph[2])
        self.lbl_time.configure(text="--:--", text_color="#4fc3f7")
        self.lbl_sub.configure(text="clock-out target", text_color="gray")
        self.lbl_detail.configure(text="")

    def _fill_entries(self, times: list[str]):
        """Fill entry fields with times already formatted for the active toggle."""
        entries = [self.entry_morning_in, self.entry_lunch_out, self.entry_lunch_in]
        for entry, value in zip(entries, times):
            entry.delete(0, "end")
            entry.insert(0, value)

    # ── Portal fetch (background thread) ────────────────────────
    def _fetch_start(self):
        self.btn_fetch.configure(state="disabled")
        self._set_status("Opening browser — please log in if prompted...", "#f0a500")
        threading.Thread(target=self._fetch_worker, daemon=True).start()

    def _fetch_worker(self):
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=False, channel="chrome")
                page = browser.new_page()
                page.goto(PORTAL_URL)

                self.after(0, self._set_status,
                           "Waiting for portal to load (log in if needed)...", "#f0a500")

                # Wait for the first time element — gives user time to SSO
                page.wait_for_selector(
                    PORTAL_SELECTORS[0],
                    timeout=LOGIN_TIMEOUT_MS
                )

                # Allow remaining elements to appear
                for sel in PORTAL_SELECTORS[1:]:
                    page.wait_for_selector(sel, timeout=ELEMENT_TIMEOUT_MS)

                raw_times = [
                    page.inner_text(sel).strip()
                    for sel in PORTAL_SELECTORS
                ]
                browser.close()

            formatted = [self._convert_portal_time(t) for t in raw_times]
            self.after(0, self._fetch_done, formatted)

        except PWTimeout:
            self.after(0, self._fetch_error, "Timed out — portal not reachable or login took too long")
        except Exception as exc:
            self.after(0, self._fetch_error, f"Error: {exc}")

    def _convert_portal_time(self, raw: str) -> str:
        """Parse a 24h time string from the portal and reformat for the active toggle."""
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                dt = datetime.strptime(raw, fmt)
                if self._fmt == "12h":
                    return dt.strftime("%I:%M:%S %p").lstrip("0")
                else:
                    return dt.strftime("%H:%M:%S")
            except ValueError:
                pass
        return raw  # return as-is if unparseable

    def _fetch_done(self, times: list[str]):
        morning_only = bool(times[0]) and not times[1].strip() and not times[2].strip()
        if morning_only and datetime.now() >= datetime.now().replace(hour=14, minute=30, second=0, microsecond=0):
            times[1] = "12:00:00 PM" if self._fmt == "12h" else "12:00:00"
            times[2] = "1:00:00 PM"  if self._fmt == "12h" else "13:00:00"
            self._fill_entries(times)
            self._set_status(
                f"Fetched: {times[0]}  •  Lunch assumed 12:00–13:00 (1 h)",
                "#f0a500"
            )
            self.btn_fetch.configure(state="normal")
            self.calculate()
            return

        self._fill_entries(times)
        self._set_status(f"Fetched: {' | '.join(times)}", "#66bb6a")
        self.btn_fetch.configure(state="normal")
        self.calculate()

    def _fetch_error(self, msg: str):
        self._set_status(msg, "#ef5350")
        self.btn_fetch.configure(state="normal")

    # ── Parse & calculate ────────────────────────────────────────
    def _try_parse(self, text: str, fmt: str):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            return None

    def _parse(self, text: str) -> datetime:
        text = text.strip()
        if self._fmt == "12h":
            fmts = ("%I:%M:%S %p", "%I:%M:%S%p", "%I:%M %p", "%I:%M%p", "%I %p", "%I%p")
            return datetime.strptime(text.upper(), next(
                f for f in fmts if self._try_parse(text.upper(), f) is not None
            ))
        else:
            fmts = ("%H:%M:%S", "%H:%M", "%H%M%S", "%H%M")
            return datetime.strptime(text, next(
                f for f in fmts if self._try_parse(text, f) is not None
            ))

    def calculate(self):
        try:
            t_in        = self._parse(self.entry_morning_in.get())
            t_lunch_out = self._parse(self.entry_lunch_out.get())
            t_lunch_in  = self._parse(self.entry_lunch_in.get())
        except (ValueError, StopIteration):
            hint = "8:41:00 AM" if self._fmt == "12h" else "08:41:00"
            self._show_error("Invalid time", f"Use {self._fmt} format (e.g. {hint})")
            return

        morning_secs = (t_lunch_out - t_in).total_seconds()
        if morning_secs < 0:
            self._show_error("Error", "Lunch-out must be after morning clock-in")
            return

        lunch_break = (t_lunch_in - t_lunch_out).total_seconds()
        if lunch_break < 0:
            self._show_error("Error", "After-lunch clock-in must be after lunch-out")
            return

        remaining = timedelta(hours=8) - timedelta(seconds=morning_secs)
        clock_out  = t_lunch_in + remaining

        total_with_break = timedelta(hours=8) + timedelta(seconds=lunch_break)
        hh, mm = divmod(int(total_with_break.total_seconds() // 60), 60)

        result_str = (
            clock_out.strftime("%I:%M:%S %p").lstrip("0")
            if self._fmt == "12h"
            else clock_out.strftime("%H:%M:%S")
        )

        self.lbl_time.configure(text=result_str, text_color="#4fc3f7")
        self.lbl_sub.configure(text="clock-out to reach 8 h worked", text_color="gray")
        self.lbl_detail.configure(
            text=f"Total time at office: {hh}h {mm:02d}m  •  Break: {int(lunch_break // 60)} min",
            text_color="green"
        )

        # compare clock_out against current time — lift both to today's date
        today = datetime.now().date()
        clock_out_today = clock_out.replace(year=today.year, month=today.month, day=today.day)
        now = datetime.now().replace(microsecond=0)
        if now > clock_out_today:
            delta = now - clock_out_today
            total_secs = int(delta.total_seconds())
            oh, rem = divmod(total_secs, 3600)
            om, os_ = divmod(rem, 60)
            if oh > 0:
                over_str = f"+{oh}h {om:02d}m {os_:02d}s over"
            else:
                over_str = f"+{om}m {os_:02d}s over"
            self.lbl_overtime.configure(text=over_str)
        else:
            self.lbl_overtime.configure(text=" ")

    def _show_error(self, title: str, detail: str):
        self.lbl_time.configure(text=title, text_color="#ef5350")
        self.lbl_sub.configure(text=detail, text_color="#ef5350")
        self.lbl_detail.configure(text="")
        self.lbl_overtime.configure(text=" ")


if __name__ == "__main__":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("8Clock.app")
    app = BoschWatch()
    app.mainloop()
