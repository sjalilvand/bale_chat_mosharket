# -*- coding: utf-8 -*-
"""نرمال‌سازی آپدیت‌های خام API بله به ساختار استاندارد برنامه

پشتیبانی کامل از انواع محتوا:
    - پیام گروه، سوپرگروه، کانال و چت خصوصی (message / edited_message /
      channel_post / edited_channel_post)
    - عکس و آلبوم عکس (media_group_id)، ویدیو، ویس، آهنگ، فایل و استیکر
    - کپشن (توضیح زیر عکس/ویدیو)
    - پاسخ‌ها و کامنت‌ها (reply_to_message)
    - اطلاعات بازنشر/فوروارد (فرمت قدیمی و جدید forward_origin)
"""

from storage import make_message

MEDIA_TYPES = ("photo", "video", "voice", "audio", "document", "sticker", "animation")


def _s(v):
    """تبدیل امن به رشته پاک‌شده"""
    return str(v or "").strip()


def _snippet(text, limit=140):
    text = _s(text).replace("\n", " ")
    if len(text) > limit:
        return text[:limit] + "…"
    return text


def _sender_name(user):
    """ساخت نام نمایشی فرستنده از شیء کاربر"""
    if not isinstance(user, dict):
        return ""
    parts = [_s(user.get("first_name")), _s(user.get("last_name"))]
    name = " ".join(p for p in parts if p)
    return name or _s(user.get("username"))


def _pick_photo(photo):
    """انتخاب بزرگ‌ترین سایز عکس از آرایه PhotoSize"""
    if not isinstance(photo, list) or not photo:
        return None
    best = None
    best_area = -1
    for p in photo:
        if not isinstance(p, dict):
            continue
        area = (p.get("width") or 0) * (p.get("height") or 0)
        if area >= best_area:
            best, best_area = p, area
    return best


def _extract_media(src):
    """استخراج لیست رسانه‌های یک پیام (عکس/ویدیو/صوت/فایل/استیکر)"""
    media = []

    photo = _pick_photo(src.get("photo"))
    if photo:
        media.append({
            "type": "photo",
            "file_id": _s(photo.get("file_id")),
            "width": photo.get("width"),
            "height": photo.get("height"),
            "name": "عکس",
        })

    video = src.get("video")
    if isinstance(video, dict):
        media.append({
            "type": "video",
            "file_id": _s(video.get("file_id")),
            "width": video.get("width"),
            "height": video.get("height"),
            "duration": video.get("duration"),
            "size": video.get("file_size"),
            "name": _s(video.get("file_name")) or "ویدیو",
        })

    animation = src.get("animation")
    if isinstance(animation, dict):
        media.append({
            "type": "animation",
            "file_id": _s(animation.get("file_id")),
            "name": _s(animation.get("file_name")) or "گیف متحرک",
        })

    voice = src.get("voice")
    if isinstance(voice, dict):
        media.append({
            "type": "voice",
            "file_id": _s(voice.get("file_id")),
            "duration": voice.get("duration"),
            "size": voice.get("file_size"),
            "name": "پیام صوتی",
        })

    audio = src.get("audio")
    if isinstance(audio, dict):
        media.append({
            "type": "audio",
            "file_id": _s(audio.get("file_id")),
            "duration": audio.get("duration"),
            "size": audio.get("file_size"),
            "name": _s(audio.get("title")) or _s(audio.get("file_name")) or "آهنگ",
        })

    document = src.get("document")
    if isinstance(document, dict):
        media.append({
            "type": "document",
            "file_id": _s(document.get("file_id")),
            "size": document.get("file_size"),
            "mime": _s(document.get("mime_type")),
            "name": _s(document.get("file_name")) or "فایل",
        })

    sticker = src.get("sticker")
    if isinstance(sticker, dict):
        media.append({
            "type": "sticker",
            "file_id": _s(sticker.get("file_id")),
            "emoji": _s(sticker.get("emoji")),
            "name": f"استیکر {_s(sticker.get('emoji'))}".strip(),
        })

    return media


