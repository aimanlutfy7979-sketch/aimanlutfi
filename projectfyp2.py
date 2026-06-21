import os
import json
import time
import threading
import ctypes
import hashlib
from ctypes import wintypes

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from tkinter.simpledialog import askstring


# =========================
# Windows helpers
# =========================
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

GetLogicalDrives = kernel32.GetLogicalDrives
GetDriveTypeW = kernel32.GetDriveTypeW
GetDriveTypeW.argtypes = [wintypes.LPCWSTR]
GetDriveTypeW.restype = wintypes.UINT

SetFileAttributesW = kernel32.SetFileAttributesW
SetFileAttributesW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD]
SetFileAttributesW.restype = wintypes.BOOL

GetFileAttributesW = kernel32.GetFileAttributesW
GetFileAttributesW.argtypes = [wintypes.LPCWSTR]
GetFileAttributesW.restype = wintypes.DWORD

FILE_ATTRIBUTE_HIDDEN = 0x2
FILE_ATTRIBUTE_SYSTEM = 0x4
FILE_ATTRIBUTE_NORMAL = 0x80
INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF
DRIVE_REMOVABLE = 2

APP_TITLE = "Smart File Protector"
DATA_FILE = "protected_list.json"


# =========================
# Password
# =========================
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


APP_PASSWORD_HASH = hash_password("1234")


def verify_password(input_password: str) -> bool:
    return hash_password(input_password) == APP_PASSWORD_HASH


# =========================
# Helpers
# =========================
def list_removable_drives():
    mask = GetLogicalDrives()
    drives = set()

    for i in range(26):
        if mask & (1 << i):
            letter = chr(ord("A") + i)
            root = f"{letter}:\\"

            if GetDriveTypeW(root) == DRIVE_REMOVABLE:
                drives.add(root)

    return drives


def set_hidden(path: str, hide: bool = True) -> bool:
    path = os.path.abspath(path)
    attrs = GetFileAttributesW(path)

    if attrs == INVALID_FILE_ATTRIBUTES:
        return False

    if hide:
        new_attrs = attrs | FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM
    else:
        new_attrs = attrs & ~FILE_ATTRIBUTE_HIDDEN
        new_attrs = new_attrs & ~FILE_ATTRIBUTE_SYSTEM

        if new_attrs == 0:
            new_attrs = FILE_ATTRIBUTE_NORMAL

    return bool(SetFileAttributesW(path, new_attrs))


def hide_recursively(folder: str, hide: bool = True, max_items: int = 5000) -> int:
    folder = os.path.abspath(folder)
    count = 0

    if set_hidden(folder, hide=hide):
        count += 1

    for root, dirs, files in os.walk(folder):
        for name in dirs:
            if count >= max_items:
                return count

            if set_hidden(os.path.join(root, name), hide=hide):
                count += 1

        for name in files:
            if count >= max_items:
                return count

            if set_hidden(os.path.join(root, name), hide=hide):
                count += 1

    return count


def mask_path(path: str) -> str:
    try:
        clean = path.rstrip("\\/")
        name = os.path.basename(clean)
        parent = os.path.basename(os.path.dirname(clean))

        if parent:
            return f"...\\{parent}\\{name}"

        return f"...\\{name}"
    except Exception:
        return "Protected Item"


def load_protected_items():
    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        return [str(x) for x in data] if isinstance(data, list) else []
    except Exception:
        return []


def save_protected_items(items):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)
    except Exception:
        pass


