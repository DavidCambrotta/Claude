import customtkinter as ctk
from datetime import datetime, timedelta

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

PLACEHOLDERS = {
    "12h": ("e.g. 8:41:00 AM", "e.g. 12:30:00 PM", "e.g. 1:15:00 PM"),
    "24h": ("e.g. 08:41:00",   "e.g. 12:30:00",    "e.g. 13:15:00"),
}


class BoschWatch(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BoschWatch")
        self.geometry("420x600")
        self.resizable(False, False)

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
        ).pack(pady=(0, 20))

        # ── Input card ──────────────────────────────────────────
        card = ctk.CTkFrame(self, corner_radius=16)
        card.pack(padx=30, fill="x")

        ph = PLACEHOLDERS["12h"]
        self.entry_morning_in, self.lbl_ph_in   = self._row(card, "Morning clock in",     ph[0])
        self.entry_lunch_out,  self.lbl_ph_out  = self._row(card, "Clock out for lunch",  ph[1])
        self.entry_lunch_in,   self.lbl_ph_back = self._row(card, "Clock in after lunch", ph[2])

        # ── Calculate button ────────────────────────────────────
        ctk.CTkButton(
            self, text="Calculate", command=self.calculate,
            font=ctk.CTkFont(size=15, weight="bold"),
            height=46, corner_radius=12
        ).pack(padx=30, pady=22, fill="x")

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
        self.lbl_detail.pack(pady=(0, 16))

    # ── helpers ─────────────────────────────────────────────────
    def _row(self, parent, label: str, placeholder: str):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.pack(padx=22, pady=9, fill="x")
        ctk.CTkLabel(wrap, text=label, font=ctk.CTkFont(size=13), anchor="w").pack(fill="x")
        entry = ctk.CTkEntry(
            wrap, placeholder_text=placeholder,
            height=38, corner_radius=8, font=ctk.CTkFont(size=14)
        )
        entry.pack(fill="x", pady=(3, 0))
        return entry, entry  # entry + ref for placeholder update

    def _on_toggle(self, value: str):
        self._fmt = value
        ph = PLACEHOLDERS[value]
        self.entry_morning_in.configure(placeholder_text=ph[0])
        self.entry_lunch_out.configure(placeholder_text=ph[1])
        self.entry_lunch_in.configure(placeholder_text=ph[2])
        # reset result when switching format
        self.lbl_time.configure(text="--:--", text_color="#4fc3f7")
        self.lbl_sub.configure(text="clock-out target", text_color="gray")
        self.lbl_detail.configure(text="")

    def _parse(self, text: str) -> datetime:
        text = text.strip()
        if self._fmt == "12h":
            formats = ("%I:%M:%S %p", "%I:%M:%S%p", "%I:%M %p", "%I:%M%p", "%I %p", "%I%p")
            return datetime.strptime(text.upper(), next(
                f for f in formats if self._try_parse(text.upper(), f) is not None
            ))
        else:
            formats = ("%H:%M:%S", "%H:%M", "%H%M%S", "%H%M")
            return datetime.strptime(text, next(
                f for f in formats if self._try_parse(text, f) is not None
            ))

    def _try_parse(self, text: str, fmt: str):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            return None

    # ── core logic ──────────────────────────────────────────────
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

        if self._fmt == "12h":
            result_str = clock_out.strftime("%I:%M:%S %p").lstrip("0")
        else:
            result_str = clock_out.strftime("%H:%M:%S")

        self.lbl_time.configure(text=result_str, text_color="#4fc3f7")
        self.lbl_sub.configure(text="clock-out to reach 8 h worked", text_color="gray")
        self.lbl_detail.configure(
            text=f"Total time at office: {hh}h {mm:02d}m  •  Break: {int(lunch_break // 60)} min",
            text_color="gray"
        )

    def _show_error(self, title: str, detail: str):
        self.lbl_time.configure(text=title, text_color="#ef5350")
        self.lbl_sub.configure(text=detail, text_color="#ef5350")
        self.lbl_detail.configure(text="")


if __name__ == "__main__":
    app = BoschWatch()
    app.mainloop()
