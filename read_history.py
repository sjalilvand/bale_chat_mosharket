# -*- coding: utf-8 -*-
"""خواندن همه پیام‌های موجود در چت ربات بله و ساخت یک فایل گزارش HTML

ابزار مستقل و ساده — بدون داشبورد وب. برای وقتی که فقط می‌خواهید همه
پیام‌های ارسالی به ربات (متن، عکس، کپشن، کامنت‌ها و بازنشرها) در «یک
فایل HTML» ذخیره شود.

روش استفاده:
    1) پیام‌های قدیمی گروه را به چت خصوصی ربات فوروارد کنید
    2) کنار همین فایل دستور زیر را اجرا کنید:
           python read_history.py
    3) توکن ربات را وارد کنید (برای دفعات بعد ذخیره می‌شود)
    4) Enter بزنید — همه پیام‌ها خوانده می‌شود و فایل گزارش
       به‌طور خودکار ساخته و در مرورگر باز می‌شود

نکته‌ها:
    - هر آپدیت قبل از هر پردازشی در «raw_updates.json» بایگانی می‌شود؛
      حتی اگر وسط کار برق قطع شود هیچ پیامی گم نمی‌شود و دفعه بعد
      خودکار از بایگانی بازیابی می‌شود.
    - سرور بله فقط آخرین ~۲۰۰۰ آپدیت را تا ۲۴ ساعت نگه می‌دارد؛ پس
      بعد از فوروارد کردن پیام‌ها، این ابزار را زودتر اجرا کنید.
    - فقط یکی از دو برنامه (این ابزار یا داشبورد وب) را همزمان اجرا کنید.
"""

import json
import os
import sys
import time
import webbrowser

from bale_client import BaleBotError, BaleClient
from categorizer import Categorizer, FALLBACK, parse_rules
from collector import normalize_member_update, normalize_update
from report import build_report
from storage import load_messages, save_json, save_messages

BASE = os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH = os.path.join(BASE, "settings.json")
MESSAGES_PATH = os.path.join(BASE, "messages.json")
RAW_PATH = os.path.join(BASE, "raw_updates.json")
MEDIA_DIR = os.path.join(BASE, "media")
OUTPUT_DIR = os.path.join(BASE, "output")
REPORT_PATH = os.path.join(OUTPUT_DIR, "report.html")

DEFAULT_RULES = """اطلاعیه: اطلاعیه، اعلام، هماهنگ، توجه داشته باشید، مهم
جلسه و قرار: جلسه، قرار، حضوری، آنلاین
پرسش و پاسخ: ؟, ?, چرا، چطور، چگونه، سوال، سؤال، مشکل، راهنمایی
سفارش و امور مالی: سفارش، خرید، قیمت، فاکتور، پرداخت، تخفیف، واریز
تشکر و تعامل: ممنون، تشکر، مرسی، عالی، دست شما درد نکند"""

DEFAULT_EXT = {
    "photo": ".jpg",
    "video": ".mp4",
    "voice": ".ogg",
    "audio": ".mp3",
    "animation": ".mp4",
    "document": ".bin",
    "sticker": ".webp",
}


def log(text, kind="info"):
    mark = {"info": "•", "ok": "✔", "warn": "⚠", "error": "✖"}.get(kind, "•")
    print(f"{mark} {text}")


