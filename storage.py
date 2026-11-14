# -*- coding: utf-8 -*-
"""ذخیره و بارگذاری پیام‌ها + ورود فایل‌های CSV (خروجی bale_chat_backup) و JSON"""

import csv
import json
import os
import tempfile


def make_message(
    message_id=None,
    sender_name="",
    username="",
    sender_id=None,
    chat_id=None,
    chat_title="",
    text="",
    date=None,
    date_text="",
    hour_text="",
    update_id=None,
    category="",
    caption="",
    media=None,
    media_group_id=None,
    reply_to=None,
    forward=None,
    chat_type="",
):
    """ساخت دیکشنری استاندارد یک پیام (شامل رسانه، پاسخ و بازنشر)"""
    return {
        "message_id": message_id,
        "update_id": update_id,
        "chat_id": chat_id,
        "chat_title": chat_title or "",
        "chat_type": str(chat_type or ""),
        "sender_id": sender_id,
        "sender_name": sender_name or "",
        "username": username or "",
        "text": text or "",
        "caption": caption or "",
        "date": date if isinstance(date, int) else None,
        "date_text": str(date_text or ""),
        "hour_text": str(hour_text or ""),
        "category": category or "",
        "media": media if isinstance(media, list) else [],
        "media_group_id": media_group_id or None,
        "reply_to": reply_to if isinstance(reply_to, dict) else None,
        "forward": forward if isinstance(forward, dict) else None,
    }


def load_messages(path):
    """خواندن messages.json — در صورت خرابی فایل، لیست خالی"""
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, list):
        return []
    return [m for m in data if isinstance(m, dict)]


def save_json(data, path, indent=None):
    """ذخیره اتمیک هر ساختار JSON (بدون خطر خراب شدن فایل در حین نوشتن)"""
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def save_messages(messages, path):
    """ذخیره اتمیک لیست پیام‌ها"""
    save_json(messages, path, indent=2)


def _field(row, keys):
    """یافتن مقدار یک فیلد در دیکشنری؛ ابتدا تطبیق دقیق، سپس تطبیق جزئی"""
    lowered = [k.lower() for k in keys]
    # مرحله ۱: تطبیق دقیق نام ستون
    for k, v in row.items():
        kl = str(k or "").strip().lower()
        if kl in lowered and v is not None and str(v).strip():
            return str(v).strip()
    # مرحله ۲: تطبیق جزئی (مثل «متن پیام» در CSV ابزار بکاپ)
    for k, v in row.items():
        kl = str(k or "").strip().lower()
        for key in lowered:
            if key in kl and v is not None and str(v).strip():
                return str(v).strip()
    return ""


def _to_int(value):
    try:
        return int(str(value).strip())
    except (ValueError, TypeError):
        return None


def import_csv(path):
    """ورود پیام‌ها از CSV — سازگار با خروجی bale_chat_backup

    ستون‌های آن ابزار: «تاریخ»، «فرستنده»، «ساعت»، «متن پیام»
    ستون‌های انگلیسی هم پذیرفته می‌شود.
    """
    out = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            text = _field(row, ["متن پیام", "متن", "text", "message", "پیام"])
            sender = _field(row, ["فرستنده", "sender", "نام", "user", "کاربر"])
            d = _field(row, ["تاریخ", "date"])
            h = _field(row, ["ساعت", "time", "hour"])
            chat = _field(row, ["گروه", "chat"])
            if not text and not sender:
                continue
            ts = _to_int(d)
            out.append(
                make_message(
                    sender_name=sender,
                    chat_title=chat,
                    text=text,
                    date=ts,
                    date_text=d if ts is None else "",
                    hour_text=h,
                )
            )
    return out


def import_json(path):
    """ورود پیام‌ها از فایل JSON (خروجی سایر ابزارها یا messages.json)"""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = data.get("messages") or data.get("result") or []
    if not isinstance(data, list):
        raise ValueError("ساختار فایل JSON قابل قبول نیست (باید لیست پیام‌ها باشد)")
    out = []
    for item in data:
        if not isinstance(item, dict):
            continue
        text = _field(item, ["text", "متن"])
        sender = _field(item, ["sender_name", "sender", "فرستنده", "نام"])
        chat = _field(item, ["chat_title", "chat", "گروه"])
        d = _field(item, ["date", "زمان", "تاریخ"])
        h = _field(item, ["hour_text", "ساعت", "time"])
        ts = _to_int(d)
        media = item.get("media")
        out.append(
            make_message(
                message_id=_to_int(_field(item, ["message_id"])),
                update_id=_to_int(_field(item, ["update_id"])),
                sender_name=sender,
                username=_field(item, ["username"]),
                chat_id=_to_int(_field(item, ["chat_id"])),
                chat_title=chat,
                text=text,
                caption=_field(item, ["caption", "کپشن"]),
                date=ts,
                date_text=d if ts is None else "",
                hour_text=h,
                media=media if isinstance(media, list) else None,
                media_group_id=_field(item, ["media_group_id"]) or None,
                reply_to=item.get("reply_to") if isinstance(item.get("reply_to"), dict) else None,
                forward=item.get("forward") if isinstance(item.get("forward"), dict) else None,
                chat_type=_field(item, ["chat_type"]),
            )
        )
    return out


def dedupe_key(msg):
    """کلید یکتا برای جلوگیری از ورود تکراری پیام‌ها"""
    return "|".join(
        [
            str(msg.get("chat_id")),
            str(msg.get("sender_name")),
            str(msg.get("text"))[:100],
            str(msg.get("date")),
            str(msg.get("date_text")),
            str(msg.get("hour_text")),
        ]
    )


def merge_messages(base, incoming):
    """افزودن پیام‌های جدید به لیست موجود بدون تکرار؛ تعداد افزوده‌شده را برمی‌گرداند

    پیام‌هایی که update_id دارند با همان شناسه هم چک می‌شوند تا فایل پشتیبان
    یا messages.json هرچقدر هم دوباره وارد شود، هیچ تکراری ساخته نشود.
    """
    seen = {dedupe_key(m) for m in base}
    seen_uids = {
        m.get("update_id") for m in base if m.get("update_id") is not None
    }
    added = 0
    for m in incoming:
        uid = m.get("update_id")
        if uid is not None and uid in seen_uids:
            continue
        k = dedupe_key(m)
        if k in seen:
            continue
        seen.add(k)
        if uid is not None:
            seen_uids.add(uid)
        base.append(m)
        added += 1
    return added
