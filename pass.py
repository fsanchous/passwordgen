# Paroļu ģenerators (Python + Tkinter + OOP + JSON)
# Faili: pass.py (šis fails) + automātiski izveidosies data.json

import json
import os
import random
import re
import string
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from tkinter import messagebox

DATA_FILE = "data.json"
MAX_HISTORY = 20


@dataclass
class PasswordPolicy:
    length: int
    use_lower: bool
    use_upper: bool
    use_digits: bool
    use_symbols: bool

    def validate(self) -> None:
        if not isinstance(self.length, int):
            raise ValueError("Paroles garumam jābūt veselam skaitlim.")
        if self.length < 8 or self.length > 64:
            raise ValueError("Paroles garumam jābūt diapazonā 8-64.")
        if not (self.use_lower or self.use_upper or self.use_digits or self.use_symbols):
            raise ValueError("Izvēlies vismaz vienu simbolu tipu (burti/cipari/simboli).")

    def selected_sets(self):
        sets = []
        if self.use_lower:
            sets.append(string.ascii_lowercase)
        if self.use_upper:
            sets.append(string.ascii_uppercase)
        if self.use_digits:
            sets.append(string.digits)
        if self.use_symbols:
            # Drošs, bieži lietots komplekts (bez atstarpēm)
            sets.append("!@#$%^&*_-+=?.,:;")
        return sets


class PasswordGenerator:
    def generate(self, policy: PasswordPolicy) -> str:
        policy.validate()
        sets = policy.selected_sets()

        # Nodrošina, ka parole satur vismaz 1 simbolu no katras izvēlētās kopas
        password_chars = [random.choice(s) for s in sets]

        all_chars = "".join(sets)
        remaining = policy.length - len(password_chars)
        password_chars += [random.choice(all_chars) for _ in range(remaining)]

        random.shuffle(password_chars)
        return "".join(password_chars)

    def strength_label(self, password: str) -> str:
        # Vienkāršs novērtējums (pietiek ieskaitei)
        length = len(password)
        classes = 0
        if re.search(r"[a-z]", password):
            classes += 1
        if re.search(r"[A-Z]", password):
            classes += 1
        if re.search(r"\d", password):
            classes += 1
        if re.search(r"[^A-Za-z0-9]", password):
            classes += 1

        score = length + classes * 5
        if score < 18:
            return "Vāja"
        elif score < 30:
            return "Vidēja"
        return "Stipra"


