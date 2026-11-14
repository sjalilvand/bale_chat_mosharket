# -*- coding: utf-8 -*-
"""رابط گرافیکی Bale Chat Mosharket

دریافت، دسته‌بندی و ساخت گزارش HTML از پیام‌های گروه‌های پیام‌رسان بله
(بر پایه API رسمی ربات‌های بله — docs.bale.ai)
"""

import csv
import json
import os
import queue
import threading
import time
import webbrowser
from collections import Counter

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from bale_client import BaleBotError, BaleClient
from categorizer import Categorizer, FALLBACK, parse_rules
from report import build_report
from storage import (
    import_csv,
    import_json,
    load_messages,
    make_message,
    merge_messages,
    save_messages,
)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH = os.path.join(APP_DIR, "settings.json")
MESSAGES_PATH = os.path.join(APP_DIR, "messages.json")

DEFAULT_RULES = """اطلاعیه: اطلاعیه، اعلام، هماهنگ، توجه داشته باشید، مهم
جلسه و قرار: جلسه، قرار، حضوری، آنلاین
پرسش و پاسخ: ؟, ?, چرا، چطور، چگونه، سوال، سؤال، مشکل، راهنمایی
سفارش و امور مالی: سفارش، خرید، قیمت، فاکتور، پرداخت، تخفیف، واریز
تشکر و تعامل: ممنون، تشکر، مرسی، عالی، دست شما درد نکند"""