def load_settings():
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def load_raw():
    try:
        with open(RAW_PATH, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [u for u in data if isinstance(u, dict)]
    except (OSError, json.JSONDecodeError):
        pass
    return []


def archive_raw(raw, updates):
    """افزودن آپدیت‌های تازه به بایگانی خام — قبل از هر پردازشی"""
    ids = {u.get("update_id") for u in raw if u.get("update_id") is not None}
    added = 0
    for upd in updates:
        if not isinstance(upd, dict):
            continue
        uid = upd.get("update_id")
        if uid is not None and uid in ids:
            continue
        raw.append(upd)
        if uid is not None:
            ids.add(uid)
        added += 1
    if added:
        try:
            save_json(raw, RAW_PATH)
        except OSError as exc:
            log(f"ذخیره بایگانی خام ناموفق بود: {exc}", "warn")
    return added


def download_media(client, msg):
    """دانلود رسانه‌های پیام در پوشه media — نام فایل در item['file']"""
    saved = 0
    for i, item in enumerate(msg.get("media") or []):
        fid = item.get("file_id")
        if not fid or item.get("file"):
            continue
        try:
            info = client.get_file(fid)
            fpath = str(info.get("file_path") or "")
            ext = os.path.splitext(fpath)[1].lower() or DEFAULT_EXT.get(
                item.get("type"), ".bin"
            )
            name = f"u{msg.get('update_id') or 0}_m{msg.get('message_id') or 0}_{i}{ext}"
            client.download_file(fpath, os.path.join(MEDIA_DIR, name))
            item["file"] = name
            saved += 1
        except BaleBotError as exc:
            log(f"دانلود {item.get('type')} ناموفق بود: {exc}", "warn")
    return saved


def process_update(upd, client, categorizer, messages, seen):
    """پردازش یک آپدیت خام؛ تعداد پیام ذخیره‌شده (۰ یا ۱) را برمی‌گرداند"""
    member = normalize_member_update(upd)
    if member:
        if member.get("new_status") in ("member", "administrator", "kicked"):
            log(f"ربات به گفتگوی «{member.get('title')}» {member.get('new_status')} شد")
        return 0
    msg = normalize_update(upd)
    if msg is None:
        return 0
    uid = msg.get("update_id")
    if uid is not None and uid in seen:
        return 0
    text = (msg.get("text") or msg.get("caption") or "").strip()
    if text.startswith("/"):
        return 0  # دستورات ربات ذخیره نمی‌شوند
    if msg.get("media"):
        download_media(client, msg)
    msg["category"] = categorizer.categorize(text) if text else FALLBACK
    # اگر پیام ویرایش‌شده باشد، نسخه قبلی جایگزین می‌شود
    replaced = False
    if msg.get("chat_id") is not None and msg.get("message_id"):
        for idx, old in enumerate(messages):
            if (
                old.get("chat_id") == msg.get("chat_id")
                and old.get("message_id") == msg.get("message_id")
            ):
                messages[idx] = msg
                replaced = True
                break
    if not replaced:
        messages.append(msg)
    if uid is not None:
        seen.add(uid)
    return 1


def run_fetch(client, offset=0, messages=None, seen=None, categorizer=None, raw=None):
    """واکشی همه آپدیت‌های در صف + بازیابی از بایگانی خام + ساخت گزارش

    خلاصه نتیجه را به‌صورت دیکشنری برمی‌گرداند (برای تست هم استفاده می‌شود).
    """
    messages = messages if messages is not None else None
    if messages is None:
        # بارگذاری خودکار پایگاه داده موجود (اجرای دوباره ابزار)
        messages = load_messages(MESSAGES_PATH)
        seen = {m.get("update_id") for m in messages if m.get("update_id") is not None}
    seen = seen if seen is not None else set()
    categorizer = categorizer or Categorizer(parse_rules(DEFAULT_RULES))
    raw = raw if raw is not None else load_raw()

    # ---- مرحله ۱: واکشی همه آپدیت‌های در صف سرور ----
    fetched = 0
    rounds = 0
    while True:
        try:
            updates = client.get_updates(offset=offset, limit=100, timeout=2) or []
        except BaleBotError as exc:
            log(f"{exc} — تلاش مجدد تا ۵ ثانیه دیگر", "warn")
            time.sleep(5)
            continue
        rounds += 1
        if rounds > 300:
            break  # محافظت در برابر حلقه بی‌نهایت
        archived = archive_raw(raw, updates)
        if archived:
            log(f"{archived} آپدیت در بایگانی خام ذخیره شد")
        for upd in updates:
            fetched += process_update(upd, client, categorizer, messages, seen)
            uid = upd.get("update_id") if isinstance(upd, dict) else None
            if uid is not None and uid + 1 > offset:
                offset = uid + 1
        if not updates:
            break
        log(f"… تا اینجا {fetched} پیام جدید خوانده شد")

    # ---- مرحله ۲: بازیابی هر پیامِ بایگانی‌شده‌ای که هنوز ذخیره نشده ----
    recovered = 0
    for upd in raw:
        recovered += process_update(upd, client, categorizer, messages, seen)
    if recovered:
        log(f"{recovered} پیام از بایگانی خام بازیابی شد", "ok")

    # ---- مرحله ۳: ذخیره و ساخت گزارش HTML ----
    save_messages(messages, MESSAGES_PATH)

    if not messages:
        log(
            "هیچ پیامی خوانده نشد. دو دلیل ممکن است:\n"
            "    ۱) هنوز پیامی به چت ربات فوروارد نشده — پیام‌ها را فوروارد کنید و دوباره اجرا کنید\n"
            "    ۲) بیش از ۲۴ ساعت از ارسالشان گذشته (سرور بله آپدیت‌های قدیمی را پاک می‌کند)",
            "warn",
        )
        return {
            "fetched": fetched,
            "recovered": recovered,
            "total": 0,
            "report": "",
            "offset": offset,
        }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    try:
        path = build_report(messages, REPORT_PATH, media_base=MEDIA_DIR)
    except OSError as exc:
        log(f"ساخت گزارش ناموفق بود: {exc}", "error")
        path = ""

    photos = sum(
        1
        for m in messages
        for x in m.get("media") or []
        if x.get("type") in ("photo", "sticker")
    )
    forwards = sum(1 for m in messages if m.get("forward"))
    log(f"مجموع پیام‌های ذخیره‌شده: {len(messages)} (عکس: {photos} — بازنشر: {forwards})", "ok")
    if path:
        log(f"گزارش HTML ساخته شد: {path}", "ok")
        try:
            webbrowser.open("file://" + path)
        except Exception:
            pass
    return {
        "fetched": fetched,
        "recovered": recovered,
        "total": len(messages),
        "report": path,
        "offset": offset,
    }


def main():
    print("=" * 62)
    print("   خواندن همه پیام‌های ربات بله و ساخت گزارش HTML")
    print("=" * 62)

    settings = load_settings()
    token = str(settings.get("token") or "").strip()
    if not token:
        token = input("توکن ربات را وارد کنید (از BotFather): ").strip()
    if not token:
        log("توکن وارد نشد", "error")
        sys.exit(1)

    client = BaleClient(token)
    try:
        me = client.get_me()
    except BaleBotError as exc:
        log(f"اتصال ناموفق: {exc}", "error")
        sys.exit(1)
    log(f"متصل شد: {me.get('first_name', '')} (@{me.get('username', '')})", "ok")

    # ذخیره توکن + خواندن offset قبلی از تنظیمات
    settings["token"] = token
    offset = 0
    try:
        offset = max(0, int(settings.get("offset") or 0))
    except (TypeError, ValueError):
        offset = 0
    try:
        save_json(settings, SETTINGS_PATH)
    except OSError:
        pass

    messages = load_messages(MESSAGES_PATH)
    seen = {m.get("update_id") for m in messages if m.get("update_id") is not None}
    raw = load_raw()
    rules_text = str(settings.get("rules") or DEFAULT_RULES)
    categorizer = Categorizer(parse_rules(rules_text))

    log(f"پیام‌های ذخیره‌شده قبلی: {len(messages)}")
    print()
    print("پیام‌های قدیمی گروه را به چت خصوصی ربات فوروارد کنید؛")
    input("سپس برای شروع خواندن، Enter بزنید ...")
    print()

    result = run_fetch(
        client, offset=offset, messages=messages, seen=seen,
        categorizer=categorizer, raw=raw,
    )

    # ذخیره offset برای ادامه درست در اجرای بعدی (بقیه تنظیمات دست نمی‌خورد)
    settings["offset"] = result.get("offset") or offset
    try:
        save_json(settings, SETTINGS_PATH)
    except OSError:
        pass
    print()
    if result["total"]:
        print("تمام شد! فایل گزارش در مرورگر باز شده است (پوشه output).")
    print("توجه: این ابزار و داشبورد وب هر دو از یک پایگاه داده مشترک استفاده می‌کنند.")


if __name__ == "__main__":
    main()
