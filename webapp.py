# -*- coding: utf-8 -*-
"""Bale Chat Mosharket — نسخه وب ۵ (Flask)

داشبورد گرافیکی مدرن در مرورگر برای دریافت، دسته‌بندی و ساخت گزارش HTML
از پیام‌های گروه‌های پیام‌رسان بله، همراه با نمایش زنده روند پیشرفت.

امکانات نسخه ۵:
    - حذف کامل پیام‌های نمونه/تستی: دکمه و اندپوینت «پیام نمونه» کلاً برداشته
      شد و پیام‌های نمونه قدیمیِ باقی‌مانده در پایگاه داده، هنگام اجرا خودکار
      پیدا و حذف می‌شوند
    - دسته‌بندی بر اساس داده‌های موجود: دسته‌های جدید حوزه مشارکت (اطلاعیه و
      ابلاغیه، جلسه و قرار، گزارش عملکرد، هماهنگی و برنامه‌ریزی، پرسش و پاسخ،
      درخواست و پیگیری، تشکر و تعامل، سفارش و امور مالی) + پیام‌های فقط عکس
      به دسته «عکس و مستندات» می‌روند؛ دسته‌های پیام‌های قبلی هنگام اجرا
      به‌روز می‌شوند (اگر قوانین سفارشی ذخیره نشده باشد)
    - گزارش تعاملی نسخه ۵: گروه‌بندی و مرتب‌سازی دلخواه (موضوع / تاریخ ارسال
      شمسی / فرستنده)، فیلتر تاریخ، حالت انتخاب و حذف گروهی، حذف تک پیام با
      همگام‌سازی به پایگاه داده، حالت ویرایش (متن، عنوان، «موضوع گزارش» و دسته
      هر پیام)، ذخیره نسخه ویرایش‌شده و خروجی پاورپوینت با ۴ تم، فرمت ۱۶:۹ یا
      ۴:۳ و شامل عکس‌ها (کتابخانه داخل فایل گزارش جاسازی شده — آفلاین)
    - اندپوینت‌های جدید: POST /api/messages/delete (حذف پیام‌های انتخابی از
      پایگاه داده) و POST /api/messages/category (تغییر دسته از داخل گزارش)

امکانات نسخه ۴.۶:
    - «گرفتن خروجی جداگانه»: هر بار یک فایل HTML جدید با تاریخ و ساعت ساخته
      می‌شود و در فهرست «خروجی‌ها» باقی می‌ماند (حذف تک‌تک هم ممکن است)
    - «پاک‌سازی پیام‌های قبلی»: شروع دور جدید — حذف همه پیام‌های ذخیره‌شده
      با گزینه‌های اختیاری: حذف آرشیو خام و عکس‌ها، حذف خروجی‌های قبلی،
      رد کردن پیام‌های موجود در صف سرور بله و همگام‌سازی دوباره بعد از پاک‌سازی
    - گزارش HTML تعاملی: جست‌وجوی زنده، فیلتر چندگانه دسته‌ها/فرستنده/گروه،
      فیلتر «فقط عکس‌دار»، حذف هر پیام از نمایش (✕) و پیوند «در پاسخ به»
      با پرش و هایلایت پیام مرتبط

امکانات نسخه ۴.۵:
    - به‌روزرسانی خودکار گزارش HTML با رسیدن «هر» پیام جدید (حتی در دریافت زنده) —
      دیگر هیچ‌وقت گزارش کهنه/خالی نشان داده نمی‌شود
    - بنر هشدار شفاف در داشبورد وقتی صف سرور بله خالی است (با دو راه بازیابی)
    - دکمه «دانلود فایل پشتیبان داده‌ها» برای انتقال امن بین پوشه‌ها و نسخه‌ها
    - ورود هوشمند: فایل پشتیبان برنامه، آرشیو خام نسخه قبلی و messages.json
      همه با یک دکمه پذیرفته می‌شوند (با دانلود عکس‌ها و به‌روزرسانی گزارش)

امکانات نسخه ۴.۴:
    - همگام‌سازی خودکار به‌محض اجرا/اتصال: اول «همه» پیام‌های قبلی موجود در بات
      خوانده می‌شود (متن، عکس، کپشن، کامنت، بازنشر — بدون فیلتر گروه)، در پایان
      گزارش HTML خودکار ساخته می‌شود و بعد دریافت زنده ادامه پیدا می‌کند
    - بازیابی خودکار پیام‌های ذخیره‌نشده از آرشیو خام هنگام شروع
    - نمایش مرحله جاری در داشبورد (خواندن پیام‌های قبلی / دریافت زنده)
    - بایگانی خام (raw_updates.json): هر آپدیت قبل از هر پردازشی ذخیره می‌شود؛
      حتی اگر برنامه وسط کار خراب شود هیچ پیامی گم نمی‌شود و با دکمه
      «بازیابی از آرشیو خام» می‌توان همه‌چیز را بازسازی کرد
    - offset ماندگار در settings.json: با ری‌استارت برنامه پیام‌ها
      نه تکرار می‌شوند و نه گم می‌شوند
    - تأییدیه فوری ذخیره در چت خصوصی ربات (کاربر می‌بیند ذخیره شده)
    - خواندن همه انواع پیام: عکس، آلبوم، ویدیو، ویس، فایل، کپشن،
      کامنت‌ها (پاسخ‌ها)، بازنشرها و پیام‌های کانال
    - دانلود خودکار عکس‌ها و نمایش آن‌ها در داشبورد و گزارش HTML
    - ذخیره پیام‌هایی که به ربات فوروارد می‌شوند (چت خصوصی) — همیشه بدون فیلتر
    - انتخاب خودکار پورت آزاد (5000 تا 5009) تا دو نسخه با هم تداخل نکنند

اجرا:
    python main.py        →  http://127.0.0.1:5000 (یا اولین پورت آزاد)
"""

import json
import os
import tempfile
import threading
import time
import webbrowser
from collections import Counter

from flask import Flask, jsonify, render_template, request, send_from_directory

from bale_client import BaleBotError, BaleClient
from categorizer import (
    DEFAULT_RULES,
    Categorizer,
    FALLBACK,
    categorize_message,
    parse_rules,
)
from collector import normalize_member_update, normalize_update
from jalali import format_ts, now_str
from report import build_report
from version import APP_NAME, VERSION, VERSION_LABEL
from storage import (
    import_csv,
    import_json,
    load_messages,
    merge_messages,
    save_json,
    save_messages,
)

BASE = os.path.dirname(os.path.abspath(__file__))
MESSAGES_PATH = os.path.join(BASE, "messages.json")
SETTINGS_PATH = os.path.join(BASE, "settings.json")
RAW_PATH = os.path.join(BASE, "raw_updates.json")
EXPORTS_PATH = os.path.join(BASE, "exports.json")
MEDIA_DIR = os.path.join(BASE, "media")
OUTPUT_DIR = os.path.join(BASE, "output")

GUIDE_TEXT = (
    "سلام! پیام‌های شما ذخیره می‌شود.\n\n"
    "برای خواندن همه پیام‌های قبلی، در داشبورد برنامه دکمه «خواندن همه پیام‌های بات + "
    "ساخت خودکار گزارش HTML» را بزنید.\n"
    "فوروارد پیام‌های قدیمی گروه به این چت کاملاً درست است؛ متن، عکس، کپشن و کامنت‌ها همه ذخیره می‌شوند."
)



TYPE_LABELS = {
    "private": "چت خصوصی",
    "group": "گروه",
    "supergroup": "گروه",
    "channel": "کانال",
}

# قوانین پیش‌فرض قدیم (نسخه‌های قبل از ۵) — برای تشخیص اینکه کاربر هرگز
# قوانین سفارشی ذخیره نکرده و دسته‌ها باید با قوانین جدید به‌روز شوند
OLD_DEFAULT_RULES = """اطلاعیه: اطلاعیه، اعلام، هماهنگ، توجه داشته باشید، مهم
جلسه و قرار: جلسه، قرار، حضوری، آنلاین
پرسش و پاسخ: ؟, ?, چرا، چطور، چگونه، سوال، سؤال، مشکل، راهنمایی
سفارش و امور مالی: سفارش، خرید، قیمت، فاکتور، پرداخت، تخفیف، واریز
تشکر و تعامل: ممنون، تشکر، مرسی، عالی، دست شما درد نکند"""

# ---------- پیام‌های نمونه (نسخه ۵: کاملاً حذف شدند) ----------
#
# نسخه‌های قبل دکمه «افزودن پیام نمونه» داشتند که داده تستی به پایگاه داده
# می‌ریخت. طبق درخواست کاربر، این قابلیت کلاً حذف شد و امضای همان پیام‌های
# نمونه اینجا نگه داشته می‌شود تا اگر در پایگاه داده کاربر باقی مانده باشند،
# هنگام اجرای نسخه ۵ به‌طور خودکار پیدا و حذف شوند.

DEMO_TITLE = "گروه مشارکت های مردمی (نمونه)"