class Storage:
    def load(self) -> dict:
        if not os.path.exists(DATA_FILE):
            return {
                "settings": {
                    "length": 16,
                    "use_lower": True,
                    "use_upper": True,
                    "use_digits": True,
                    "use_symbols": False
                },
                "history": []
            }
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "settings" not in data:
                data["settings"] = {}
            if "history" not in data:
                data["history"] = []
            return data
        except Exception:
            # Ja fails bojāts, startē ar noklusējumu
            return {
                "settings": {
                    "length": 16,
                    "use_lower": True,
                    "use_upper": True,
                    "use_digits": True,
                    "use_symbols": False
                },
                "history": []
            }

    def save(self, settings: dict, history: list) -> None:
        data = {"settings": settings, "history": history[-MAX_HISTORY:]}
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class PasswordApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Paroļu ģenerators")
        self.root.resizable(False, False)

        self.generator = PasswordGenerator()
        self.storage = Storage()

        self.data = self.storage.load()
        self.history = self.data.get("history", [])

        self._build_ui()
        self._apply_loaded_settings()
        self._refresh_history_list()

    def _build_ui(self):
        pad = 10

        # Iestatījumi
        frm_settings = tk.LabelFrame(self.root, text="Iestatījumi", padx=pad, pady=pad)
        frm_settings.grid(row=0, column=0, padx=pad, pady=pad, sticky="ew")

        tk.Label(frm_settings, text="Paroles garums (8-64):").grid(row=0, column=0, sticky="w")
        self.length_var = tk.StringVar()
        self.length_entry = tk.Entry(frm_settings, textvariable=self.length_var, width=6)
        self.length_entry.grid(row=0, column=1, sticky="w", padx=(8, 0))

        self.lower_var = tk.BooleanVar()
        self.upper_var = tk.BooleanVar()
        self.digits_var = tk.BooleanVar()
        self.symbols_var = tk.BooleanVar()

        tk.Checkbutton(frm_settings, text="Mazie burti (a-z)", variable=self.lower_var).grid(row=1, column=0, columnspan=2, sticky="w")
        tk.Checkbutton(frm_settings, text="Lielie burti (A-Z)", variable=self.upper_var).grid(row=2, column=0, columnspan=2, sticky="w")
        tk.Checkbutton(frm_settings, text="Cipari (0-9)", variable=self.digits_var).grid(row=3, column=0, columnspan=2, sticky="w")
        tk.Checkbutton(frm_settings, text="Speciālās zīmes (!@#$...)", variable=self.symbols_var).grid(row=4, column=0, columnspan=2, sticky="w")

        # Darbības
        frm_actions = tk.Frame(self.root, padx=pad, pady=0)
        frm_actions.grid(row=1, column=0, padx=pad, pady=(0, pad), sticky="ew")

        tk.Button(frm_actions, text="Ģenerēt", width=12, command=self.on_generate).grid(row=0, column=0, padx=(0, 6))
        tk.Button(frm_actions, text="Kopēt", width=12, command=self.on_copy).grid(row=0, column=1, padx=(0, 6))
        tk.Button(frm_actions, text="Saglabāt", width=12, command=self.on_save).grid(row=0, column=2, padx=(0, 6))
        tk.Button(frm_actions, text="Ielādēt", width=12, command=self.on_load).grid(row=0, column=3)

        # Rezultāts
        frm_result = tk.LabelFrame(self.root, text="Rezultāts", padx=pad, pady=pad)
        frm_result.grid(row=2, column=0, padx=pad, pady=(0, pad), sticky="ew")

        self.password_var = tk.StringVar(value="")
        self.password_entry = tk.Entry(frm_result, textvariable=self.password_var, width=42)
        self.password_entry.grid(row=0, column=0, sticky="w")

        self.strength_var = tk.StringVar(value="Stiprums: -")
        tk.Label(frm_result, textvariable=self.strength_var).grid(row=1, column=0, sticky="w", pady=(6, 0))

        # Vēsture
        frm_history = tk.LabelFrame(self.root, text="Vēsture (pēdējās paroles)", padx=pad, pady=pad)
        frm_history.grid(row=3, column=0, padx=pad, pady=(0, pad), sticky="ew")

        self.history_listbox = tk.Listbox(frm_history, width=54, height=8)
        self.history_listbox.grid(row=0, column=0, sticky="ew")
        self.history_listbox.bind("<<ListboxSelect>>", self.on_history_select)

    def _apply_loaded_settings(self):
        s = self.data.get("settings", {})
        self.length_var.set(str(s.get("length", 16)))
        self.lower_var.set(bool(s.get("use_lower", True)))
        self.upper_var.set(bool(s.get("use_upper", True)))
        self.digits_var.set(bool(s.get("use_digits", True)))
        self.symbols_var.set(bool(s.get("use_symbols", False)))

    def _current_policy(self) -> PasswordPolicy:
        try:
            length = int(self.length_var.get().strip())
        except Exception:
            raise ValueError("Paroles garumam jābūt veselam skaitlim.")

        return PasswordPolicy(
            length=length,
            use_lower=self.lower_var.get(),
            use_upper=self.upper_var.get(),
            use_digits=self.digits_var.get(),
            use_symbols=self.symbols_var.get()
        )

    def _settings_dict(self) -> dict:
        # Saglabā tieši to, kas UI
        return {
            "length": int(self.length_var.get().strip()) if self.length_var.get().strip().isdigit() else 16,
            "use_lower": self.lower_var.get(),
            "use_upper": self.upper_var.get(),
            "use_digits": self.digits_var.get(),
            "use_symbols": self.symbols_var.get()
        }

    def _refresh_history_list(self):
        self.history_listbox.delete(0, tk.END)
        # Rāda jaunākās augšā
        for item in reversed(self.history[-MAX_HISTORY:]):
            # item: {"time": "...", "password": "..."}
            t = item.get("time", "")
            p = item.get("password", "")
            self.history_listbox.insert(tk.END, f"{t}  |  {p}")

    def on_generate(self):
        try:
            policy = self._current_policy()
            pwd = self.generator.generate(policy)
        except ValueError as e:
            messagebox.showerror("Kļūda", str(e))
            return
        except Exception:
            messagebox.showerror("Kļūda", "Notika neparedzēta kļūda paroles ģenerēšanā.")
            return

        self.password_var.set(pwd)
        self.strength_var.set(f"Stiprums: {self.generator.strength_label(pwd)}")

        # Pievieno vēsturē un autosaglabā
        self.history.append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "password": pwd
        })
        self.history = self.history[-MAX_HISTORY:]
        self._refresh_history_list()
        self.on_save(silent=True)

    def on_copy(self):
        pwd = self.password_var.get()
        if not pwd:
            messagebox.showinfo("Info", "Nav ko kopēt (parole nav ģenerēta).")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(pwd)
        self.root.update()
        messagebox.showinfo("Info", "Parole nokopēta starpliktuvē.")

    def on_save(self, silent=False):
        try:
            # Pārbaudām politiku, lai nesaglabā absurdu (piem., garums nav skaitlis)
            policy = self._current_policy()
            policy.validate()
        except Exception:
            # Ja lietotājs ievadījis nesaprotamu garumu, tomēr saglabāsim checkboxus,
            # bet garumu ieliksim drošu default.
            pass

        settings = self._settings_dict()
        try:
            self.storage.save(settings=settings, history=self.history)
            if not silent:
                messagebox.showinfo("Info", "Dati saglabāti (data.json).")
        except Exception:
            messagebox.showerror("Kļūda", "Neizdevās saglabāt datus failā.")

    def on_load(self):
        self.data = self.storage.load()
        self.history = self.data.get("history", [])
        self._apply_loaded_settings()
        self._refresh_history_list()
        messagebox.showinfo("Info", "Dati ielādēti no faila (data.json).")

    def on_history_select(self, _event):
        sel = self.history_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        # listbox rāda reversed(), tātad jāpārvērš uz īsto index vēsturē
        real_index = len(self.history) - 1 - idx
        if 0 <= real_index < len(self.history):
            pwd = self.history[real_index].get("password", "")
            if pwd:
                self.password_var.set(pwd)
                self.strength_var.set(f"Stiprums: {self.generator.strength_label(pwd)}")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    PasswordApp().run()
