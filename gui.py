"""
gui.py
------
Tkinter front-end. Two screens, swapped inside one window:
  1. LoginScreen  -> first-run "create master password" OR normal login
  2. VaultScreen  -> the actual password manager (table + add/search/etc.)

Run this via main.py, not directly.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

try:
    import pyperclip
    CLIPBOARD_LIB = "pyperclip"
except ImportError:
    CLIPBOARD_LIB = "tk"

import db
from password_generator import generate_password

# ---- Colour palette -----------------------------------------------------
BG_DARK = "#1e1e2f"
BG_CARD = "#27293d"
ACCENT = "#7f5af0"
ACCENT_HOVER = "#6c46e0"
TEXT_LIGHT = "#f5f5f7"
TEXT_MUTED = "#a0a0b2"
DANGER = "#e5484d"
SUCCESS = "#2cb67d"
ENTRY_BG = "#33354d"

FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_SUB = ("Segoe UI", 10)
FONT_LABEL = ("Segoe UI", 10, "bold")
FONT_NORMAL = ("Segoe UI", 10)
FONT_BTN = ("Segoe UI", 10, "bold")


def copy_to_clipboard(root, text):
    if CLIPBOARD_LIB == "pyperclip":
        pyperclip.copy(text)
    else:
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()


class RoundedButton(tk.Button):
    """A tk.Button pre-styled to look flat/modern with a hover effect."""
    def __init__(self, master, bg=ACCENT, hover=ACCENT_HOVER, fg=TEXT_LIGHT, **kwargs):
        super().__init__(
            master, bg=bg, fg=fg, activebackground=hover, activeforeground=fg,
            relief="flat", bd=0, font=FONT_BTN, cursor="hand2",
            padx=14, pady=8, **kwargs
        )
        self._bg = bg
        self._hover = hover
        self.bind("<Enter>", lambda e: self.config(bg=self._hover))
        self.bind("<Leave>", lambda e: self.config(bg=self._bg))


class LoginScreen(tk.Frame):
    def __init__(self, master, on_success):
        super().__init__(master, bg=BG_DARK)
        self.on_success = on_success
        self.first_run = not db.is_master_password_set()

        card = tk.Frame(self, bg=BG_CARD, padx=40, pady=40)
        card.place(relx=0.5, rely=0.5, anchor="center")

        title_text = "Create Master Password" if self.first_run else "Enter Master Password"
        tk.Label(card, text="🔐 Password Manager", font=FONT_TITLE, bg=BG_CARD, fg=TEXT_LIGHT).pack(pady=(0, 4))
        tk.Label(card, text=title_text, font=FONT_SUB, bg=BG_CARD, fg=TEXT_MUTED).pack(pady=(0, 20))

        self.pw_var = tk.StringVar()
        entry = tk.Entry(card, textvariable=self.pw_var, show="*", font=FONT_NORMAL,
                          bg=ENTRY_BG, fg=TEXT_LIGHT, insertbackground=TEXT_LIGHT,
                          relief="flat", width=28)
        entry.pack(ipady=8, pady=(0, 10))
        entry.focus()
        entry.bind("<Return>", lambda e: self._submit())

        if self.first_run:
            self.confirm_var = tk.StringVar()
            confirm = tk.Entry(card, textvariable=self.confirm_var, show="*", font=FONT_NORMAL,
                                bg=ENTRY_BG, fg=TEXT_LIGHT, insertbackground=TEXT_LIGHT,
                                relief="flat", width=28)
            confirm.pack(ipady=8, pady=(0, 10))
            confirm.bind("<Return>", lambda e: self._submit())
            confirm.insert(0, "")
            confirm.config(show="*")
            tk.Label(card, text="(confirm password)", font=("Segoe UI", 8), bg=BG_CARD, fg=TEXT_MUTED).pack()

        btn_text = "Create & Unlock" if self.first_run else "Unlock"
        RoundedButton(card, text=btn_text, command=self._submit).pack(pady=(16, 0), fill="x")

        if self.first_run:
            tk.Label(card, text="⚠ There is no password reset.\nIf you forget this, your vault is unrecoverable.",
                      font=("Segoe UI", 8), bg=BG_CARD, fg=DANGER, justify="center").pack(pady=(14, 0))

    def _submit(self):
        password = self.pw_var.get()
        if not password:
            messagebox.showwarning("Required", "Please enter a master password.")
            return

        if self.first_run:
            confirm = self.confirm_var.get()
            if len(password) < 6:
                messagebox.showwarning("Too short", "Use at least 6 characters for your master password.")
                return
            if password != confirm:
                messagebox.showerror("Mismatch", "Passwords do not match.")
                return
            key = db.setup_master_password(password)
            self.on_success(key)
        else:
            key = db.verify_master_password(password)
            if key is None:
                messagebox.showerror("Incorrect", "Wrong master password.")
                self.pw_var.set("")
            else:
                self.on_success(key)


class VaultScreen(tk.Frame):
    def __init__(self, master, key):
        super().__init__(master, bg=BG_DARK)
        self.key = key
        self.selected_id = None

        self._build_header()
        self._build_search_bar()
        self._build_table()
        self._build_form()

        self.refresh_table()

    # ---------------------------------------------------------------- UI
    def _build_header(self):
        header = tk.Frame(self, bg=BG_DARK)
        header.pack(fill="x", padx=20, pady=(16, 4))
        tk.Label(header, text="🔐 My Vault", font=FONT_TITLE, bg=BG_DARK, fg=TEXT_LIGHT).pack(side="left")
        RoundedButton(header, text="Lock", bg="#3a3c55", hover="#4a4c68",
                      command=self._lock).pack(side="right")

    def _build_search_bar(self):
        bar = tk.Frame(self, bg=BG_DARK)
        bar.pack(fill="x", padx=20, pady=(6, 10))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self.refresh_table())
        entry = tk.Entry(bar, textvariable=self.search_var, font=FONT_NORMAL,
                          bg=ENTRY_BG, fg=TEXT_LIGHT, insertbackground=TEXT_LIGHT, relief="flat")
        entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))
        entry.insert(0, "")
        tk.Label(bar, text="🔎 search by website / username", font=("Segoe UI", 8),
                 bg=BG_DARK, fg=TEXT_MUTED).pack(side="left")

    def _build_table(self):
        table_frame = tk.Frame(self, bg=BG_DARK)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Vault.Treeview",
                         background=BG_CARD, fieldbackground=BG_CARD, foreground=TEXT_LIGHT,
                         rowheight=30, borderwidth=0, font=FONT_NORMAL)
        style.configure("Vault.Treeview.Heading",
                         background="#3a3c55", foreground=TEXT_LIGHT, font=FONT_LABEL, relief="flat")
        style.map("Vault.Treeview", background=[("selected", ACCENT)])

        columns = ("website", "username", "password")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                                  style="Vault.Treeview", selectmode="browse")
        self.tree.heading("website", text="Website")
        self.tree.heading("username", text="Username")
        self.tree.heading("password", text="Password")
        self.tree.column("website", width=200)
        self.tree.column("username", width=200)
        self.tree.column("password", width=180)
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        actions = tk.Frame(self, bg=BG_DARK)
        actions.pack(fill="x", padx=20, pady=(0, 10))
        RoundedButton(actions, text="📋 Copy Password", command=self._copy_selected).pack(side="left", padx=(0, 8))
        RoundedButton(actions, text="🗑 Delete", bg=DANGER, hover="#c53a3e",
                      command=self._delete_selected).pack(side="left")

    def _build_form(self):
        form = tk.Frame(self, bg=BG_CARD, padx=20, pady=16)
        form.pack(fill="x", padx=20, pady=(0, 20))

        tk.Label(form, text="Website", font=FONT_LABEL, bg=BG_CARD, fg=TEXT_LIGHT).grid(row=0, column=0, sticky="w")
        tk.Label(form, text="Username", font=FONT_LABEL, bg=BG_CARD, fg=TEXT_LIGHT).grid(row=0, column=1, sticky="w", padx=(10, 0))
        tk.Label(form, text="Password", font=FONT_LABEL, bg=BG_CARD, fg=TEXT_LIGHT).grid(row=0, column=2, sticky="w", padx=(10, 0))

        self.website_var = tk.StringVar()
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()

        def styled_entry(var, show=None):
            return tk.Entry(form, textvariable=var, show=show, font=FONT_NORMAL,
                             bg=ENTRY_BG, fg=TEXT_LIGHT, insertbackground=TEXT_LIGHT, relief="flat", width=20)

        self.website_entry = styled_entry(self.website_var)
        self.website_entry.grid(row=1, column=0, ipady=6, sticky="ew")
        self.username_entry = styled_entry(self.username_var)
        self.username_entry.grid(row=1, column=1, ipady=6, sticky="ew", padx=(10, 0))
        self.password_entry = styled_entry(self.password_var)
        self.password_entry.grid(row=1, column=2, ipady=6, sticky="ew", padx=(10, 0))

        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=1)
        form.grid_columnconfigure(2, weight=1)

        btn_row = tk.Frame(form, bg=BG_CARD)
        btn_row.grid(row=2, column=0, columnspan=3, pady=(14, 0), sticky="ew")

        RoundedButton(btn_row, text="🎲 Generate", bg="#3a3c55", hover="#4a4c68",
                      command=self._generate_password).pack(side="left")
        RoundedButton(btn_row, text="💾 Save New", bg=SUCCESS, hover="#249e6b",
                      command=self._save_new).pack(side="left", padx=8)
        RoundedButton(btn_row, text="✏ Update Selected", bg=ACCENT, hover=ACCENT_HOVER,
                      command=self._update_selected).pack(side="left")
        RoundedButton(btn_row, text="✖ Clear Form", bg="#3a3c55", hover="#4a4c68",
                      command=self._clear_form).pack(side="right")

    # ------------------------------------------------------------ actions
    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        term = self.search_var.get()
        entries = db.search_entries(self.key, term) if term else db.get_all_entries(self.key)
        for e in entries:
            masked = "•" * min(len(e["password"]), 12)
            self.tree.insert("", "end", iid=str(e["id"]),
                              values=(e["website"], e["username"], masked))
        self._entries_cache = {e["id"]: e for e in entries}

    def _on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        entry_id = int(selection[0])
        entry = self._entries_cache.get(entry_id)
        if not entry:
            return
        self.selected_id = entry_id
        self.website_var.set(entry["website"])
        self.username_var.set(entry["username"])
        self.password_var.set(entry["password"])

    def _clear_form(self):
        self.selected_id = None
        self.website_var.set("")
        self.username_var.set("")
        self.password_var.set("")
        self.tree.selection_remove(self.tree.selection())

    def _generate_password(self):
        length = simpledialog.askinteger(
            "Password length", "Length (8-32):", initialvalue=12, minvalue=8, maxvalue=32, parent=self
        )
        if length is None:
            return
        self.password_var.set(generate_password(length=length))

    def _save_new(self):
        website = self.website_var.get().strip()
        username = self.username_var.get().strip()
        password = self.password_var.get()
        if not website or not username or not password:
            messagebox.showwarning("Missing info", "Website, username and password are all required.")
            return
        db.add_password(website, username, self.key, password)
        self._clear_form()
        self.refresh_table()

    def _update_selected(self):
        if self.selected_id is None:
            messagebox.showinfo("Nothing selected", "Select a row in the table first, or use 'Save New'.")
            return
        website = self.website_var.get().strip()
        username = self.username_var.get().strip()
        password = self.password_var.get()
        if not website or not username or not password:
            messagebox.showwarning("Missing info", "Website, username and password are all required.")
            return
        db.update_entry(self.selected_id, self.key, website, username, password)
        self._clear_form()
        self.refresh_table()

    def _delete_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Nothing selected", "Select a row to delete first.")
            return
        entry_id = int(selection[0])
        entry = self._entries_cache.get(entry_id)
        confirm = messagebox.askyesno("Confirm delete", f"Delete saved login for '{entry['website']}'?")
        if confirm:
            db.delete_entry(entry_id)
            self._clear_form()
            self.refresh_table()

    def _copy_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Nothing selected", "Select a row to copy its password.")
            return
        entry_id = int(selection[0])
        entry = self._entries_cache.get(entry_id)
        copy_to_clipboard(self.winfo_toplevel(), entry["password"])
        messagebox.showinfo("Copied", f"Password for '{entry['website']}' copied to clipboard.")

    def _lock(self):
        app = self.winfo_toplevel()
        app.show_login()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Password Manager")
        self.geometry("760x600")
        self.minsize(680, 560)
        self.configure(bg=BG_DARK)
        db.init_db()
        self.current_frame = None
        self.show_login()

    def show_login(self):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = LoginScreen(self, on_success=self.show_vault)
        self.current_frame.pack(fill="both", expand=True)

    def show_vault(self, key):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = VaultScreen(self, key)
        self.current_frame.pack(fill="both", expand=True)


if __name__ == "__main__":
    App().mainloop()