DEMO_SIGNATURES = {
    ("علی رضایی", "اعلامیه: جلسه هماهنگی گروه فردا ساعت ۱۰ برگزار می‌شود"),
    ("مریم احمدی", "سلام، چطور می‌توانم در پروژه محله شرکت کنم؟"),
    ("حسین کریمی", "ممنون از اطلاع‌رسانی، حتماً حضور دارم"),
    ("زهرا موسوی", "سفارش بنرهای همایش را ثبت کردم، فاکتور را می‌فرستم"),
    ("علی رضایی", "توجه داشته باشید مهلت ثبت‌نام تا پنجشنبه است"),
    ("سارا نوری", "متن گزارش فعالیت‌های مردمی را کجا بفرستم؟"),
    ("حسین کریمی", "جلسه با شهرداری به‌صورت آنلاین خواهد بود"),
    ("مریم احمدی", "عالی بود، دست شما درد نکند"),
    ("زهرا موسوی", "قیمت پوسترها با تخفیف توافق شد"),
    ("سارا نوری", "قرار ما ساعت ۱۶ در فرمانداری است"),
}


def is_demo_message(msg):
    """تشخیص پیام نمونه/تستی قدیمی برای حذف خودکار از پایگاه داده"""
    if msg.get("update_id") is not None:
        return False  # پیام واقعی دریافتی از بات هرگز update_id ندارد = None نمی‌ماند
    if msg.get("media"):
        return False
    if str(msg.get("chat_title") or "") == DEMO_TITLE:
        return True
    key = (str(msg.get("sender_name") or ""), str(msg.get("text") or ""))
    return key in DEMO_SIGNATURES


