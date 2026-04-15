import customtkinter as ctk
from datetime import datetime, timedelta

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class BoschWatch(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BoschWatch")
        self.geometry("420x560")
        self.resizable(False, False)

        # ── Header ──────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="BoschWatch",
            font=ctk.CTkFont(size=30, weight="bold")
        ).pack(pady=(35, 4))

        ctk.CTkLabel(
            self, text="Calculate your 8-hour clock-out time",
            font=ctk.CTkFont(size=13), text_color="gray"
        ).pack(pady=(0, 25))

        # ── Input card ──────────────────────────────────────────
        card = ctk.CTkFrame(self, corner_radius=16)
        card.pack(padx=30, fill="x")

        self.entry_morning_in  = self._row(card, "Morning clock in",        "e.g. 08:00")
        self.entry_lunch_out   = self._row(card, "Clock out for lunch",     "e.g. 12:30")
        self.entry_lunch_in    = self._row(card, "Clock in after lunch",    "e.g. 13:15")

        # ── Button ──────────────────────────────────────────────
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

    def _parse(self, text: str) -> datetime:
        for fmt in ("%H:%M", "%H%M", "%H.%M"):
            try:
                return datetime.strptime(text.strip(), fmt)
            except ValueError:
                pass
        raise ValueError(f"Cannot parse '{text}'")

    # ── core logic ──────────────────────────────────────────────
    def calculate(self):
        try:
            t_in        = self._parse(self.entry_morning_in.get())
            t_lunch_out = self._parse(self.entry_lunch_out.get())
            t_lunch_in  = self._parse(self.entry_lunch_in.get())
        except ValueError:
            self._show_error("Invalid time", "Use HH:MM format (e.g. 08:00)")
            return

        morning_secs = (t_lunch_out - t_in).total_seconds()
        if morning_secs < 0:
            self._show_error("Error", "Lunch-out must be after morning clock-in")
            return

        lunch_break = (t_lunch_in - t_lunch_out).total_seconds()
        if lunch_break < 0:
            self._show_error("Error", "After-lunch clock-in must be after lunch-out")
            return

        worked_so_far = timedelta(seconds=morning_secs)
        remaining     = timedelta(hours=8) - worked_so_far
        clock_out     = t_lunch_in + remaining

        total_with_break = timedelta(hours=8) + timedelta(seconds=lunch_break)
        hh, mm = divmod(int(total_with_break.total_seconds() // 60), 60)

        self.lbl_time.configure(text=clock_out.strftime("%H:%M"), text_color="#4fc3f7")
        self.lbl_sub.configure(text="clock-out to reach 8 h worked", text_color="gray")
        self.lbl_detail.configure(
            text=f"Total time at office: {hh}h {mm:02d}m  •  Break: {int(lunch_break//60)} min",
            text_color="gray"
        )

    def _show_error(self, title: str, detail: str):
        self.lbl_time.configure(text=title, text_color="#ef5350")
        self.lbl_sub.configure(text=detail, text_color="#ef5350")
        self.lbl_detail.configure(text="")


if __name__ == "__main__":
    app = BoschWatch()
    app.mainloop()
