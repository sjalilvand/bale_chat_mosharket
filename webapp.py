# -*- coding: utf-8 -*-
"""Bale Chat Mosharket — نسخه وب ۳ (Flask)

داشبورد گرافیکی مدرن در مرورگر برای دریافت، دسته‌بندی و ساخت گزارش HTML
از پیام‌های گروه‌های پیام‌رسان بله، همراه با نمایش زنده روند پیشرفت.

امکانات نسخه ۳:
    - افزودن گروه با لینک دعوت ble.ir/join/... (با راهنمای گام‌به‌گام)
    - خواندن همه انواع پیام: عکس، آلبوم، ویدیو، ویس، فایل، کپشن،
      کامنت‌ها (پاسخ‌ها)، بازنشرها و پیام‌های کانال
    - دانلود خودکار عکس‌ها و نمایش آن‌ها در داشبورد و گزارش HTML
    - ذخیره پیام‌هایی که به ربات فوروارد می‌شوند (چت خصوصی)

اجرا:
    python main.py        →  http://127.0.0.1:5000
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
from categorizer import Categorizer, FALLBACK, parse_rules
from collector import normalize_member_update, normalize_update
from jalali import format_ts, now_str
from report import build_report
from storage import (
    import_csv,
    import_json,
    load_messages,
    make_message,
    merge_messages,
    save_messages,
)

BASE = os.path.dirname(os.path.abspath(__file__))
MESSAGES_PATH = os.path.join(BASE, "messages.json")
SETTINGS_PATH = os.path.join(BASE, "settings.json")
MEDIA_DIR = os.path.join(BASE, "media")
OUTPUT_DIR = os.path.join(BASE, "output")

DEFAULT_RULES = """اطلاعیه: اطلاعیه، اعلام، هماهنگ، توجه داشته باشید، مهم
جلسه و قرار: جلسه، قرار، حضوری، آنلاین
پرسش و پاسخ: ؟, ?, چرا، چطور، چگونه، سوال، سؤال، مشکل، راهنمایی
سفارش و امور مالی: سفارش، خرید، قیمت، فاکتور، پرداخت، تخفیف، واریز
تشکر و تعامل: ممنون، تشکر، مرسی، عالی، دست شما درد نکند"""

TYPE_LABELS = {
    "private": "چت خصوصی",
    "group": "گروه",
    "supergroup": "گروه",
    "channel": "کانال",
}

DEMO_MESSAGES = [
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
]


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
        self.started_once = False
        self.stop_event = threading.Event()
        self.thread = None
        self.session_count = 0
        self.target = 50
        self.log = []
        self.report_ready = False
        self.report_url = ""
        self.error = ""
        self._load_settings()

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
        for m in msgs:
            p = m.get("sender_name") or m.get("username") or m.get("sender_id")
            if p:
                people.add(str(p))
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
            "error": S.error,
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
    return jsonify(ok=True, bot={"name": me.get("first_name", ""), "username": me.get("username", "")})


@app.route("/api/groups", methods=["POST"])
def api_groups():
    token = _current_token()
    if not token:
        return jsonify(ok=False, error="ابتدا ربات را متصل کنید"), 400

    # اسکن زنده غیرمخرب (offset=0 تأیید نمی‌کند)؛ اگر دریافت فعال باشد 409 می‌گیریم و بی‌خیال
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
        pass  # هنگام polling فعال؛ لیست از پیام‌های ذخیره‌شده ساخته می‌شود

    groups = S.groups_snapshot()
    S.add_log(f"{len(groups)} گفتگو شناسایی شد", "info")
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
    S.add_log("دریافت پیام‌ها آغاز شد", "info")
    return jsonify(ok=True)


@app.route("/api/stop", methods=["POST"])
def api_stop():
    if S.running:
        S.stop_event.set()
        S.add_log("دستور توقف دریافت صادر شد", "info")
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


def _collector_worker(token):
    try:
        client = BaleClient(token)
        try:
            me = client.get_me()
            S.add_log(
                f"متصل شد — ربات: {me.get('first_name', '')} (@{me.get('username', '')})",
                "info",
            )
        except BaleBotError:
            pass
        offset = 0
        while not S.stop_event.is_set():
            try:
                updates = client.get_updates(offset=offset, limit=100, timeout=20) or []
            except BaleBotError as exc:
                S.add_log(f"{exc} — تلاش مجدد پس از ۵ ثانیه", "error")
                for _ in range(50):
                    if S.stop_event.is_set():
                        break
                    time.sleep(0.1)
                continue
            for upd in updates:
                uid = upd.get("update_id")
                if uid is not None:
                    if uid < offset:
                        continue
                    offset = uid + 1

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
                    continue

                msg = normalize_update(upd)
                if msg is None:
                    continue

                chat_id = msg.get("chat_id")
                ctype = msg.get("chat_type") or ""
                S.record_chat(chat_id, msg.get("chat_title"), ctype)

                # فیلتر گفتگو: پیام‌های چت خصوصی (فوروارد کاربر) همیشه ذخیره می‌شوند
                if S.chat_id is not None and ctype != "private" and chat_id != S.chat_id:
                    continue

                cat_text = (msg.get("text") or msg.get("caption") or "").strip()
                if cat_text.startswith("/"):
                    continue  # دستورات ربات ذخیره نمی‌شوند

                # دانلود رسانه‌ها (عکس/ویدیو/فایل)
                if msg.get("media"):
                    n = _download_media(client, msg)
                    if n:
                        S.add_log(f"{n} فایل رسانه ذخیره شد", "info")

                msg["category"] = (
                    S.categorizer.categorize(cat_text) if cat_text else FALLBACK
                )

                with S.lock:
                    # اگر پیام ویرایش‌شده باشد، نسخه قبلی جایگزین می‌شود
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
                    if uid is not None:
                        S.seen_updates.add(uid)
                    try:
                        save_messages(S.messages, MESSAGES_PATH)
                    except OSError as exc:
                        S.add_log(f"ذخیره فایل پیام‌ها ناموفق بود: {exc}", "error")

                kind = "ویرایش" if msg.get("edited") else "پیام"
                shown = cat_text[:44] + ("…" if len(cat_text) > 44 else "") or (
                    f"[{len(msg.get('media') or [])} رسانه]"
                    if msg.get("media")
                    else "(بدون متن)"
                )
                S.add_log(
                    f"{kind} #{len(S.messages)} — {msg['sender_name']}: {shown} ← دسته: {msg['category']}",
                    "msg",
                )
        with S.lock:
            S.running = False
        S.add_log("دریافت پیام متوقف شد", "info")
    except Exception as exc:  # محافظت از رشته پس‌زمینه
        with S.lock:
            S.running = False
        S.add_log(f"خطای غیرمنتظره در دریافت: {exc}", "error")


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
            t = (m.get("text") or m.get("caption") or "").strip()
            m["category"] = S.categorizer.categorize(t) if t else FALLBACK
        save_messages(S.messages, MESSAGES_PATH)
    S.add_log(f"{len(rules)} دسته فعال و بر {len(S.messages)} پیام اعمال شد", "info")
    _save_settings()
    return jsonify(ok=True, count=len(rules))


@app.route("/api/import", methods=["POST"])
def api_import():
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify(ok=False, error="فایلی ارسال نشد"), 400
    suffix = ".csv" if f.filename.lower().endswith(".csv") else ".json"
    path = os.path.join(tempfile.gettempdir(), f"bale_import_{int(time.time())}{suffix}")
    f.save(path)
    try:
        incoming = import_csv(path) if suffix == ".csv" else import_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        S.add_log(f"خطای ورود فایل {f.filename}: {exc}", "error")
        return jsonify(ok=False, error=str(exc)), 400
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
    with S.lock:
        added = merge_messages(S.messages, incoming)
        save_messages(S.messages, MESSAGES_PATH)
    S.add_log(f"{added} پیام از فایل «{f.filename}» وارد شد", "info")
    return jsonify(ok=True, added=added)


@app.route("/api/demo", methods=["POST"])
def api_demo():
    """افزودن پیام‌های نمونه برای پیش‌نمایش داشبورد و گزارش"""
    data = request.get_json(silent=True) or {}
    n = max(1, min(30, int(data.get("count") or 10)))
    added = 0
    with S.lock:
        title = S.chat_title or "گروه مشارکت های مردمی (نمونه)"
        base = len(S.messages)
        demo_id = 990000 + base
        for i in range(n):
            name, text = DEMO_MESSAGES[(base + i) % len(DEMO_MESSAGES)]
            msg = make_message(
                sender_name=name,
                chat_title=title,
                text=text,
                date=int(time.time()) - (n - i) * 420,
            )
            msg["category"] = S.categorizer.categorize(text)
            S.messages.append(msg)
            added += 1
        save_messages(S.messages, MESSAGES_PATH)
    S.add_log(f"{added} پیام نمونه برای تست اضافه شد", "info")
    return jsonify(ok=True, added=added)


@app.route("/api/messages", methods=["GET"])
def api_messages():
    with S.lock:
        msgs = list(S.messages)
    return jsonify(ok=True, count=len(msgs), messages=msgs[-200:])


# ---------------- گزارش ----------------


@app.route("/api/report", methods=["POST"])
def api_report():
    with S.lock:
        msgs = list(S.messages)
        title = S.chat_title or None
    if not msgs:
        return jsonify(ok=False, error="پیامی ذخیره نشده است"), 400
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    name = "report.html"
    try:
        path = build_report(
            msgs,
            os.path.join(OUTPUT_DIR, name),
            group_title=title,
            media_base=MEDIA_DIR,
        )
    except OSError as exc:
        return jsonify(ok=False, error=str(exc)), 500
    with S.lock:
        S.report_ready = True
        S.report_url = f"/output/{name}"
    S.add_log(f"گزارش HTML ساخته شد ({len(msgs)} پیام)", "info")
    return jsonify(ok=True, url=f"/output/{name}?ts={int(time.time())}", path=path)


@app.route("/api/clear_error", methods=["POST"])
def api_clear_error():
    with S.lock:
        S.error = ""
    return jsonify(ok=True)


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
            "known_chats": S.known_chats,
        }
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def main():
    port = int(os.environ.get("PORT", 5000))
    threading.Timer(
        1.5, lambda: webbrowser.open(f"http://127.0.0.1:{port}")
    ).start()
    app.run(host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    main()