class AppState:
    """حالت مشترک برنامه بین سرور فلسک و رشته دریافت"""

    def __init__(self):
        self.lock = threading.RLock()
        self.token = ""
        self.bot_info = None
        self.chat_id = None
        self.chat_title = ""
        self.rules_text = DEFAULT_RULES
        self.rules_saved = False
        self.categorizer = Categorizer(parse_rules(DEFAULT_RULES))
        self.messages = load_messages(MESSAGES_PATH)
        self.seen_updates = {
            m.get("update_id") for m in self.messages if m.get("update_id") is not None
        }
        self.known_chats = {}  # chat_id(str) → {id,title,type,count}
        self.running = False
        self.draining = False  # حالت «خواندن همه پیام‌ها»
        self.phase = "idle"  # idle | backlog (خواندن پیام‌های قبلی) | live (دریافت زنده)
        self.last_groups_count = -1
        self.started_once = False
        self.stop_event = threading.Event()
        self.thread = None
        self.session_count = 0
        self.target = 50
        self.log = []
        self.report_ready = False
        self.report_url = ""
        self.queue_hint = False  # بنر هشدار «صف سرور بله خالی است»
        self.last_report_ts = 0.0  # آخرین زمان ساخت/به‌روزرسانی خودکار گزارش
        self.error = ""
        self.offset = 0  # آخرین update_id تأییدشده + ۱ (ماندگار در settings)
        self.raw = []  # بایگانی خام آپدیت‌ها — ضد گم‌شدن پیام
        self.raw_ids = set()
        self.last_private_chat = None
        self.exports = []  # فهرست خروجی‌های جداگانه (نسخه ۴.۶)
        self.gen = 0  # نسلی — برای توقف سریع کارگر هنگام پاک‌سازی
        self._load_raw()
        self._load_exports()
        self._load_settings()
        self._startup_cleanup()

    # ---------- پاک‌سازی خودکار هنگام اجرا (نسخه ۵) ----------

    def _startup_cleanup(self):
        """۱) حذف خودکار پیام‌های نمونه/تستی قدیمی از پایگاه داده
        ۲) به‌روزرسانی دسته‌ها با قوانین پیش‌فرض جدید (اگر کاربر قوانین سفارشی
        ذخیره نکرده باشد) — دسته‌بندی بر اساس داده‌های موجود انجام می‌شود
        """
        removed = [m for m in self.messages if is_demo_message(m)]
        if removed:
            self.messages = [
                m for m in self.messages if not is_demo_message(m)
            ]
            try:
                save_messages(self.messages, MESSAGES_PATH)
            except OSError:
                pass
        # اگر کاربر هرگز قوانین سفارشی ذخیره نکرده باشد (یا همان پیش‌فرض
        # قدیمی در settings.json ذخیره شده باشد — حالت رایج نسخه‌های قبلی)،
        # دسته‌های پیام‌های قبلی با قوانین جدید به‌روز می‌شوند
        rules_customized = self.rules_saved and (
            self.rules_text.strip() != OLD_DEFAULT_RULES.strip()
        )
        changed = 0
        if not rules_customized:
            # قوانین جدید فعال و دسته‌بندی دوباره انجام می‌شود
            self.rules_text = DEFAULT_RULES
            self.rules_saved = True
            self.categorizer = Categorizer(parse_rules(DEFAULT_RULES))
            for m in self.messages:
                new_cat = categorize_message(self.categorizer, m)
                if new_cat != m.get("category"):
                    m["category"] = new_cat
                    changed += 1
            if changed:
                try:
                    save_messages(self.messages, MESSAGES_PATH)
                except OSError:
                    pass
                # تنظیمات کمی بعد (هنگام شروع دریافت/اتصال) ذخیره می‌شود —
                # در زمان __init__ هنوز _save_settings در دسترس نیست
        if removed:
            self.add_log(
                f"{len(removed)} پیام نمونه/تستی قدیمی از پایگاه داده حذف شد — "
                "قابلیت پیام نمونه در نسخه ۵ کلاً حذف شده است",
                "warn",
            )
        if changed:
            self.add_log(
                f"دسته‌بندی {changed} پیام با قوانین پیش‌فرض جدید به‌روز شد",
                "info",
            )

    # ---------- فهرست خروجی‌های جداگانه (نسخه ۴.۶) ----------

    def _load_exports(self):
        try:
            with open(EXPORTS_PATH, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return
        if isinstance(data, list):
            self.exports = [e for e in data if isinstance(e, dict)]

    def _save_exports(self):
        with self.lock:
            try:
                save_json(self.exports, EXPORTS_PATH, indent=2)
            except OSError:
                pass

    # ---------- بایگانی خام ----------

    def _load_raw(self):
        try:
            with open(RAW_PATH, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return
        if isinstance(data, list):
            self.raw = [u for u in data if isinstance(u, dict)]
            self.raw_ids = {
                u.get("update_id") for u in self.raw if u.get("update_id") is not None
            }

    def archive_raw(self, updates):
        """ذخیره همه آپدیت‌های خام قبل از هر پردازشی — هیچ پیامی گم نمی‌شود"""
        with self.lock:
            added = 0
            for upd in updates:
                if not isinstance(upd, dict):
                    continue
                uid = upd.get("update_id")
                if uid is not None and uid in self.raw_ids:
                    continue
                self.raw.append(upd)
                if uid is not None:
                    self.raw_ids.add(uid)
                added += 1
            if added:
                try:
                    save_json(self.raw, RAW_PATH)
                except OSError:
                    pass
            return added

    def _load_settings(self):
        """بازیابی تنظیمات قبلی (توکن، گروه، قوانین، گفتگوهای شناخته‌شده)"""
        try:
            with open(SETTINGS_PATH, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(data, dict):
            return
        token = str(data.get("token") or "").strip()
        if token:
            self.token = token
        self.chat_id = data.get("chat_id")
        self.chat_title = str(data.get("chat_title") or "")
        rules = str(data.get("rules") or "").strip()
        if rules:
            self.rules_text = rules
            self.categorizer = Categorizer(parse_rules(rules))
            self.rules_saved = True
        try:
            self.target = max(1, int(data.get("target") or 50))
        except (TypeError, ValueError):
            pass
        chats = data.get("known_chats")
        if isinstance(chats, dict):
            self.known_chats = {
                str(k): (v if isinstance(v, dict) else {}) for k, v in chats.items()
            }
        try:
            self.offset = max(0, int(data.get("offset") or 0))
        except (TypeError, ValueError):
            self.offset = 0

    # ---------- لاگ ----------

    def add_log(self, text, kind="info"):
        with self.lock:
            self.log.append({"t": now_str(), "text": text, "kind": kind})
            self.log = self.log[-300:]

    # ---------- گفتگوهای شناخته‌شده ----------

    def record_chat(self, chat_id, title="", ctype="", count=1):
        """ثبت/به‌روزرسانی یک گفتگو برای صفحه «انتخاب گروه»"""
        if chat_id is None:
            return
        with self.lock:
            key = str(chat_id)
            rec = self.known_chats.get(key) or {
                "id": chat_id,
                "title": "",
                "type": ctype or "",
                "count": 0,
            }
            if title:
                rec["title"] = title
            if ctype:
                rec["type"] = ctype
            rec["count"] = int(rec.get("count") or 0) + count
            self.known_chats[key] = rec

    def groups_snapshot(self):
        """لیست گفتگوهای شناخته‌شده از آپدیت‌ها و پیام‌های ذخیره‌شده"""
        chats = {}
        with self.lock:
            base = {k: dict(v) for k, v in self.known_chats.items()}
        for key, rec in base.items():
            chats[key] = {
                "id": rec.get("id"),
                "title": rec.get("title") or f"گفتگو {key}",
                "type": rec.get("type") or "",
                "count": rec.get("count") or 0,
            }
        with self.lock:
            msgs = list(self.messages)
        for m in msgs:
            cid = m.get("chat_id")
            if cid is None:
                continue
            key = str(cid)
            rec = chats.get(key) or {"id": cid, "title": "", "type": m.get("chat_type") or "", "count": 0}
            if not rec.get("title") and m.get("chat_title"):
                rec["title"] = m["chat_title"]
            rec["count"] = int(rec.get("count") or 0)
            chats[key] = rec
        out = []
        for key, rec in chats.items():
            t = rec.get("type") or ""
            out.append({
                "id": rec["id"],
                "title": rec.get("title") or f"گفتگو {key}",
                "type": t,
                "type_label": TYPE_LABELS.get(t, "گفتگو"),
                "count": rec.get("count") or 0,
            })
        out.sort(key=lambda c: -c["count"])
        return out

    # ---------- پیشرفت ----------

    def progress(self):
        with self.lock:
            total = len(self.messages)
            target = max(1, self.target)
            reading_pct = min(100, int(total * 100 / target))
            steps = [
                {
                    "name": "وارد کردن توکن و اتصال ربات",
                    "done": self.bot_info is not None,
                    "weight": 15,
                    "note": "",
                },
                {
                    "name": "شناسایی و انتخاب گروه",
                    "done": self.chat_id is not None,
                    "weight": 15,
                    "note": self.chat_title or "",
                },
                {
                    "name": "شروع دریافت پیام‌ها",
                    "done": self.started_once,
                    "weight": 10,
                    "note": "",
                },
                {
                    "name": "تنظیم قوانین دسته‌بندی",
                    "done": self.rules_saved,
                    "weight": 5,
                    "note": "",
                },
                {
                    "name": "خواندن پیام‌ها",
                    "done": reading_pct >= 100,
                    "weight": int(reading_pct * 40 / 100),
                    "note": f"{total} از {target} پیام ({reading_pct}٪)",
                    "partial": True,
                },
                {
                    "name": "ساخت گزارش HTML",
                    "done": self.report_ready,
                    "weight": 15,
                    "note": "",
                },
            ]
            percent = min(100, sum(s["weight"] for s in steps if s["done"]))
            return {
                "percent": percent,
                "steps": steps,
                "reading_percent": reading_pct,
                "target": target,
                "read": total,
            }

    # ---------- آمار ----------

    def stats(self):
        with self.lock:
            msgs = list(self.messages)
        cats = Counter(m.get("category") or FALLBACK for m in msgs)
        people = set()
        photos = 0
        media_count = 0
        forwards = 0
        for m in msgs:
            p = m.get("sender_name") or m.get("username") or m.get("sender_id")
            if p:
                people.add(str(p))
            if m.get("forward"):
                forwards += 1
            for item in m.get("media") or []:
                media_count += 1
                if item.get("type") == "photo":
                    photos += 1
        return {
            "total": len(msgs),
            "session": self.session_count,
            "participants": len(people),
            "photos": photos,
            "media": media_count,
            "forwards": forwards,
            "raw": len(self.raw),
            "categories": dict(cats.most_common()),
        }

    def recent(self, n=8):
        with self.lock:
            msgs = list(self.messages)
        msgs.sort(key=lambda m: m.get("date") or 0, reverse=True)
        out = []
        for m in msgs[:n]:
            has_photo = any(x.get("type") == "photo" for x in m.get("media") or [])
            text = m.get("text") or m.get("caption") or ""
            if not text and m.get("media"):
                text = "[عکس]" if has_photo else "[رسانه]"
            out.append(
                {
                    "sender": m.get("sender_name") or m.get("username") or "ناشناس",
                    "category": m.get("category") or FALLBACK,
                    "text": text[:140],
                    "when": format_ts(m.get("date")) or m.get("date_text", ""),
                    "chat": m.get("chat_title") or "",
                    "media": len(m.get("media") or []),
                }
            )
        return out


S = AppState()
app = Flask(__name__)


# ---------------- صفحات ----------------


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/output/<path:name>")
def output_file(name):
    resp = send_from_directory(OUTPUT_DIR, name)
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.route("/media/<path:name>")
def media_file(name):
    resp = send_from_directory(MEDIA_DIR, name)
    resp.headers["Cache-Control"] = "max-age=3600"
    return resp


# ---------------- وضعیت ----------------


@app.route("/api/state")
def api_state():
    with S.lock:
        bot = None
        if S.bot_info:
            bot = {
                "name": S.bot_info.get("first_name", ""),
                "username": S.bot_info.get("username", ""),
            }
        state = {
            "bot": bot,
            "connected": S.bot_info is not None,
            "running": S.running,
            "chat": (
                {"id": S.chat_id, "title": S.chat_title}
                if S.chat_id is not None
                else None
            ),
            "progress": S.progress(),
            "stats": S.stats(),
            "recent": S.recent(),
            "log": S.log[-80:],
            "rules": S.rules_text,
            "target": S.target,
            "report_ready": S.report_ready,
            "report_url": S.report_url,
            "exports": list(S.exports),
            "error": S.error,
            "draining": S.draining,
            "phase": S.phase,
            "raw_count": len(S.raw),
            "queue_hint": S.queue_hint,
            "data_info": {
                "messages": MESSAGES_PATH,
                "raw": RAW_PATH,
                "output": OUTPUT_DIR,
                "media": MEDIA_DIR,
            },
            "version": VERSION,
            "app_name": APP_NAME,
        }
    return jsonify(state)


# ---------------- اتصال و گروه ----------------


@app.route("/api/connect", methods=["POST"])
def api_connect():
    data = request.get_json(silent=True) or {}
    token = str(data.get("token") or "").strip()
    if not token:
        return jsonify(ok=False, error="توکن ربات را وارد کنید"), 400
    try:
        me = BaleClient(token).get_me()
    except BaleBotError as exc:
        S.error = f"اتصال ناموفق: {exc}"
        S.add_log(S.error, "error")
        return jsonify(ok=False, error=str(exc)), 400
    with S.lock:
        S.token = token
        S.bot_info = me
        S.error = ""
    S.add_log(
        f"ربات متصل شد: {me.get('first_name', '')} (@{me.get('username', '')})",
        "info",
    )
    _save_settings()
    _ensure_worker()  # دریافت زنده به‌طور خودکار آغاز می‌شود — بدون نیاز به دکمه
    return jsonify(ok=True, bot={"name": me.get("first_name", ""), "username": me.get("username", "")})


@app.route("/api/groups", methods=["POST"])
def api_groups():
    token = _current_token()
    if not token:
        return jsonify(ok=False, error="ابتدا ربات را متصل کنید"), 400

    # اسکن زنده غیرمخرب (offset=0 تأیید نمی‌کند) — فقط وقتی رشته دریافت فعال نیست؛
    # در حین polling فعال، همین اسکن باعث تداخل (409) و کندی دریافت می‌شد
    if not S.running:
        try:
            updates = BaleClient(token).get_updates(offset=0, limit=100, timeout=0) or []
            for upd in updates:
                member = normalize_member_update(upd)
                if member:
                    S.record_chat(member["chat_id"], member["title"], member["type"])
                src = (
                    upd.get("message")
                    or upd.get("edited_message")
                    or upd.get("channel_post")
                    or upd.get("edited_channel_post")
                )
                if isinstance(src, dict):
                    chat = src.get("chat") or {}
                    S.record_chat(chat.get("id"), chat.get("title") or chat.get("first_name"),
                                  chat.get("type"))
        except BaleBotError:
            pass  # لیست از پیام‌های ذخیره‌شده ساخته می‌شود

    groups = S.groups_snapshot()
    if len(groups) != S.last_groups_count:
        if S.last_groups_count >= 0:
            S.add_log(f"{len(groups)} گفتگو شناسایی شد", "info")
        S.last_groups_count = len(groups)
    return jsonify(ok=True, groups=groups)


@app.route("/api/group/add", methods=["POST"])
def api_group_add():
    """افزودن گروه: شناسه عددی، @نام‌کاربری یا لینک دعوت

    نکته: API ربات بله اجازه عضویت با لینک دعوت ندارد (تست زنده شد)،
    بنابراین برای لینک، راهنمای گام‌به‌گام نمایش داده می‌شود.
    """
    data = request.get_json(silent=True) or {}
    raw = str(data.get("link") or "").strip()
    if not raw:
        return jsonify(ok=False, error="لینک یا شناسه گروه را وارد کنید"), 400
    token = _current_token()
    if not token:
        return jsonify(ok=False, error="ابتدا ربات را متصل کنید"), 400
    client = BaleClient(token)

    # ۱) شناسه عددی (مثلاً -1001234567890)
    cleaned = raw.replace(" ", "")
    try:
        chat_id = int(cleaned)
        info = client.get_chat(chat_id)
        title = info.get("title") or info.get("first_name") or f"گفتگو {chat_id}"
        ctype = info.get("type") or ""
        S.record_chat(chat_id, title, ctype)
        with S.lock:
            S.chat_id = chat_id
            S.chat_title = title
        S.add_log(f"گروه «{title}» با شناسه انتخاب شد", "info")
        _save_settings()
        return jsonify(ok=True, chat={"id": chat_id, "title": title,
                                      "type_label": TYPE_LABELS.get(ctype, "گفتگو")})
    except ValueError:
        pass
    except BaleBotError as exc:
        return jsonify(
            ok=False,
            error=f"شناسه یافت نشد: {exc} — ربات باید ابتدا در گروه اضافه شده باشد",
        ), 400

    # ۲) لینک دعوت (ble.ir/join/HASH) — ربات نمی‌تواند خودش عضو شود
    lower = cleaned.lower()
    is_invite = ("ble.ir/join/" in lower) or ("/join/" in lower) or (
        "invite" in lower and "http" in lower
    )
    if is_invite:
        S.add_log("لینک دعوت دریافت شد — عضویت خودکار ربات ممکن نیست", "warn")
        return jsonify(
            ok=False,
            need_manual=True,
            link=raw,
            error="ربات‌های بله (مثل همه ربات‌ها) نمی‌توانند با لینک دعوت وارد گروه شوند؛ لینک دعوت فقط برای افراد است. لطفاً ربات را دستی به گروه اضافه کنید:",
            steps=[
                "گروه را باز کنید و روی نام گروه (بالای صفحه) بزنید تا تنظیمات گروه باز شود",
                "گزینه «افزودن عضو» را بزنید و @mosharkat_bot را جست‌وجو و انتخاب کنید",
                "بهتر است ربات را «مدیر» (ادمین) کنید تا همه پیام‌ها را ببیند",
                "بعد از اضافه شدن، در همین صفحه دکمه «شناسایی گروه‌ها» را بزنید — گروه به‌طور خودکار ظاهر می‌شود",
            ],
        ), 200

    # ۳) نام کاربری (@name یا ble.ir/name یا t.me/name)
    username = ""
    if cleaned.startswith("@"):
        username = cleaned
    else:
        for prefix in ("https://ble.ir/", "http://ble.ir/", "ble.ir/", "https://t.me/", "t.me/"):
            if lower.startswith(prefix):
                username = "@" + raw[len(prefix):].strip("/? ")
                break
    if username:
        try:
            info = client.get_chat(username)
            chat_id = info.get("id")
            title = info.get("title") or info.get("first_name") or username
            ctype = info.get("type") or ""
            S.record_chat(chat_id, title, ctype)
            with S.lock:
                S.chat_id = chat_id
                S.chat_title = title
            S.add_log(f"گفتگو «{title}» با نام کاربری انتخاب شد", "info")
            _save_settings()
            return jsonify(ok=True, chat={"id": chat_id, "title": title,
                                          "type_label": TYPE_LABELS.get(ctype, "گفتگو")})
        except BaleBotError as exc:
            return jsonify(
                ok=False,
                need_manual=True,
                error=f"این گفتگو برای ربات قابل شناسایی نیست ({exc}).",
                steps=[
                    "اگر گروه خصوصی است، ربات باید اول با «افزودن عضو» به گروه اضافه شود",
                    "بعد از اضافه شدن ربات، دکمه «شناسایی گروه‌ها» را بزنید",
                ],
            ), 200

    return jsonify(
        ok=False,
        error="قالب ورودی شناخته نشد؛ شناسه عددی گروه، @نام‌کاربری یا لینک بله را وارد کنید",
    ), 400


@app.route("/api/group/select", methods=["POST"])
def api_group_select():
    data = request.get_json(silent=True) or {}
    if str(data.get("id")) == "all":
        with S.lock:
            S.chat_id = None
            S.chat_title = ""
        S.add_log("حالت «همه گفتگوها» فعال شد", "info")
        _save_settings()
        return jsonify(ok=True)
    try:
        chat_id = int(data.get("id"))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="شناسه گروه معتبر نیست"), 400
    with S.lock:
        S.chat_id = chat_id
        S.chat_title = str(data.get("title") or f"گروه {chat_id}")
    S.add_log(f"گروه «{S.chat_title}» انتخاب شد", "info")
    _save_settings()
    return jsonify(ok=True)


# ---------------- دریافت ----------------


@app.route("/api/start", methods=["POST"])
def api_start():
    token = _current_token()
    if not token:
        return jsonify(ok=False, error="ابتدا توکن را وارد و اتصال را تست کنید"), 400
    if S.running:
        return jsonify(ok=True)
    with S.lock:
        S.rules_saved = True  # قوانین ذخیره‌شده/پیش‌فرض فعال است
        S.error = ""
        S.stop_event.clear()
        S.running = True
        S.started_once = True
        S.thread = threading.Thread(target=_collector_worker, args=(token,), daemon=True)
        S.thread.start()
    S.add_log(
        "دریافت آغاز شد: اول همه پیام‌های قبلی بات خوانده می‌شود، بعد دریافت زنده ادامه پیدا می‌کند",
        "info",
    )
    return jsonify(ok=True)


@app.route("/api/stop", methods=["POST"])
def api_stop():
    S.draining = False
    if S.running:
        S.stop_event.set()
        S.add_log("دستور توقف دریافت صادر شد", "info")
    return jsonify(ok=True)


def _ensure_worker():
    """شروع خودکار دریافت اگر توکن موجود باشد و رشته‌ای در حال کار نباشد

    از نسخه ۴.۴ به‌محض اتصال/اجرای برنامه:
    اول همه پیام‌های قبلی موجود در بات خوانده می‌شود (مرحله ۱)،
    گزارش HTML خودکار ساخته می‌شود و بعد دریافت زنده آغاز می‌شود (مرحله ۲).
    """
    token = _current_token()
    if not token:
        return
    with S.lock:
        if S.running:
            return
        S.rules_saved = True
        S.stop_event.clear()
        S.running = True
        S.started_once = True
        S.thread = threading.Thread(target=_collector_worker, args=(token,), daemon=True)
        S.thread.start()
    S.add_log(
        "همگام‌سازی خودکار آغاز شد: اول همه پیام‌های قبلی بات خوانده می‌شود، بعد پیام‌های جدید زنده دریافت می‌شوند",
        "info",
    )


@app.route("/api/read_all", methods=["POST"])
def api_read_all():
    """خواندن همه پیام‌های موجود در بات (فورواردها، عکس‌ها، کامنت‌ها)
    و سپس ساخت خودکار گزارش HTML

    از نسخه ۴.۴ این کار هنگام اجرا/اتصال به‌طور خودکار انجام می‌شود؛
    این دکمه برای «همگام‌سازی دوباره در همین لحظه» است.
    """
    token = _current_token()
    if not token:
        return jsonify(ok=False, error="ابتدا توکن را وارد و اتصال را تست کنید"), 400
    with S.lock:
        S.rules_saved = True
        S.error = ""
        S.draining = True
        if not S.running:
            S.stop_event.clear()
            S.running = True
            S.started_once = True
            S.thread = threading.Thread(
                target=_collector_worker, args=(token,), daemon=True
            )
            S.thread.start()
    S.add_log(
        "همگام‌سازی آغاز شد — همه پیام‌های موجود خوانده می‌شوند و در پایان گزارش ساخته می‌شود",
        "info",
    )
    return jsonify(ok=True)


@app.route("/api/target", methods=["POST"])
def api_target():
    data = request.get_json(silent=True) or {}
    try:
        S.target = max(1, int(data.get("target") or 50))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="عدد نامعتبر"), 400
    _save_settings()
    return jsonify(ok=True, target=S.target)


def _default_ext(media_type):
    return {
        "photo": ".jpg",
        "video": ".mp4",
        "voice": ".ogg",
        "audio": ".mp3",
        "animation": ".mp4",
        "document": ".bin",
        "sticker": ".webp",
    }.get(media_type, ".bin")


def _download_media(client, msg):
    """دانلود همه رسانه‌های پیام در پوشه media — نام فایل در item['file'] ذخیره می‌شود"""
    saved = 0
    for i, item in enumerate(msg.get("media") or []):
        fid = item.get("file_id")
        if not fid:
            continue
        if item.get("file"):
            continue  # قبلاً دانلود شده است
        try:
            info = client.get_file(fid)
            fpath = str(info.get("file_path") or "")
            ext = os.path.splitext(fpath)[1].lower()
            if not ext:
                ext = _default_ext(item.get("type"))
            name = f"u{msg.get('update_id') or 0}_m{msg.get('message_id') or 0}_{i}{ext}"
            client.download_file(fpath, os.path.join(MEDIA_DIR, name))
            item["file"] = name
            saved += 1
        except BaleBotError as exc:
            S.add_log(f"دانلود {item.get('type')} ناموفق: {exc}", "error")
    return saved


def _send_private(client, chat_id, text):
    """ارسال امن پیام به چت خصوصی — خطا هرگز رشته دریافت را نمی‌شکند"""
    try:
        client.send_message(chat_id, text)
    except BaleBotError:
        pass


def _finish_drain(client):
    """پایان «خواندن همه»: ساخت خودکار گزارش HTML + پیام خلاصه به کاربر"""
    with S.lock:
        msgs = list(S.messages)
        total = len(msgs)
        session = S.session_count
        target_chat = S.last_private_chat
    S.add_log(
        f"خواندن همه پیام‌ها کامل شد — مجموع {total} پیام ({session} پیام در این دور)",
        "info",
    )
    if session == 0:
        S.add_log(
            "در این دور هیچ پیام جدیدی در بات نبود. اگر قبلاً پیام‌هایی به چت ربات فرستاده‌اید، "
            "آن‌ها با نسخه قدیمی برنامه خوانده و ذخیره نشده‌اند یا بیش از ۲۴ ساعت از ارسالشان "
            "گذشته است (سرور بله آپدیت‌ها را حداکثر ۲۴ ساعت نگه می‌دارد). لطفاً پیام‌ها را دوباره "
            "به چت ربات فوروارد کنید و دوباره «خواندن همه» را بزنید — این بار همه‌چیز ذخیره می‌شود.",
            "warn",
        )
    if not msgs:
        S.add_log("پیامی برای گزارش وجود ندارد", "error")
        return
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    try:
        build_report(
            msgs,
            os.path.join(OUTPUT_DIR, "report.html"),
            group_title=S.chat_title or None,
            media_base=MEDIA_DIR,
        )
        with S.lock:
            S.report_ready = True
            S.report_url = "/output/report.html"
        S.add_log("گزارش HTML به‌صورت خودکار ساخته شد — دکمه «مشاهده گزارش» فعال است", "info")
    except OSError as exc:
        S.add_log(f"ساخت خودکار گزارش ناموفق بود: {exc}", "error")
    if target_chat is not None:
        _send_private(
            client,
            target_chat,
            f"خواندن کامل شد: مجموع {total} پیام ذخیره شد و گزارش HTML ساخته شد.",
        )


def _upsert_message(msg):
    """افزودن پیام به پایگاه داده یا جایگزینی نسخه قبلی (پیام ویرایش‌شده)

    تابع مشترک مسیر عادی (_store_update) و مسیر بازیابی از آرشیو خام
    (_recover_from_raw) — تا در هر دو مسیر، پیام ویرایش‌شده نسخه قبلی
    را جایگزین کند و هیچ پیام تکراری‌ای ساخته نشود (اصلاح نسخه ۴.۵).

    خروجی: True اگر پیام جدید اضافه شد، False اگر نسخه قبلی جایگزین شد.
    """
    with S.lock:
        replaced = False
        if msg.get("chat_id") is not None and msg.get("message_id"):
            for idx, old in enumerate(S.messages):
                if (
                    old.get("chat_id") == msg.get("chat_id")
                    and old.get("message_id") == msg.get("message_id")
                ):
                    S.messages[idx] = msg
                    replaced = True
                    break
        if not replaced:
            S.messages.append(msg)
            S.session_count += 1
        return not replaced


def _recover_from_raw(client):
    """بازیابی پیام‌های ذخیره‌نشده از آرشیو خام (raw_updates.json)

    هر آپدیت قبل از هر پردازشی در بایگانی خام ذخیره می‌شود؛ این تابع
    هر پیامی که به‌هر دلیل ذخیره نشده باشد را بازسازی می‌کند.
    """
    with S.lock:
        raw = list(S.raw)
        seen = set(S.seen_updates)
    recovered = 0
    for upd in raw:
        if not isinstance(upd, dict):
            continue
        uid = upd.get("update_id")
        if uid is not None and uid in seen:
            continue
        msg = normalize_update(upd)
        if msg is None:
            continue
        cat_text = (msg.get("text") or msg.get("caption") or "").strip()
        if cat_text.startswith("/"):
            continue  # دستورات ربات بازیابی نمی‌شوند
        if client is not None and msg.get("media"):
            try:
                _download_media(client, msg)
            except Exception:
                pass
        msg["category"] = categorize_message(S.categorizer, msg)
        if _upsert_message(msg):
            recovered += 1
        with S.lock:
            if uid is not None:
                S.seen_updates.add(uid)
    if recovered:
        with S.lock:
            try:
                save_messages(S.messages, MESSAGES_PATH)
            except OSError:
                pass
        S.queue_hint = False
    return recovered


def _maybe_auto_report(min_interval=25.0, force=False):
    """ساخت/به‌روزرسانی گزارش HTML از وضعیت فعلی پایگاه داده (نسخه ۴.۵)

    این تابع با «هر» تغییر پایگاه داده فراخوانی می‌شود تا گزارش همیشه
    هم‌گام با پیام‌های ذخیره‌شده باشد و هیچ‌وقت گزارش کهنه/خالی دیده نشود.
    برای جلوگیری از بازسازی مکرر با عکس‌های زیاد، حداقل فاصله ۲۵ ثانیه
    اعمال می‌شود (force=True بدون توجه به فاصله زمانی بازسازی می‌کند).
    """
    with S.lock:
        now = time.time()
        if not force and now - S.last_report_ts < min_interval:
            return False
        if not S.messages:
            return False
        S.last_report_ts = now
        msgs = list(S.messages)
        title = S.chat_title or None
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    try:
        build_report(
            msgs,
            os.path.join(OUTPUT_DIR, "report.html"),
            group_title=title,
            media_base=MEDIA_DIR,
        )
    except OSError as exc:
        S.add_log(f"به‌روزرسانی خودکار گزارش ناموفق بود: {exc}", "error")
        return False
    with S.lock:
        S.report_ready = True
        S.report_url = "/output/report.html"
    return True


def _build_report_auto():
    """ساخت خودکار گزارش HTML از پیام‌های ذخیره‌شده؛ اگر پیامی نباشد کاری نمی‌کند"""
    if _maybe_auto_report(force=True):
        return S.report_url
    return ""


def _store_update(client, upd, force_all=False, live=False):
    """پردازش و ذخیره یک آپدیت خام (پیام/ویرایش/رسانه/کامنت/بازنشر)

    force_all=True (مرحله خواندن پیام‌های قبلی): همه‌چیز بدون فیلتر گروه ذخیره می‌شود
    live=True (دریافت زنده): برای پیام خصوصی تأییدیه «ذخیره شد» ارسال می‌شود
    خروجی: True یعنی آپدیت شناخته و رسیدگی شد (صرف‌نظر از ذخیره‌شدن)
    """
    # اضافه/حذف شدن ربات از گروهی → گفتگو را ثبت کن
    member = normalize_member_update(upd)
    if member:
        S.record_chat(member["chat_id"], member["title"], member["type"])
        status = member.get("new_status") or ""
        if status in ("member", "administrator"):
            S.add_log(
                f"ربات به «{member['title']}» اضافه شد — گفتگو در فهرست انتخاب گروه قرار گرفت",
                "info",
            )
        return True

    msg = normalize_update(upd)
    if msg is None:
        return False

    uid = msg.get("update_id")
    chat_id = msg.get("chat_id")
    ctype = msg.get("chat_type") or ""
    S.record_chat(chat_id, msg.get("chat_title"), ctype)
    if ctype == "private":
        with S.lock:
            S.last_private_chat = chat_id

    cat_text = (msg.get("text") or msg.get("caption") or "").strip()

    # فیلتر گفتگو فقط در حالت زنده؛ در «خواندن پیام‌های قبلی» هر چیز ذخیره می‌شود
    if (
        not force_all
        and S.chat_id is not None
        and ctype != "private"
        and chat_id != S.chat_id
    ):
        return True

    if cat_text.startswith("/"):
        if ctype == "private":
            _send_private(client, chat_id, GUIDE_TEXT)
        return True  # دستورات ربات ذخیره نمی‌شوند

    # دانلود رسانه‌ها (عکس/ویدیو/فایل)
    if msg.get("media"):
        n = _download_media(client, msg)
        if n:
            S.add_log(f"{n} فایل رسانه ذخیره شد", "info")

    msg["category"] = categorize_message(S.categorizer, msg)

    _upsert_message(msg)
    with S.lock:
        if uid is not None:
            S.seen_updates.add(uid)
        S.queue_hint = False  # پیام رسید — بنر «صف خالی» برداشته می‌شود
        try:
            save_messages(S.messages, MESSAGES_PATH)
        except OSError as exc:
            S.add_log(f"ذخیره فایل پیام‌ها ناموفق بود: {exc}", "error")

    kind = "ویرایش" if msg.get("edited") else "پیام"
    if msg.get("forward"):
        kind += " (بازنشر)"
    shown = cat_text[:44] + ("…" if len(cat_text) > 44 else "") or (
        f"[{len(msg.get('media') or [])} رسانه]"
        if msg.get("media")
        else "(بدون متن)"
    )
    S.add_log(
        f"{kind} #{len(S.messages)} — {msg['sender_name']}: {shown} ← دسته: {msg['category']}",
        "msg",
    )
    # تأییدیه فوری در چت خصوصی (فقط پیام جدید زنده — نه بک‌لاگ)
    if live and ctype == "private":
        _send_private(
            client, chat_id,
            f"ذخیره شد — پیام شماره {len(S.messages)} در پایگاه داده برنامه.",
        )
    return True


BACKLOG_EMPTY_HINT = (
    "در صف سرور بله هیچ پیام قبلی‌ای پیدا نشد. دلیل‌های ممکن:\n"
    "۱) پیام‌هایی که قبلاً به چت ربات فرستاده/فوروارد کرده بودید، پیش‌تر توسط نسخه قدیمی "
    "برنامه (در پوشه دیگر) خوانده شده‌اند یا بیش از ۲۴ ساعت از ارسالشان گذشته است — "
    "سرور بله صف را فقط ۲۴ ساعت نگه می‌دارد و طبق مستندات رسمی، API ربات بله هیچ روشی "
    "برای خواندن تاریخچه چت ندارد. اگر پوشه قدیمی برنامه فایل raw_updates.json یا "
    "messages.json دارد، آن‌ها را کنار این برنامه کپی کنید و برنامه را دوباره باز کنید — "
    "به‌طور خودکار بازیابی می‌شوند.\n"
    "۲) یا هنوز پیامی به چت ربات فوروارد نشده است — پیام‌های قدیمی گروه را به چت ربات "
    "فوروارد کنید؛ به‌محض رسیدن، همه ذخیره و گزارش ساخته می‌شود."
)


def _collector_worker(token, backlog=True):
    """رشته دریافت: اول «خواندن همه پیام‌های قبلی» سپس «دریافت زنده»

    مرحله صفر: بازیابی خودکار از آرشیو خام (اگر پیام ذخیره‌نشده وجود داشته باشد)
    مرحله ۱ (backlog): همه آپدیت‌های موجود در صف سرور بله خوانده و ذخیره می‌شوند
                       (بدون فیلتر گروه) و در پایان گزارش HTML خودکار ساخته می‌شود
    مرحله ۲ (live): دریافت زنده برای همیشه ادامه دارد — هر پیام جدید فوری ذخیره می‌شود

    با تغییر S.gen (مثلاً هنگام پاک‌سازی) کارگر سریع و بدون ذخیره پیام جدید خارج می‌شود.
    """
    try:
        with S.lock:
            my_gen = S.gen
        gen_alive = lambda: (S.gen == my_gen)  # noqa: E731
        client = BaleClient(token)
        try:
            me = client.get_me()
            # حتی وقتی worker خودکار (با توکن ذخیره‌شده) شروع می‌شود،
            # داشبورد باید «ربات متصل» را نشان دهد
            with S.lock:
                S.bot_info = me
                S.token = token
                S.error = ""
            S.add_log(
                f"متصل شد — ربات: {me.get('first_name', '')} (@{me.get('username', '')})",
                "info",
            )
        except BaleBotError:
            pass
        with S.lock:
            offset = S.offset or 0

        # ---------- مرحله صفر: بازیابی از آرشیو خام ----------
        try:
            recovered = _recover_from_raw(client)
            if recovered:
                S.add_log(f"{recovered} پیام از آرشیو خام بازیابی شد", "ok")
        except Exception as exc:  # نابودی آرشیو هرگز رشته دریافت را نمی‌شکند
            S.add_log(f"بازیابی از آرشیو خام ناموفق بود: {exc}", "warn")

        # ---------- مرحله ۱: خواندن همه پیام‌های قبلی صف سرور ----------
        if backlog:
            with S.lock:
                S.phase = "backlog"
                before = len(S.messages)
            S.add_log(
                "مرحله ۱ — خواندن همه پیام‌های قبلی موجود در بات (متن، عکس، کپشن، "
                "کامنت‌ها و بازنشرها) ...",
                "info",
            )
            empty_rounds = 0
            while (not S.stop_event.is_set()) and gen_alive() and empty_rounds < 2:
                try:
                    updates = client.get_updates(
                        offset=offset, limit=100, timeout=1
                    ) or []
                except BaleBotError as exc:
                    S.add_log(f"{exc} — تلاش مجدد پس از ۵ ثانیه", "error")
                    for _ in range(50):
                        if S.stop_event.is_set() or not gen_alive():
                            break
                        time.sleep(0.1)
                    continue

                # بایگانی خام قبل از هر پردازشی — هیچ پیامی گم نمی‌شود
                S.archive_raw(updates)

                for upd in updates:
                    uid = upd.get("update_id") if isinstance(upd, dict) else None
                    if uid is not None:
                        if uid < offset:
                            continue
                        offset = uid + 1
                        if uid in S.seen_updates:
                            continue  # قبلاً ذخیره شده (ری‌استارت برنامه)
                    _store_update(client, upd, force_all=True, live=False)
                if not gen_alive():
                    break

                if updates:
                    empty_rounds = 0
                    with S.lock:
                        read_so_far = len(S.messages) - before
                    if read_so_far:
                        S.add_log(f"… تا اینجا {read_so_far} پیام قبلی خوانده شد", "info")
                else:
                    empty_rounds += 1
                    time.sleep(0.3)

                if offset != S.offset:
                    with S.lock:
                        S.offset = offset
                    _save_settings()

            if offset != S.offset:
                with S.lock:
                    S.offset = offset
                _save_settings()

            with S.lock:
                found = len(S.messages) - before
                total_msgs = len(S.messages)
            if found:
                S.add_log(
                    f"مرحله ۱ کامل شد — {found} پیام قبلی خوانده و ذخیره شد؛ "
                    "گزارش HTML به‌طور خودکار ساخته می‌شود ...",
                    "ok",
                )
                target_chat = S.last_private_chat
                if target_chat is not None:
                    _send_private(
                        client, target_chat,
                        f"همه پیام‌های قبلی خوانده شد ({found} پیام جدید) و گزارش HTML ساخته شد. "
                        "از این پس پیام‌های جدید به‌طور زنده ذخیره می‌شوند.",
                    )
            elif not S.stop_event.is_set() and not recovered:
                for line in BACKLOG_EMPTY_HINT.splitlines():
                    S.add_log(line, "warn")
            # از نسخه ۴.۵: گزارش همیشه از وضعیت فعلی پایگاه داده ساخته می‌شود —
            # حتی اگر این دور پیام جدیدی نبوده ولی پیام‌های قبلی ذخیره شده‌اند
            if _maybe_auto_report(force=True):
                S.add_log("گزارش HTML به‌روز شد — دکمه «مشاهده گزارش» فعال است", "ok")
            with S.lock:
                if total_msgs == 0 and not S.stop_event.is_set():
                    S.queue_hint = True  # بنر هشدار «صف خالی» در داشبورد

        # ---------- مرحله ۲: دریافت زنده ----------
        with S.lock:
            S.phase = "live"
        S.add_log(
            "مرحله ۲ — دریافت زنده آغاز شد؛ هر پیام جدید (گروه یا چت ربات) بلافاصله ذخیره می‌شود",
            "info",
        )
        while (not S.stop_event.is_set()) and gen_alive():
            draining = S.draining
            try:
                updates = client.get_updates(
                    offset=offset, limit=100, timeout=1 if draining else 20
                ) or []
            except BaleBotError as exc:
                S.add_log(f"{exc} — تلاش مجدد پس از ۵ ثانیه", "error")
                for _ in range(50):
                    if S.stop_event.is_set() or not gen_alive():
                        break
                    time.sleep(0.1)
                continue
            if not gen_alive():
                break

            # بایگانی خام قبل از هر پردازشی — هیچ پیامی گم نمی‌شود
            S.archive_raw(updates)

            with S.lock:
                before_live = len(S.messages)
            for upd in updates:
                uid = upd.get("update_id") if isinstance(upd, dict) else None
                if uid is not None:
                    if uid < offset:
                        continue
                    offset = uid + 1
                    if uid in S.seen_updates:
                        continue  # قبلاً ذخیره شده (ری‌استارت برنامه)
                _store_update(client, upd, force_all=False, live=True)

            # از نسخه ۴.۵: با رسیدن هر پیام جدید (حتی در دریافت زنده) گزارش
            # خودکار به‌روز می‌شود تا هیچ‌وقت گزارش کهنه/خالی دیده نشود
            with S.lock:
                stored_now = len(S.messages) != before_live
            if stored_now:
                S.queue_hint = False
                if _maybe_auto_report():
                    S.add_log("گزارش HTML با پیام‌های جدید به‌روز شد", "info")

            if offset != S.offset:
                with S.lock:
                    S.offset = offset
                _save_settings()

            if draining and not updates:
                _finish_drain(client)
                with S.lock:
                    S.draining = False
                # ادامه دریافت زنده پس از پایان «خواندن همه» — برنامه متوقف نمی‌شود
                continue
            if draining:
                time.sleep(0.15)
    except Exception as exc:  # محافظت از رشته پس‌زمینه
        S.add_log(f"خطای غیرمنتظره در دریافت: {exc}", "error")
    finally:
        with S.lock:
            S.running = False
            S.draining = False
            S.phase = "idle"
        S.add_log("دریافت پیام متوقف شد", "info")


# ---------------- دسته‌بندی و داده ----------------


@app.route("/api/rules", methods=["POST"])
def api_rules():
    data = request.get_json(silent=True) or {}
    text = str(data.get("rules") or "")
    rules = parse_rules(text)
    if not rules:
        return jsonify(ok=False, error="هیچ قانون معتبری پیدا نشد"), 400
    with S.lock:
        S.rules_text = text
        S.categorizer = Categorizer(rules)
        S.rules_saved = True
        for m in S.messages:
            m["category"] = categorize_message(S.categorizer, m)
        save_messages(S.messages, MESSAGES_PATH)
    S.add_log(f"{len(rules)} دسته فعال و بر {len(S.messages)} پیام اعمال شد", "info")
    _save_settings()
    return jsonify(ok=True, count=len(rules))


RAW_KINDS = (
    "message", "edited_message", "channel_post", "edited_channel_post",
    "my_chat_member", "chat_member",
)


def _looks_like_raw_update(u):
    """تشخیص آپدیت خام: update_id + یکی از کلیدهای نوع آپدیت

    نکته: پیام‌های ذخیره‌شده هم update_id دارند؛ پس فقط وجود update_id کافی نیست.
    """
    return (
        isinstance(u, dict)
        and "update_id" in u
        and any(k in u for k in RAW_KINDS)
    )


def _load_json_any(path):
    """تشخیص هوشمند نوع فایل JSON (نسخه ۴.۵)

    همه فرمت‌های ممکن با یک دکمه پذیرفته می‌شوند:
        - فایل پشتیبان خود برنامه: {"messages": [...], "raw_updates": [...]}
        - آرشیو خام raw_updates.json: لیست آپدیت‌های خام (دارای update_id)
        - messages.json نسخه‌های قبلی یا خروجی سایر ابزارها: لیست پیام‌ها
    خروجی: (لیست پیام‌ها، لیست آپدیت‌های خام)
    """
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    raw_updates = []
    messages = []
    if isinstance(data, dict):
        ru = data.get("raw_updates")
        if isinstance(ru, list):
            raw_updates = [u for u in ru if _looks_like_raw_update(u)]
        msgs = data.get("messages")
        if isinstance(msgs, list):
            messages = [m for m in msgs if isinstance(m, dict)]
        if not raw_updates and not messages:
            if _looks_like_raw_update(data):
                raw_updates = [data]  # یک آپدیت خام تکی
            else:
                raise ValueError("ساختار فایل JSON قابل قبول نیست")
    elif isinstance(data, list):
        sample = [u for u in data[:5] if isinstance(u, dict)]
        if sample and all(_looks_like_raw_update(u) for u in sample):
            raw_updates = [u for u in data if _looks_like_raw_update(u)]
        else:
            messages = import_json(path)
    else:
        raise ValueError("ساختار فایل JSON قابل قبول نیست")
    return messages, raw_updates


@app.route("/api/import", methods=["POST"])
def api_import():
    """ورود پیام‌های قدیمی از CSV/JSON — از نسخه ۴.۵ همه فرمت‌ها با یک دکمه:
    فایل پشتیبان برنامه، آرشیو خام نسخه قبلی، messages.json و خروجی CSV.
    بعد از ورود، عکس‌های قابل دانلود گرفته و گزارش خودکار به‌روز می‌شود.
    """
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify(ok=False, error="فایلی ارسال نشد"), 400
    suffix = ".csv" if f.filename.lower().endswith(".csv") else ".json"
    path = os.path.join(tempfile.gettempdir(), f"bale_import_{int(time.time())}{suffix}")
    f.save(path)
    incoming, raw_updates = [], []
    try:
        if suffix == ".csv":
            incoming = import_csv(path)
        else:
            incoming, raw_updates = _load_json_any(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        S.add_log(f"خطای ورود فایل {f.filename}: {exc}", "error")
        return jsonify(ok=False, error=str(exc)), 400
    finally:
        try:
            os.remove(path)
        except OSError:
            pass

    added = 0
    if raw_updates:
        # آپدیت‌های خام اول در آرشیو ذخیره می‌شوند (ضد گم‌شدن) و سپس
        # با همان مسیر پردازش عادی نرمال و ذخیره می‌شوند (با دانلود عکس‌ها)
        S.archive_raw(raw_updates)
        token = _current_token()
        client = BaleClient(token) if token else None
        added += _recover_from_raw(client)
    if incoming:
        with S.lock:
            added += merge_messages(S.messages, incoming)
            save_messages(S.messages, MESSAGES_PATH)
    if added:
        S.queue_hint = False
        _maybe_auto_report(force=True)
    S.add_log(f"{added} پیام از فایل «{f.filename}» وارد شد", "info")
    return jsonify(ok=True, added=added, raw=len(raw_updates))


@app.route("/api/messages", methods=["GET"])
def api_messages():
    with S.lock:
        msgs = list(S.messages)
    return jsonify(ok=True, count=len(msgs), messages=msgs[-200:])


def _parse_msg_ids(raw_ids):
    """تبدیل شناسه‌های «chat_id:message_id» به مجموعه جفت‌ها"""
    want = set()
    for x in (raw_ids or [])[:3000]:
        s = str(x or "")
        if ":" not in s:
            continue
        cid, _, mid = s.rpartition(":")
        if cid and mid and mid != "None":
            want.add((cid, mid))
    return want


@app.route("/api/messages/delete", methods=["POST"])
def api_messages_delete():
    """حذف پیام‌های انتخابی از پایگاه داده (از داخل گزارش تعاملی)

    ورودی: {"ids": ["chat_id:message_id", ...]}
    بعد از حذف، گزارش زنده هم به‌طور خودکار بازسازی می‌شود.
    """
    data = request.get_json(silent=True) or {}
    want = _parse_msg_ids(data.get("ids"))
    if not want:
        return jsonify(ok=False, error="هیچ شناسه معتبری ارسال نشد"), 400
    removed = 0
    with S.lock:
        before = len(S.messages)

        def _keep(m):
            k = (str(m.get("chat_id")), str(m.get("message_id")))
            return k not in want

        S.messages = [m for m in S.messages if _keep(m)]
        removed = before - len(S.messages)
        try:
            save_messages(S.messages, MESSAGES_PATH)
        except OSError as exc:
            S.add_log(f"ذخیره پس از حذف پیام ناموفق بود: {exc}", "error")
    if removed:
        S.add_log(f"{removed} پیام با انتخاب کاربر از گزارش حذف شد", "warn")
        _maybe_auto_report(force=True)
    return jsonify(ok=True, removed=removed)


@app.route("/api/messages/category", methods=["POST"])
def api_messages_category():
    """تغییر دسته پیام‌های انتخابی (از حالت ویرایش گزارش)

    ورودی: {"ids": ["chat_id:message_id", ...], "category": "نام دسته"}
    """
    data = request.get_json(silent=True) or {}
    want = _parse_msg_ids(data.get("ids"))
    category = str(data.get("category") or "").strip()[:60]
    if not want:
        return jsonify(ok=False, error="هیچ شناسه معتبری ارسال نشد"), 400
    if not category:
        return jsonify(ok=False, error="نام دسته خالی است"), 400
    changed = 0
    with S.lock:
        for m in S.messages:
            k = (str(m.get("chat_id")), str(m.get("message_id")))
            if k in want:
                m["category"] = category
                changed += 1
        if changed:
            try:
                save_messages(S.messages, MESSAGES_PATH)
            except OSError as exc:
                S.add_log(f"ذخیره پس از تغییر دسته ناموفق بود: {exc}", "error")
    if changed:
        S.add_log(
            f"دسته {changed} پیام به «{category}» تغییر کرد (از گزارش)", "info",
        )
        _maybe_auto_report(force=True)
    return jsonify(ok=True, changed=changed)


# ---------------- گزارش ----------------


def _make_export():
    """ساخت «خروجی جداگانه»: فایل HTML جدید با نام زمان‌دار (نسخه ۴.۶)

    هر بار یک فایل تازه ساخته می‌شود و در فهرست خروجی‌ها ثبت می‌گردد؛
    گزارش زنده (report.html) دست‌نخورده باقی می‌ماند.
    خروجی: (entry یا None، پیام خطا)
    """
    with S.lock:
        msgs = list(S.messages)
        title = S.chat_title or None
    if not msgs:
        return None, "پیامی ذخیره نشده است"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    name = time.strftime("report_%Y%m%d_%H%M%S") + ".html"
    path = os.path.join(OUTPUT_DIR, name)
    try:
        build_report(msgs, path, group_title=title, media_base=MEDIA_DIR)
    except OSError as exc:
        return None, str(exc)
    entry = {
        "name": name,
        "url": f"/output/{name}",
        "count": len(msgs),
        "when": now_str(),
        "time": int(time.time()),
        "size": os.path.getsize(path),
        "title": title or "",
    }
    with S.lock:
        S.exports.insert(0, entry)
        S.exports = S.exports[:60]  # نگهداری حداکثر ۶۰ خروجی اخیر
        S._save_exports()
    S.add_log(
        f"خروجی جداگانه ساخته شد: {name} ({len(msgs)} پیام)",
        "ok",
    )
    return entry, ""


@app.route("/api/report", methods=["POST"])
def api_report():
    """ساخت خروجی جداگانه جدید — هر بار یک فایل تازه با تاریخ و ساعت"""
    entry, err = _make_export()
    if entry is None:
        return jsonify(ok=False, error=err), 400
    return jsonify(
        ok=True,
        url=f"{entry['url']}?ts={int(time.time())}",
        name=entry["name"],
        count=entry["count"],
        path=os.path.join(OUTPUT_DIR, entry["name"]),
    )


@app.route("/api/export", methods=["POST"])
def api_export():
    """همان ساخت گزارش — با نام روشن‌تر «گرفتن خروجی جداگانه"""
    return api_report()


@app.route("/api/exports/delete", methods=["POST"])
def api_exports_delete():
    """حذف یک فایل خروجی از فهرست و از روی دیسک"""
    data = request.get_json(silent=True) or {}
    name = str(data.get("name") or "").strip()
    if (
        not name
        or "/" in name
        or "\\" in name
        or ".." in name
        or not name.startswith("report_")
        or not name.endswith(".html")
    ):
        return jsonify(ok=False, error="نام فایل معتبر نیست"), 400
    with S.lock:
        found = any(e.get("name") == name for e in S.exports)
    if not found:
        return jsonify(ok=False, error="این خروجی در فهرست نیست"), 404
    try:
        os.remove(os.path.join(OUTPUT_DIR, name))
    except OSError as exc:
        return jsonify(ok=False, error=str(exc)), 500
    with S.lock:
        S.exports = [e for e in S.exports if e.get("name") != name]
        S._save_exports()
        if S.report_url == f"/output/{name}":
            S.report_ready = False
            S.report_url = ""
    S.add_log(f"خروجی «{name}» حذف شد", "info")
    return jsonify(ok=True)


@app.route("/api/reset", methods=["POST"])
def api_reset():
    """پاک‌سازی پیام‌های قبلی و شروع دور جدید (نسخه ۴.۶)

    گزینه‌ها (همه اختیاری):
        clear_raw     — حذف آرشیو خام و عکس‌های دانلودشده هم (پاک‌سازی کامل)
        clear_reports — حذف همه فایل‌های خروجی قبلی هم
        skip_server   — پیام‌های موجود در صف سرور بله تأیید و رد شوند
                        (دیگر هیچ‌وقت خوانده نشوند)
        resync        — بعد از پاک‌سازی، دوباره از بات همگام‌سازی شود
    """
    data = request.get_json(silent=True) or {}
    clear_raw = bool(data.get("clear_raw"))
    clear_reports = bool(data.get("clear_reports"))
    skip_server = bool(data.get("skip_server"))
    resync = bool(data.get("resync"))

    with S.lock:
        S.gen += 1  # کارگر فعال سریع خارج می‌شود
        S.stop_event.set()
        S.messages = []
        S.seen_updates = set()
        S.session_count = 0
        S.queue_hint = False
        try:
            save_messages(S.messages, MESSAGES_PATH)
        except OSError as exc:
            S.add_log(f"ذخیره پس از پاک‌سازی ناموفق بود: {exc}", "error")
        removed_reports = 0
        if clear_raw:
            S.raw = []
            S.raw_ids = set()
            S.offset = 0
            try:
                os.remove(RAW_PATH)
            except OSError:
                pass
            try:
                for fn in os.listdir(MEDIA_DIR):
                    p = os.path.join(MEDIA_DIR, fn)
                    if os.path.isfile(p):
                        os.remove(p)
            except OSError:
                pass
        if clear_reports:
            for e in list(S.exports):
                try:
                    os.remove(os.path.join(OUTPUT_DIR, str(e.get("name") or "")))
                    removed_reports += 1
                except OSError:
                    pass
            S.exports = []
            try:
                os.remove(EXPORTS_PATH)
            except OSError:
                pass
            try:
                os.remove(os.path.join(OUTPUT_DIR, "report.html"))
            except OSError:
                pass
            S.report_ready = False
            S.report_url = ""
            S.last_report_ts = 0.0
    note = "پیام‌های ذخیره‌شده پاک شد — دور جدید آماده است"
    if clear_reports:
        note += f" ({removed_reports} فایل خروجی هم حذف شد)"
    if clear_raw:
        note += " — آرشیو خام و عکس‌ها هم پاک شد"
    S.add_log(note, "warn")

    token = _current_token()
    if (skip_server or resync) and token:
        def _post_reset():
            with S.lock:
                old_thread = S.thread
            if old_thread is not None:
                old_thread.join(timeout=30)  # خروج کامل کارگر قبلی
            if skip_server:
                try:
                    n = _skip_server_backlog(BaleClient(token))
                    with S.lock:
                        S.offset = max(S.offset, 0)
                    if n:
                        S.add_log(
                            f"{n} پیام قدیمی صف سرور بله رد شد — دیگر خوانده نمی‌شوند",
                            "info",
                        )
                    else:
                        S.add_log("صف سرور بله از قبل خالی بود", "info")
                    _save_settings()
                except BaleBotError as exc:
                    S.add_log(f"رد کردن صف سرور ناموفق بود: {exc}", "error")
            if resync:
                if _start_worker(token, draining=True):
                    S.add_log(
                        "همگام‌سازی دوباره آغاز شد — پیام‌های جدید خوانده می‌شوند",
                        "info",
                    )
        threading.Thread(target=_post_reset, daemon=True).start()
    return jsonify(ok=True, removed_reports=removed_reports)


def _skip_server_backlog(client):
    """رد کردن (تأیید) همه آپدیت‌های موجود در صف سرور بله

    فقط برای «شروع کاملاً تازه» استفاده می‌شود؛ آپدیت‌های ردشده
    برای همیشه از سرور حذف می‌شوند و دیگر خوانده نمی‌شوند.
    """
    skipped = 0
    for _ in range(30):
        updates = client.get_updates(offset=0, limit=100, timeout=0) or []
        if not updates:
            return skipped
        uids = [
            u.get("update_id")
            for u in updates
            if isinstance(u, dict) and u.get("update_id") is not None
        ]
        if not uids:
            return skipped
        client.get_updates(offset=max(uids) + 1, limit=1, timeout=0)
        skipped += len(updates)
    return skipped


def _start_worker(token, draining=False):
    """شروع رشته دریافت (بدون چک توکن — فقط برای استفاده داخلی)"""
    with S.lock:
        if S.running:
            return False
        S.rules_saved = True
        S.error = ""
        S.stop_event.clear()
        S.draining = bool(draining)
        S.running = True
        S.started_once = True
        S.thread = threading.Thread(target=_collector_worker, args=(token,), daemon=True)
        S.thread.start()
    return True


@app.route("/api/backup")
def api_backup():
    """دانلود فایل پشتیبان کامل (پیام‌ها + آرشیو خام) — نسخه ۴.۵

    برای انتقال امن داده‌ها بین پوشه‌ها و نسخه‌های برنامه؛ همین فایل با
    دکمه «ورود پیام‌های قدیمی / پشتیبان» در هر نسخه دیگر بازیابی می‌شود.
    """
    with S.lock:
        payload = {
            "app": APP_NAME,
            "version": VERSION,
            "exported": now_str(),
            "messages": list(S.messages),
            "raw_updates": list(S.raw),
        }
    filename = f"bale_backup_{time.strftime('%Y%m%d_%H%M%S')}.json"
    body = json.dumps(payload, ensure_ascii=False)
    resp = app.response_class(body, mimetype="application/json")
    resp.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return resp


@app.route("/api/clear_error", methods=["POST"])
def api_clear_error():
    with S.lock:
        S.error = ""
    return jsonify(ok=True)


@app.route("/api/recover_raw", methods=["POST"])
def api_recover_raw():
    """بازسازی پیام‌ها از بایگانی خام — حتی اگر پردازش قبلی ناقص بوده باشد

    (از نسخه ۴.۴ این کار هنگام اجرا/اتصال هم به‌طور خودکار انجام می‌شود)
    """
    token = _current_token()
    client = BaleClient(token) if token else None
    recovered = _recover_from_raw(client)
    if recovered:
        S.add_log(f"{recovered} پیام از بایگانی خام بازیابی شد", "info")
        _build_report_auto()
    else:
        S.add_log("پیام بازیابی‌نشده‌ای در بایگانی خام وجود ندارد", "info")
    return jsonify(ok=True, recovered=recovered)


# ---------------- ابزارها ----------------


def _current_token():
    with S.lock:
        if S.token:
            return S.token
    # اگر کاربر قبلاً توکن را ذخیره کرده باشد
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        tok = str(data.get("token") or "").strip()
        if tok:
            with S.lock:
                S.token = tok
            return tok
    except (OSError, json.JSONDecodeError):
        pass
    return ""


def _save_settings():
    with S.lock:
        data = {
            "token": S.token,
            "chat_id": S.chat_id,
            "chat_title": S.chat_title,
            "rules": S.rules_text,
            "target": S.target,
            "offset": S.offset,
            "known_chats": S.known_chats,
        }
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def _find_free_port(start=5000, tries=10):
    """اولین پورت آزاد از start به بعد — تا دو نسخه برنامه با هم تداخل نکنند"""
    import socket

    for port in range(start, start + tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start


def main():
    port = _find_free_port(int(os.environ.get("PORT", 5000)))
    url = f"http://127.0.0.1:{port}"
    print(f"{APP_NAME} — {VERSION_LABEL} — روی {url} در حال اجراست — مرورگر باز می‌شود ...")
    if _current_token():
        # اگر قبلاً توکن ذخیره شده، دریافت زنده بلافاصله و بدون دکمه آغاز می‌شود
        threading.Timer(0.5, _ensure_worker).start()
    threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    app.run(host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    main()