def _extract_reply(src):
    """استخراج اطلاعات پاسخ/کامنت (reply_to_message)"""
    r = src.get("reply_to_message")
    if not isinstance(r, dict):
        return None
    return {
        "message_id": r.get("message_id"),
        "chat_id": (r.get("chat") or {}).get("id"),
        "sender": _sender_name(r.get("from")) or _s((r.get("chat") or {}).get("title")),
        "snippet": _snippet(r.get("text") or r.get("caption") or "(بدون متن)"),
    }


def _extract_forward(src):
    """استخراج منبع بازنشر — هم فرمت قدیمی و هم forward_origin جدید"""
    # فرمت جدید
    origin = src.get("forward_origin")
    if isinstance(origin, dict):
        otype = _s(origin.get("type"))
        if otype == "channel":
            chat = origin.get("chat") or {}
            return {"source": _s(chat.get("title")) or "کانال", "date": origin.get("date")}
        if otype == "user":
            return {"source": _sender_name(origin.get("sender_user")) or "کاربر",
                    "date": origin.get("date")}
        if otype == "hidden_user":
            return {"source": _s(origin.get("sender_user_name")) or "کاربر",
                    "date": origin.get("date")}
        return {"source": "نامشخص", "date": origin.get("date")}

    # فرمت قدیمی
    if src.get("forward_from_chat"):
        chat = src.get("forward_from_chat") or {}
        return {"source": _s(chat.get("title")) or "کانال",
                "date": src.get("forward_date")}
    if src.get("forward_sender_name"):
        return {"source": _s(src.get("forward_sender_name")),
                "date": src.get("forward_date")}
    if src.get("forward_from"):
        name = _sender_name(src.get("forward_from"))
        if name:
            return {"source": name, "date": src.get("forward_date")}
    return None


MSG_KINDS = ("message", "edited_message", "channel_post", "edited_channel_post")


def normalize_update(upd):
    """تبدیل یک آپدیت خام به دیکشنری استاندارد پیام؛ نامعتبر → None"""
    if not isinstance(upd, dict):
        return None
    uid = upd.get("update_id")
    src = None
    edited = False
    for kind in MSG_KINDS:
        if isinstance(upd.get(kind), dict):
            src = upd[kind]
            edited = kind.startswith("edited")
            break
    if src is None:
        return None

    chat = src.get("chat") or {}
    sender = src.get("from") or {}
    text = _s(src.get("text"))
    caption = _s(src.get("caption"))
    media = _extract_media(src)

    msg = make_message(
        message_id=src.get("message_id"),
        update_id=uid,
        chat_id=chat.get("id"),
        chat_title=_s(chat.get("title")) or _sender_name(sender) or _s(chat.get("first_name")),
        chat_type=_s(chat.get("type")),
        sender_id=(sender.get("id") if isinstance(sender, dict) else None),
        sender_name=_sender_name(sender),
        username=_s(sender.get("username")) if isinstance(sender, dict) else "",
        text=text,
        caption=caption,
        date=src.get("date"),
        media=media,
        media_group_id=_s(src.get("media_group_id")) or None,
        reply_to=_extract_reply(src),
        forward=_extract_forward(src),
    )
    msg["edited"] = edited
    return msg


def normalize_member_update(upd):
    """آپدیت my_chat_member — ربات به گروهی اضافه/حذف شده است؛ برای کشف گروه"""
    if not isinstance(upd, dict):
        return None
    for kind in ("my_chat_member", "chat_member"):
        payload = upd.get(kind)
        if isinstance(payload, dict):
            chat = payload.get("chat") or {}
            return {
                "chat_id": chat.get("id"),
                "title": _s(chat.get("title")) or _s(chat.get("first_name")),
                "type": _s(chat.get("type")),
                "old_status": _s((payload.get("old_chat_member") or {}).get("status")),
                "new_status": _s((payload.get("new_chat_member") or {}).get("status")),
            }
    return None


def has_media(msg):
    return bool(msg.get("media"))