HINT = "#6b7280"


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Bale Chat Mosharket — دسته‌بندی پیام‌های گروه بله")
        self.root.geometry("820x580")
        self.root.minsize(780, 540)

        self.q = queue.Queue()
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.collector = None
        self.session_count = 0
        self.cat_counter = Counter()
        self.chat_id = None
        self.chat_title = ""

        self.messages = load_messages(MESSAGES_PATH)
        self.seen_updates = {
            m.get("update_id") for m in self.messages if m.get("update_id") is not None
        }

        self.settings = self._load_settings()
        self.categorizer = Categorizer(
            parse_rules(self.settings.get("rules") or DEFAULT_RULES)
        )

        self._build_ui()
        self._apply_settings()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(150, self._poll_queue)

    def run(self):
        self.root.mainloop()

    # ---------------- تنظیمات ----------------

    def _load_settings(self):
        try:
            with open(SETTINGS_PATH, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except (OSError, json.JSONDecodeError):
            pass
        return {}

    def _save_settings(self):
        data = {
            "token": self.token_var.get().strip() if self.save_token_var.get() else "",
            "interval": int(self.interval_var.get() or 20),
            "chat_id": self.chat_id,
            "chat_title": self.chat_title,
            "rules": self.rules_text.get("1.0", "end").rstrip(),
            "report_path": self.report_path_var.get().strip(),
        }
        try:
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def _apply_settings(self):
        if self.settings.get("token"):
            self.token_var.set(self.settings["token"])
            self.save_token_var.set(True)
        self.interval_var.set(int(self.settings.get("interval") or 20))
        if self.settings.get("chat_id") is not None:
            self.chat_id = self.settings["chat_id"]
            self.chat_title = self.settings.get("chat_title") or ""
        self.rules_text.insert("1.0", self.settings.get("rules") or DEFAULT_RULES)
        self.report_path_var.set(self.settings.get("report_path") or "report.html")
        self._update_selected_chat_label()
        self._update_counts()

    # ---------------- ساخت رابط ----------------

    def _build_ui(self):
        self.token_var = tk.StringVar()
        self.save_token_var = tk.BooleanVar(value=False)
        self.interval_var = tk.IntVar(value=20)
        self.report_path_var = tk.StringVar(value="report.html")
        self.open_report_var = tk.BooleanVar(value=True)
        self.manual_chat_var = tk.StringVar()
        self.selected_chat_var = tk.StringVar(value="هیچ گروهی انتخاب نشده است")
        self.rules_info_var = tk.StringVar(
            value="قالب هر خط:  نام دسته: کلیدواژه۱، کلیدواژه۲"
        )
        self.status_var = tk.StringVar(value="آماده")
        self.counts_var = tk.StringVar(value="")

        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=10, pady=(10, 6))

        self._tab_bot(nb)
        self._tab_group(nb)
        self._tab_rules(nb)
        self._tab_collect(nb)
        self._tab_report(nb)

        self.status_label = tk.Label(
            self.root, textvariable=self.status_var, anchor="e",
            fg="#0b7a55", font=("TkDefaultFont", 9)
        )
        self.status_label.pack(fill="x", padx=14, pady=(0, 8))

    def _hint(self, parent, text):
        return tk.Label(
            parent, text=text, fg=HINT, justify="right", wraplength=740,
            anchor="e"
        )

    def _tab_bot(self, nb):
        tab = ttk.Frame(nb, padding=18)
        nb.add(tab, text=" تنظیمات ربات ")

        ttk.Label(tab, text="توکن ربات بله (از BotFather):").pack(anchor="e")
        token_row = ttk.Frame(tab)
        token_row.pack(fill="x", pady=(4, 2))
        self.token_entry = ttk.Entry(token_row, textvariable=self.token_var, show="*")
        self.token_entry.pack(side="right", fill="x", expand=True)

        ttk.Checkbutton(
            tab,
            text="ذخیره توکن روی این سیستم (در settings.json — به مخزن گیت ارسال نمی‌شود)",
            variable=self.save_token_var,
        ).pack(anchor="e", pady=(0, 10))

        row2 = ttk.Frame(tab)
        row2.pack(fill="x", pady=6)
        ttk.Label(row2, text="فاصله بررسی پیام‌های جدید (ثانیه):").pack(side="right")
        ttk.Spinbox(
            row2, from_=5, to=60, width=6, textvariable=self.interval_var
        ).pack(side="right", padx=8)

        btns = ttk.Frame(tab)
        btns.pack(fill="x", pady=14)
        ttk.Button(btns, text="تست اتصال", command=self._test_connection).pack(
            side="right", padx=4
        )
        ttk.Button(btns, text="ذخیره تنظیمات", command=self._save_settings).pack(
            side="right", padx=4
        )

        self._hint(
            tab,
            "۱) در بله به BotFather@ پیام دهید و با دستور /newbot ربات بسازید.\n"
            "۲) توکن دریافتی (مثل 123456:ABC-DEF) را در کادر بالا وارد کنید.\n"
            "۳) ربات را به گروه اضافه کنید؛ برای اطمینان از دیدن همه پیام‌ها آن را «ادمین» گروه کنید.",
        ).pack(anchor="e", pady=(14, 0))

    def _tab_group(self, nb):
        tab = ttk.Frame(nb, padding=18)
        nb.add(tab, text=" گروه ")

        ttk.Button(
            tab, text="شناسایی گروه‌ها از پیام‌های اخیر", command=self._identify_groups
        ).pack(anchor="e")
        self._hint(
            tab,
            "ربات فقط گفتگوهایی را می‌بیند که در ۲۴ ساعت اخیر در آنها پیامی ردوبدل شده است؛ "
            "اگر گروه در لیست نیامد، در خود گروه یک پیام (مثلاً سلام) بفرستید و دوباره تلاش کنید.",
        ).pack(anchor="e", pady=(6, 10))

        cols = ("chat_id", "title", "type")
        self.tree = ttk.Treeview(tab, columns=cols, show="headings", height=8)
        self.tree.heading("chat_id", text="شناسه")
        self.tree.heading("title", text="عنوان")
        self.tree.heading("type", text="نوع")
        self.tree.column("chat_id", width=170, anchor="center")
        self.tree.column("title", width=380, anchor="e")
        self.tree.column("type", width=90, anchor="center")
        self.tree.pack(fill="both", expand=True)

        ttk.Button(tab, text="انتخاب این گروه", command=self._select_group).pack(
            anchor="e", pady=8
        )

        sep = ttk.Separator(tab)
        sep.pack(fill="x", pady=8)

        manual = ttk.Frame(tab)
        manual.pack(fill="x")
        ttk.Label(manual, text="افزودن دستی با شناسه گروه:").pack(side="right")
        ttk.Entry(manual, textvariable=self.manual_chat_var, width=24).pack(
            side="right", padx=8
        )
        ttk.Button(manual, text="افزودن", command=self._add_manual_chat).pack(
            side="right"
        )

        tk.Label(
            tab,
            textvariable=self.selected_chat_var,
            fg="#0b7a55",
            font=("TkDefaultFont", 10, "bold"),
        ).pack(anchor="e", pady=(10, 0))
        self._hint(
            tab,
            "اگر هیچ گروهی انتخاب نشود، پیام‌های همه گروه‌ها (به‌جز چت خصوصی) ذخیره می‌شوند.",
        ).pack(anchor="e")

    def _tab_rules(self, nb):
        tab = ttk.Frame(nb, padding=18)
        nb.add(tab, text=" دسته‌بندی ")

        self._hint(
            tab,
            "هر خط یک دسته است. اگر هر کلیدواژه داخل متن پیام باشد، پیام به آن دسته می‌رود؛ "
            "پیام‌های بدون تطبیق به دسته «سایر» می‌روند.",
        ).pack(anchor="e", pady=(0, 8))

        frame = ttk.Frame(tab)
        frame.pack(fill="both", expand=True)
        self.rules_text = tk.Text(frame, height=12, undo=True, font=("TkFixedFont", 11))
        scroll = ttk.Scrollbar(frame, command=self.rules_text.yview)
        self.rules_text.configure(yscrollcommand=scroll.set)
        self.rules_text.pack(side="right", fill="both", expand=True)
        scroll.pack(side="left", fill="y")

        btns = ttk.Frame(tab)
        btns.pack(fill="x", pady=10)
        ttk.Button(
            btns, text="اعمال و ذخیره دسته‌بندی", command=self._apply_rules_clicked
        ).pack(side="right", padx=4)
        ttk.Button(
            btns, text="بازگرداندن قوانین پیش‌فرض", command=self._reset_rules
        ).pack(side="right", padx=4)

        tk.Label(tab, textvariable=self.rules_info_var, fg="#0b7a55").pack(anchor="e")

    def _tab_collect(self, nb):
        tab = ttk.Frame(nb, padding=18)
        nb.add(tab, text=" دریافت پیام ")

        btns = ttk.Frame(tab)
        btns.pack(fill="x", pady=(0, 10))
        self.start_btn = ttk.Button(
            btns, text="شروع دریافت", command=self._start_collect
        )
        self.start_btn.pack(side="right", padx=4)
        self.stop_btn = ttk.Button(
            btns, text="توقف", command=self._stop_collect, state="disabled"
        )
        self.stop_btn.pack(side="right", padx=4)

        self.counts_label = tk.Label(
            tab,
            textvariable=self.counts_var,
            justify="right",
            anchor="e",
            font=("TkDefaultFont", 10),
        )
        self.counts_label.pack(fill="x", pady=6)

        ttk.Separator(tab).pack(fill="x", pady=10)

        ttk.Label(tab, text="ورود پیام‌های قدیمی:").pack(anchor="e")
        imp = ttk.Frame(tab)
        imp.pack(fill="x", pady=4)
        ttk.Button(
            imp, text="ورود فایل CSV (خروجی bale_chat_backup)", command=lambda: self._import_files("csv")
        ).pack(side="right", padx=4)
        ttk.Button(
            imp, text="ورود فایل JSON", command=lambda: self._import_files("json")
        ).pack(side="right", padx=4)

        self._hint(
            tab,
            "ربات‌ها به تاریخچه قبل از ورودشان دسترسی ندارند. برای پیام‌های قدیمی گروه، ابتدا با ابزار "
            "bale_chat_backup (نسخه وب بله) خروجی CSV بگیرید و فایل‌های «بخش_*.csv» را همین‌جا وارد کنید؛ "
            "سپس در تب «گزارش HTML» گزارش کامل قدیمی + جدید را بسازید.",
        ).pack(anchor="e", pady=(8, 0))

        self._hint(
            tab,
            f"محل ذخیره پیام‌ها: {MESSAGES_PATH}",
        ).pack(anchor="e", pady=(8, 0))

    def _tab_report(self, nb):
        tab = ttk.Frame(nb, padding=18)
        nb.add(tab, text=" گزارش HTML ")

        ttk.Label(tab, text="نام فایل خروجی:").pack(anchor="e")
        ttk.Entry(tab, textvariable=self.report_path_var).pack(
            fill="x", pady=(4, 8)
        )
        ttk.Checkbutton(
            tab, text="پس از ساخت، گزارش در مرورگر باز شود", variable=self.open_report_var
        ).pack(anchor="e")

        ttk.Button(tab, text="ساخت گزارش HTML", command=self._build_report).pack(
            anchor="e", pady=12
        )

        self._hint(
            tab,
            "گزارش شامل آمار کلی، نمودار توزیع دسته‌ها و پیام‌های هر دسته است؛ "
            "تاریخ‌ها به شمسی نمایش داده می‌شوند و فایل خروجی تک‌فایلی و قابل ارسال است.",
        ).pack(anchor="e")

    # ---------------- وضعیت و شمارنده‌ها ----------------

    def _set_status(self, text, warn=False):
        self.status_var.set(text)
        self.status_label.config(fg="#b91c1c" if warn else "#0b7a55")

    def _update_counts(self):
        cats = Counter(m.get("category") or FALLBACK for m in self.messages)
        detail = " | ".join(f"{k}: {v}" for k, v in cats.most_common()) or "—"
        self.counts_var.set(
            f"کل پیام‌های ذخیره‌شده: {len(self.messages)}  |  دریافت این نشست: {self.session_count}\n"
            f"{detail}"
        )

    def _update_selected_chat_label(self):
        if self.chat_id is None:
            self.selected_chat_var.set(
                "هیچ گروهی انتخاب نشده — پیام‌های همه گروه‌ها ذخیره می‌شود"
            )
        else:
            self.selected_chat_var.set(
                f"گروه انتخاب‌شده: {self.chat_title} (شناسه: {self.chat_id})"
            )

    # ---------------- اکشن‌ها ----------------

    def _test_connection(self):
        token = self.token_var.get().strip()
        if not token:
            messagebox.showwarning("توکن ربات", "توکن ربات را وارد کنید.")
            return

        def work():
            try:
                me = BaleClient(token).get_me()
                self.q.put(
                    (
                        "status",
                        f"اتصال موفق — ربات: {me.get('first_name', '')} (@{me.get('username', '')})",
                    )
                )
            except BaleBotError as exc:
                self.q.put(("error", f"اتصال ناموفق: {exc}"))

        threading.Thread(target=work, daemon=True).start()

    def _identify_groups(self):
        token = self.token_var.get().strip()
        if not token:
            messagebox.showwarning(
                "توکن ربات", "ابتدا در تب «تنظیمات ربات» توکن را وارد کنید."
            )
            return

        def work():
            try:
                updates = BaleClient(token).get_updates(offset=0, limit=100, timeout=0) or []
                chats = {}
                for upd in updates:
                    src = upd.get("message") or upd.get("edited_message")
                    if not src:
                        continue
                    chat = src.get("chat") or {}
                    key = chat.get("id")
                    if key is None:
                        continue
                    chats[key] = (
                        str(chat.get("title") or chat.get("first_name") or key),
                        str(chat.get("type") or ""),
                    )
                self.q.put(("groups", sorted(chats.items())))
            except BaleBotError as exc:
                self.q.put(("error", str(exc)))

        self._set_status("در حال شناسایی گروه‌ها...")
        threading.Thread(target=work, daemon=True).start()

    def _select_group(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("انتخاب گروه", "ابتدا یک ردیف از جدول انتخاب کنید.")
            return
        values = self.tree.item(sel[0], "values")
        try:
            chat_id = int(values[0])
        except (ValueError, TypeError, IndexError):
            messagebox.showerror("خطا", "شناسه گفتگو معتبر نیست.")
            return
        self.chat_id = chat_id
        self.chat_title = values[1] if len(values) > 1 else ""
        self._update_selected_chat_label()
        self._save_settings()
        self._set_status(f"گروه «{self.chat_title}» انتخاب شد.")

    def _add_manual_chat(self):
        raw = self.manual_chat_var.get().strip()
        if not raw:
            messagebox.showwarning(
                "شناسه گروه", "شناسه گروه را وارد کنید (معمولاً عددی منفی است)."
            )
            return
        try:
            chat_id = int(raw)
        except ValueError:
            messagebox.showwarning(
                "شناسه نامعتبر", "شناسه گروه باید عدد باشد؛ مثال: -100123456789"
            )
            return

        def work():
            title, ctype = f"گروه {chat_id}", "group"
            token = self.token_var.get().strip()
            if token:
                try:
                    info = BaleClient(token).get_chat(chat_id)
                    title = str(info.get("title") or info.get("first_name") or title)
                    ctype = str(info.get("type") or ctype)
                except BaleBotError as exc:
                    self.q.put(
                        ("status_warn", f"دریافت مشخصات گروه ناموفق بود ({exc})؛ با عنوان پیش‌فرض اضافه شد.")
                    )
            self.q.put(("chat_selected", (chat_id, title, ctype)))

        threading.Thread(target=work, daemon=True).start()

    def _apply_rules_clicked(self):
        self._apply_rules()
        self._save_settings()

    def _apply_rules(self, silent=False):
        rules = parse_rules(self.rules_text.get("1.0", "end"))
        if not rules:
            if not silent:
                messagebox.showwarning(
                    "قوانین",
                    "هیچ قانون معتبری پیدا نشد.\nقالب صحیح: نام دسته: کلیدواژه۱، کلیدواژه۲",
                )
            return False
        self.categorizer = Categorizer(rules)
        with self.lock:
            for m in self.messages:
                text = m.get("text") or ""
                m["category"] = self.categorizer.categorize(text) if text else FALLBACK
            try:
                save_messages(self.messages, MESSAGES_PATH)
            except OSError:
                pass
        self.rules_info_var.set(
            f"{len(rules)} دسته فعال شد و بر {len(self.messages)} پیام ذخیره‌شده اعمال گردید."
        )
        self._update_counts()
        return True

    def _reset_rules(self):
        self.rules_text.delete("1.0", "end")
        self.rules_text.insert("1.0", DEFAULT_RULES)

    def _import_files(self, kind):
        if kind == "csv":
            paths = filedialog.askopenfilenames(
                title="انتخاب فایل‌های CSV",
                filetypes=[("CSV", "*.csv"), ("همه فایل‌ها", "*.*")],
            )
            loader = import_csv
        else:
            paths = filedialog.askopenfilenames(
                title="انتخاب فایل‌های JSON",
                filetypes=[("JSON", "*.json"), ("همه فایل‌ها", "*.*")],
            )
            loader = import_json
        if not paths:
            return
        total = 0
        errors = []
        with self.lock:
            for p in paths:
                try:
                    total += merge_messages(self.messages, loader(p))
                except (OSError, ValueError, csv.Error) as exc:
                    errors.append(f"{os.path.basename(p)}: {exc}")
            save_messages(self.messages, MESSAGES_PATH)
        self._update_counts()
        if errors:
            messagebox.showerror("خطای ورود فایل", "\n".join(errors))
        messagebox.showinfo(
            "ورود پیام‌ها", f"{total} پیام جدید از {len(paths)} فایل وارد شد."
        )

    # ---------------- حلقه دریافت ----------------

    def _start_collect(self):
        if self.collector and self.collector.is_alive():
            return
        token = self.token_var.get().strip()
        if not token:
            messagebox.showwarning(
                "توکن ربات", "ابتدا در تب «تنظیمات ربات» توکن را وارد کنید."
            )
            return
        self._apply_rules(silent=True)
        self._save_settings()
        self.stop_event.clear()
        self.collector = threading.Thread(
            target=self._collector_worker, args=(token,), daemon=True
        )
        self.collector.start()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self._set_status("در حال دریافت پیام‌ها...")

    def _stop_collect(self):
        if self.collector and self.collector.is_alive():
            self.stop_event.set()
            self._set_status("در حال توقف (حداکثر یک دقیقه)...")
            self.stop_btn.config(state="disabled")

    def _toggle_running(self, running):
        self.start_btn.config(state="normal" if not running else "disabled")
        self.stop_btn.config(state="disabled" if not running else "normal")

    def _collector_worker(self, token):
        try:
            client = BaleClient(token)
            me = client.get_me()
            self.q.put(
                (
                    "status",
                    f"متصل شد — ربات: {me.get('first_name', '')} (@{me.get('username', '')})",
                )
            )
        except BaleBotError as exc:
            self.q.put(("error", f"اتصال ناموفق: {exc}"))
            self.q.put(("stopped", None))
            return

        try:
            poll = max(5, min(60, int(self.interval_var.get() or 20)))
        except (ValueError, tk.TclError):
            poll = 20

        offset = 0
        while not self.stop_event.is_set():
            try:
                updates = client.get_updates(offset=offset, limit=100, timeout=poll) or []
            except BaleBotError as exc:
                self.q.put(("error", f"{exc} — تلاش مجدد پس از ۵ ثانیه"))
                for _ in range(50):
                    if self.stop_event.is_set():
                        break
                    time.sleep(0.1)
                continue

            for upd in updates:
                uid = upd.get("update_id")
                if uid is not None:
                    if uid < offset:
                        continue
                    if uid in self.seen_updates:
                        offset = uid + 1
                        continue
                    offset = uid + 1

                src = upd.get("message") or upd.get("edited_message")
                if not src:
                    continue
                chat = src.get("chat") or {}
                chat_id = chat.get("id")
                if self.chat_id is not None:
                    if chat_id != self.chat_id:
                        continue
                elif chat.get("type") == "private":
                    continue

                text = str(src.get("text") or src.get("caption") or "").strip()
                sender = src.get("from") or {}
                new_msg = make_message(
                    message_id=src.get("message_id"),
                    update_id=uid,
                    sender_name=sender.get("first_name", ""),
                    username=sender.get("username", ""),
                    sender_id=sender.get("id"),
                    chat_id=chat_id,
                    chat_title=chat.get("title", ""),
                    text=text,
                    date=src.get("date"),
                )
                new_msg["category"] = (
                    self.categorizer.categorize(text) if text else FALLBACK
                )
                with self.lock:
                    self.messages.append(new_msg)
                    if uid is not None:
                        self.seen_updates.add(uid)
                    try:
                        save_messages(self.messages, MESSAGES_PATH)
                    except OSError as exc:
                        self.q.put(("error", f"ذخیره فایل پیام‌ها ناموفق بود: {exc}"))
                self.q.put(("msg", new_msg["category"]))

        self.q.put(("stopped", None))

    # ---------------- گزارش ----------------

    def _build_report(self):
        self._apply_rules(silent=True)
        with self.lock:
            msgs = list(self.messages)
        if not msgs:
            messagebox.showwarning(
                "گزارش خالی",
                "هنوز پیامی ذخیره نشده است.\nابتدا از تب «دریافت پیام» شروع کنید "
                "یا فایل CSV پیام‌های قدیمی را وارد کنید.",
            )
            return
        out = self.report_path_var.get().strip() or "report.html"
        try:
            path = build_report(msgs, out, group_title=self.chat_title or None)
        except OSError as exc:
            messagebox.showerror("خطا", f"ساخت گزارش ناموفق بود: {exc}")
            return
        self._set_status(f"گزارش ساخته شد: {path}")
        if self.open_report_var.get():
            webbrowser.open("file://" + path.replace("\\", "/"))
        else:
            messagebox.showinfo("گزارش ساخته شد", f"مسیر فایل:\n{path}")

    # ---------------- صف رویدادها ----------------

    def _poll_queue(self):
        try:
            while True:
                ev, payload = self.q.get_nowait()
                if ev == "status":
                    self._set_status(payload)
                elif ev == "status_warn":
                    self._set_status(payload, warn=True)
                elif ev == "error":
                    self._set_status(payload, warn=True)
                elif ev == "msg":
                    self.session_count += 1
                    self.cat_counter[payload] += 1
                    self._update_counts()
                elif ev == "groups":
                    self._show_groups(payload)
                elif ev == "chat_selected":
                    chat_id, title, ctype = payload
                    self.chat_id = chat_id
                    self.chat_title = title
                    found = False
                    for item in self.tree.get_children():
                        vals = self.tree.item(item, "values")
                        if vals and str(vals[0]) == str(chat_id):
                            found = True
                            break
                    if not found:
                        self.tree.insert(
                            "", "end", values=(str(chat_id), title, ctype)
                        )
                    self._update_selected_chat_label()
                    self._save_settings()
                    self._set_status(f"گروه «{title}» انتخاب شد.")
                elif ev == "stopped":
                    self._toggle_running(False)
                    if not self.stop_event.is_set():
                        self.stop_event.set()
                    self._set_status("دریافت پیام متوقف شد.")
        except queue.Empty:
            pass
        self.root.after(150, self._poll_queue)

    def _show_groups(self, chats):
        self.tree.delete(*self.tree.get_children())
        for cid, (title, ctype) in chats:
            self.tree.insert("", "end", values=(str(cid), title, ctype))
        if not chats:
            self._set_status(
                "هیچ گفتگویی در ۲۴ ساعت اخیر پیدا نشد؛ یک پیام در گروه بفرستید و دوباره تلاش کنید.",
                warn=True,
            )
        else:
            self._set_status(
                f"{len(chats)} گفتگو پیدا شد؛ یکی را انتخاب و «انتخاب این گروه» را بزنید."
            )

    # ---------------- بستن برنامه ----------------

    def _on_close(self):
        self.stop_event.set()
        self._save_settings()
        with self.lock:
            try:
                save_messages(self.messages, MESSAGES_PATH)
            except OSError:
                pass
        self.root.destroy()


def main():
    App().run()


if __name__ == "__main__":
    main()