# =========================
# App
# =========================
class SmartFileProtector:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"{APP_TITLE} - Security Dashboard")
        self.root.geometry("1560x900")
        self.root.minsize(1300, 780)
        self.root.configure(bg="#050816")

        self.protected_items = load_protected_items()
        self.monitoring = False
        self.monitor_thread = None
        self.last_usb_set = set()

        self._style()
        self._build_ui()
        self._refresh_table()

        self.log("Application launched. Authorized access granted.")
        self.log("System ready. Waiting for USB activity.")

        usb_now = list_removable_drives()
        self.last_usb_set = usb_now
        self._set_usb_status(usb_now)

    def _style(self):
        self.style = ttk.Style()

        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        bg = "#050816"
        card = "#111827"
        fg = "#f8fafc"
        muted = "#a3b3c7"

        self.style.configure("TFrame", background=bg)
        self.style.configure("Card.TFrame", background=card)

        self.style.configure(
            "Title.TLabel",
            background=bg,
            foreground=fg,
            font=("Segoe UI", 30, "bold")
        )

        self.style.configure(
            "Sub.TLabel",
            background=bg,
            foreground=muted,
            font=("Segoe UI", 11)
        )

        self.style.configure(
            "CardTitle.TLabel",
            background=card,
            foreground=fg,
            font=("Segoe UI", 13, "bold")
        )

        self.style.configure(
            "CardText.TLabel",
            background=card,
            foreground=muted,
            font=("Segoe UI", 10)
        )

        self.style.configure(
            "MetricValue.TLabel",
            background=card,
            foreground="#ffffff",
            font=("Segoe UI", 24, "bold")
        )

        self.style.configure(
            "MetricLabel.TLabel",
            background=card,
            foreground=muted,
            font=("Segoe UI", 10)
        )

        button_styles = [
            ("Cyan.TButton", "#0891b2", "#0e7490"),
            ("Rose.TButton", "#e11d48", "#be123c"),
            ("Emerald.TButton", "#059669", "#047857"),
            ("Indigo.TButton", "#4f46e5", "#4338ca"),
            ("Slate.TButton", "#475569", "#334155"),
        ]

        for style_name, normal, active in button_styles:
            self.style.configure(
                style_name,
                font=("Segoe UI Semibold", 10),
                padding=(20, 13),
                foreground="white",
                background=normal,
                borderwidth=0,
                focusthickness=0,
                relief="flat"
            )
            self.style.map(
                style_name,
                background=[("active", active), ("disabled", "#334155")],
                foreground=[("disabled", "#94a3b8")]
            )

        self.style.configure(
            "Treeview",
            background="#07111f",
            foreground="#e5e7eb",
            fieldbackground="#07111f",
            rowheight=34,
            font=("Segoe UI", 10),
            borderwidth=0
        )

        self.style.configure(
            "Treeview.Heading",
            background="#172033",
            foreground="white",
            font=("Segoe UI", 10, "bold")
        )

        self.style.map(
            "Treeview",
            background=[("selected", "#0891b2")],
            foreground=[("selected", "white")]
        )

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=18)
        main.pack(fill="both", expand=True)

        header = ttk.Frame(main)
        header.pack(fill="x", pady=(0, 16))

        left_header = ttk.Frame(header)
        left_header.pack(side="left", fill="x", expand=True)

        ttk.Label(
            left_header,
            text=APP_TITLE,
            style="Title.TLabel"
        ).pack(anchor="w")

        ttk.Label(
            left_header,
            text="USB Monitoring • Password Authentication • Automated File Protection • Activity Logging",
            style="Sub.TLabel"
        ).pack(anchor="w", pady=(4, 0))

        self.header_badge = tk.Label(
            header,
            text="SYSTEM READY",
            bg="#0891b2",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=20,
            pady=11
        )
        self.header_badge.pack(side="right", anchor="n")

        metrics = ttk.Frame(main)
        metrics.pack(fill="x", pady=(0, 16))

        self.usb_card = self._metric_card(metrics, "USB Status", "NO USB", "No removable drive detected")
        self.usb_card.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.protect_card = self._metric_card(metrics, "Protection Status", "IDLE", "Files are visible")
        self.protect_card.pack(side="left", fill="x", expand=True, padx=10)

        self.auth_card = self._metric_card(metrics, "Authentication Status", "AUTHORIZED", "Application access granted")
        self.auth_card.pack(side="left", fill="x", expand=True, padx=(10, 0))

        controls = self._card(main, "Security Controls")
        controls.pack(fill="x", pady=(0, 16))

        btnrow = ttk.Frame(controls, style="Card.TFrame")
        btnrow.pack(fill="x")

        self.btn_start = ttk.Button(
            btnrow,
            text="▶ Start Monitoring",
            style="Cyan.TButton",
            command=self.start_monitoring
        )
        self.btn_start.pack(side="left", padx=(0, 10))

        self.btn_stop = ttk.Button(
            btnrow,
            text="■ Stop",
            style="Rose.TButton",
            command=self.stop_monitoring,
            state="disabled"
        )
        self.btn_stop.pack(side="left", padx=(0, 10))

        self.btn_protect = ttk.Button(
            btnrow,
            text="🛡 Protect Now",
            style="Emerald.TButton",
            command=self.protect_now
        )
        self.btn_protect.pack(side="left", padx=(0, 10))

        self.btn_restore = ttk.Button(
            btnrow,
            text="🔓 Restore Files",
            style="Indigo.TButton",
            command=self.restore_files
        )
        self.btn_restore.pack(side="left")

        ttk.Label(
            controls,
            text="Tip: Start monitoring, insert a USB device, and use Protect Now to hide selected sensitive files. Restore requires password authentication.",
            style="CardText.TLabel"
        ).pack(anchor="w", pady=(14, 0))

        body = ttk.Frame(main)
        body.pack(fill="both", expand=True)

        left = ttk.Frame(body)
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        right = ttk.Frame(body)
        right.pack(side="right", fill="both", expand=False)
        right.configure(width=720)
        right.pack_propagate(False)

        items_card = self._card(left, "Protected Items")
        items_card.pack(fill="both", expand=True)

        toolbar = ttk.Frame(items_card, style="Card.TFrame")
        toolbar.pack(fill="x", pady=(0, 12))

        ttk.Button(
            toolbar,
            text="📄 Add File",
            style="Slate.TButton",
            command=self.add_file
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            toolbar,
            text="📁 Add Folder",
            style="Cyan.TButton",
            command=self.add_folder
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            toolbar,
            text="🗑 Remove Selected",
            style="Rose.TButton",
            command=self.remove_selected
        ).pack(side="left")

        table_frame = ttk.Frame(items_card, style="Card.TFrame")
        table_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(
            table_frame,
            columns=("type", "path"),
            show="headings",
            selectmode="extended"
        )
        self.tree.heading("type", text="Type")
        self.tree.heading("path", text="Protected Location (Masked)")
        self.tree.column("type", width=120, anchor="center")
        self.tree.column("path", width=780, anchor="w")

        yscroll = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=yscroll.set)

        self.tree.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")

        log_card = self._card(right, "Activity Log")
        log_card.pack(fill="both", expand=True)

        top = ttk.Frame(log_card, style="Card.TFrame")
        top.pack(fill="x", pady=(0, 8))

        self.log_status = tk.Label(
            top,
            text="● LIVE MONITORING LOG",
            bg="#111827",
            fg="#22d3ee",
            font=("Segoe UI", 10, "bold")
        )
        self.log_status.pack(side="left")

        ttk.Button(
            top,
            text="🧹 Clear Log",
            style="Slate.TButton",
            command=self.clear_log
        ).pack(side="right")

        self.logbox = ScrolledText(
            log_card,
            wrap="word",
            height=70,
            font=("Consolas", 12),
            bg="#020617",
            fg="#dbeafe",
            insertbackground="white",
            relief="flat",
            borderwidth=0
        )
        self.logbox.pack(fill="both", expand=True, pady=(8, 0))
        self.logbox.configure(state="normal")

        self.logbox.tag_config("white", foreground="#f8fafc")
        self.logbox.tag_config("red", foreground="#ff4d6d")
        self.logbox.tag_config("green", foreground="#22c55e")
        self.logbox.tag_config("blue", foreground="#38bdf8")
        self.logbox.tag_config("orange", foreground="#f59e0b")
        self.logbox.tag_config("pink", foreground="#ff66c4")
        self.logbox.tag_config("gray", foreground="#94a3b8")

    def _card(self, parent, title):
        card = ttk.Frame(parent, style="Card.TFrame", padding=16)
        ttk.Label(
            card,
            text=title,
            style="CardTitle.TLabel"
        ).pack(anchor="w", pady=(0, 10))
        return card

    def _metric_card(self, parent, title, value, subtitle):
        card = ttk.Frame(parent, style="Card.TFrame", padding=18)

        ttk.Label(
            card,
            text=title,
            style="CardTitle.TLabel"
        ).pack(anchor="w")

        value_label = ttk.Label(
            card,
            text=value,
            style="MetricValue.TLabel"
        )
        value_label.pack(anchor="w", pady=(14, 2))

        sub_label = ttk.Label(
            card,
            text=subtitle,
            style="MetricLabel.TLabel"
        )
        sub_label.pack(anchor="w")

        card.value_label = value_label
        card.sub_label = sub_label

        return card

    def log(self, msg: str):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        full_msg = f"[{ts}] {msg}\n"

        msg_lower = msg.lower()
        tag = "white"

        if "restore" in msg_lower or "unhidden" in msg_lower:
            tag = "blue"
        elif "protection" in msg_lower or "hidden file" in msg_lower or "hidden folder" in msg_lower:
            tag = "green"
        elif "usb" in msg_lower or "removed" in msg_lower or "inserted" in msg_lower or "detected" in msg_lower:
            tag = "white"
        elif "error" in msg_lower or "failed" in msg_lower or "denied" in msg_lower or "unauthorized" in msg_lower:
            tag = "pink"
        elif "ready" in msg_lower or "launched" in msg_lower:
            tag = "gray"

        self.logbox.insert("end", full_msg, tag)
        self.logbox.see("end")

    def clear_log(self):
        self.logbox.delete("1.0", "end")

    def request_password(self, title="Authentication Required", prompt="Enter password:") -> bool:
        user_pass = askstring(title, prompt, show="*")

        if user_pass is None:
            return False

        return verify_password(user_pass)

    def _refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for p in self.protected_items:
            t = "Folder" if os.path.isdir(p) else "File"
            self.tree.insert("", "end", values=(t, mask_path(p)))

    def _set_usb_status(self, usb_set):
        if not usb_set:
            self.usb_card.value_label.config(text="NO USB")
            self.usb_card.sub_label.config(text="No removable drive detected")
        else:
            drives = ", ".join(sorted(usb_set))
            self.usb_card.value_label.config(text="USB DETECTED")
            self.usb_card.sub_label.config(text=f"Detected: {drives}")

    def _set_protection_status(self, status, subtitle):
        self.protect_card.value_label.config(text=status)
        self.protect_card.sub_label.config(text=subtitle)

    def _set_header_badge(self, text, color):
        self.header_badge.config(text=text, bg=color)

    def add_file(self):
        path = filedialog.askopenfilename(title="Select a file to protect")

        if not path:
            return

        path = os.path.abspath(path)

        if path not in self.protected_items:
            self.protected_items.append(path)
            save_protected_items(self.protected_items)
            self._refresh_table()
            self.log(f"Added file: {mask_path(path)}")

    def add_folder(self):
        path = filedialog.askdirectory(title="Select a folder to protect")

        if not path:
            return

        path = os.path.abspath(path)

        if path not in self.protected_items:
            self.protected_items.append(path)
            save_protected_items(self.protected_items)
            self._refresh_table()
            self.log(f"Added folder: {mask_path(path)}")

    def remove_selected(self):
        sel = self.tree.selection()

        if not sel:
            messagebox.showinfo(APP_TITLE, "Please select an item to remove.")
            return

        selected_indices = [self.tree.index(i) for i in sel]

        removed_items = []
        new_items = []

        for index, path in enumerate(self.protected_items):
            if index in selected_indices:
                removed_items.append(path)
            else:
                new_items.append(path)

        self.protected_items = new_items
        save_protected_items(self.protected_items)
        self._refresh_table()

        for p in removed_items:
            self.log(f"Removed: {mask_path(p)}")

    def protect_now(self):
        if not self.protected_items:
            messagebox.showinfo(APP_TITLE, "No protected items configured. Add files/folders first.")
            return

        self.log("Protection triggered: Hiding selected items...")

        ok_count = 0

        for p in self.protected_items:
            if not os.path.exists(p):
                self.log(f"Skipped not found: {mask_path(p)}")
                continue

            try:
                if os.path.isdir(p):
                    changed = hide_recursively(p, hide=True)
                    ok_count += changed
                    self.log(f"Hidden folder + contents ({changed} items): {mask_path(p)}")
                else:
                    if set_hidden(p, hide=True):
                        ok_count += 1
                        self.log(f"Hidden file: {mask_path(p)}")
                    else:
                        self.log(f"Failed to hide: {mask_path(p)}")

            except Exception as e:
                self.log(f"Error protecting {mask_path(p)}: {e}")

        self._set_protection_status("PROTECTED", f"Total items updated: {ok_count}")
        self.log(f"Protection done. Total items updated: {ok_count}")

    def restore_files(self):
        if not self.protected_items:
            messagebox.showinfo(APP_TITLE, "No protected items in list.")
            return

        allowed = self.request_password(
            title="Restore Authentication",
            prompt="Enter password to restore files:"
        )

        if not allowed:
            messagebox.showerror("Access Denied", "Incorrect password or action cancelled.")
            self.log("Unauthorized restore attempt blocked.")
            return

        self.log("Restore authentication successful.")
        self.log("Restore requested: Unhiding selected items...")

        ok_count = 0

        for p in self.protected_items:
            if not os.path.exists(p):
                self.log(f"Skipped not found: {mask_path(p)}")
                continue

            try:
                if os.path.isdir(p):
                    changed = hide_recursively(p, hide=False)
                    ok_count += changed
                    self.log(f"Unhidden folder + contents ({changed} items): {mask_path(p)}")
                else:
                    if set_hidden(p, hide=False):
                        ok_count += 1
                        self.log(f"Unhidden file: {mask_path(p)}")
                    else:
                        self.log(f"Failed to unhide: {mask_path(p)}")

            except Exception as e:
                self.log(f"Error restoring {mask_path(p)}: {e}")

        self._set_protection_status("IDLE", f"Restored items: {ok_count}")
        self._set_header_badge("SYSTEM READY", "#0891b2")
        self.log(f"Restore done. Total items updated: {ok_count}")

    def start_monitoring(self):
        if self.monitoring:
            return

        self.monitoring = True
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self._set_header_badge("MONITORING ACTIVE", "#0891b2")
        self.log("USB monitoring started.")

        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        self.monitoring = False
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self._set_header_badge("MONITORING STOPPED", "#475569")
        self.log("USB monitoring stopped.")

    def _monitor_loop(self):
        while self.monitoring:
            try:
                usb_now = list_removable_drives()
                inserted = usb_now - self.last_usb_set
                removed = self.last_usb_set - usb_now

                if inserted or removed:
                    self.last_usb_set = usb_now
                    self.root.after(0, self._set_usb_status, usb_now)

                if inserted:
                    for drive in sorted(inserted):
                        self.root.after(0, self.log, f"USB inserted: {drive}")
                        self.root.after(0, self.log, f"USB detected successfully: {drive}")

                if removed:
                    self.root.after(
                        0,
                        self.log,
                        f"USB removed: {', '.join(sorted(removed))}"
                    )

            except Exception as e:
                self.root.after(0, self.log, f"Monitor error: {e}")

            time.sleep(1.5)


def startup_auth(root: tk.Tk, max_attempts: int = 3) -> bool:
    for attempt in range(max_attempts):
        user_pass = askstring(
            "Application Login",
            f"Enter application password:\nAttempt {attempt + 1} of {max_attempts}",
            show="*"
        )

        if user_pass is None:
            return False

        if verify_password(user_pass):
            return True

        messagebox.showerror("Access Denied", "Incorrect password.")

    return False


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    authenticated = startup_auth(root, max_attempts=3)

    if authenticated:
        root.deiconify()
        app = SmartFileProtector(root)
        root.mainloop()
    else:
        messagebox.showerror(
            "Access Denied",
            "Too many failed attempts or login cancelled."
        )
        root.destroy()