# -*- coding: utf-8 -*-
"""دسته‌بندی کلیدواژه‌ای متن پیام‌ها

قالب قوانین (هر خط یک دسته):
    نام دسته: کلیدواژه۱، کلیدواژه۲ | کلیدواژه۳
اگر هر یک از کلیدواژه‌ها داخل متن پیام باشد، پیام به همان دسته می‌رود
(اولین دسته‌ای که در متنش تطبیق دارد). پیام‌های بدون تطبیق به دسته
پیش‌فرض «سایر» می‌روند.
"""

FALLBACK = "سایر"


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
