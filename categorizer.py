# -*- coding: utf-8 -*-
"""دسته‌بندی کلیدواژه‌ای متن پیام‌ها + دسته‌بندی پیام‌های رسانه‌ای

قالب قوانین (هر خط یک دسته):
    نام دسته: کلیدواژه۱، کلیدواژه۲ | کلیدواژه۳
اگر هر یک از کلیدواژه‌ها داخل متن پیام باشد، پیام به همان دسته می‌رود
(اولین دسته‌ای که در متنش تطبیق دارد). پیام‌های بدون تطبیق به دسته
پیش‌فرض «سایر» می‌روند؛ پیام‌های فقط عکس/رسانه به دسته «عکس و مستندات».
"""

FALLBACK = "سایر"
PHOTO_CATEGORY = "عکس و مستندات"
MEDIA_CATEGORY = "رسانه و فایل"

# قوانین پیش‌فرض حوزه مشارکت‌های مردمی — در webapp و report استفاده می‌شود
# (فهرست دسته‌های استاندارد برای «تغییر دسته» در حالت ویرایش گزارش هم از همین‌جا می‌آید)
DEFAULT_RULES = """اطلاعیه و ابلاغیه: اطلاعیه، ابلاغ، اعلام، بخشنامه، دستور، توجه داشته باشید، مهم، فوری، تذکر
جلسه و قرار: جلسه، قرار، حضوری، آنلاین، دستور جلسه، حضور، وقت ملاقات
گزارش عملکرد: گزارش، عملکرد، فعالیت، اقدام، اجرا، پیشرفت، آمار، نتیجه
هماهنگی و برنامه‌ریزی: هماهنگ، برنامه‌ریزی، برنامه، زمان‌بندی، دستور کار، تقویم
پرسش و پاسخ: ؟, ?, چرا، چطور، چگونه، سوال، سؤال، مشکل، راهنمایی
درخواست و پیگیری: درخواست، پیگیری، استعلام، بفرستید، ارسال کنید، اعلام کنید
تشکر و تعامل: ممنون، تشکر، مرسی، عالی، دست شما درد نکند، خسته نباشید، سلام، درود
سفارش و امور مالی: سفارش، خرید، قیمت، فاکتور، پرداخت، تخفیف، واریز، هزینه، بودجه"""


def categorize_message(categorizer, msg, text=None):
    """دسته‌بندی یک پیام کامل

    اگر متن یا کپشن دارد: بر اساس کلیدواژه‌ها؛
    اگر فقط رسانه دارد: «عکس و مستندات» (عکس/استیکر) یا «رسانه و فایل»؛
    در غیر این صورت: «سایر».
    دسته‌بندی بر اساس داده‌های موجود خود پیام انجام می‌شود.
    """
    t = (msg.get("text") or msg.get("caption") or "").strip() if text is None else text.strip()
    if t:
        return categorizer.categorize(t)
    media = msg.get("media") or []
    if any(x.get("type") in ("photo", "sticker") for x in media):
        return PHOTO_CATEGORY
    if media:
        return MEDIA_CATEGORY
    return FALLBACK


def parse_rules(text):
    """تبدیل متن قوانین به لیست (نام دسته، [کلیدواژه‌ها])"""
    rules = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        name, kws = line.split(":", 1)
        name = name.strip()
        kws = [
            k.strip()
            for k in kws.replace("،", ",").replace("|", ",").split(",")
            if k.strip()
        ]
        if name and kws:
            rules.append((name, kws))
    return rules


class Categorizer:
    """طبقه‌بندی متن بر اساس قوانین کلیدواژه‌ای"""

    def __init__(self, rules):
        self.rules = [(n, [k.lower() for k in ks]) for n, ks in rules]

    def categorize(self, text):
        t = (text or "").lower()
        if not t:
            return FALLBACK
        for name, keywords in self.rules:
            for kw in keywords:
                if kw and kw in t:
                    return name
        return FALLBACK
