# -*- coding: utf-8 -*-
"""تبدیل تاریخ میلادی به شمسی (جلالی) — الگوریتم استاندارد و بدون وابستگی"""

from datetime import datetime


def gregorian_to_jalali(gy, gm, gd):
    """تبدیل تاریخ میلادی به (سال، ماه، روز) جلالی"""
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy + 1 if gm > 2 else gy
    days = (
        355666
        + (365 * gy)
        + ((gy2 + 3) // 4)
        - ((gy2 + 99) // 100)
        + ((gy2 + 399) // 400)
        + gd
        + g_d_m[gm - 1]
    )
    jy = -1595 + (33 * (days // 12053))
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + (days // 31)
        jd = 1 + (days % 31)
    else:
        jm = 7 + ((days - 186) // 30)
        jd = 1 + ((days - 186) % 30)
    return jy, jm, jd


def jalali_str(dt):
    """رشته تاریخ شمسی از یک datetime یا timestamp"""
    if dt is None:
        return ""
    if isinstance(dt, (int, float)):
        try:
            dt = datetime.fromtimestamp(dt)
        except (ValueError, OSError, OverflowError):
            return ""
    jy, jm, jd = gregorian_to_jalali(dt.year, dt.month, dt.day)
    return f"{jy}/{jm:02d}/{jd:02d}"


def format_ts(ts, with_time=True):
    """نمایش خوانا و شمسی یک timestamp یونیکس"""
    if ts in (None, "", 0):
        return ""
    try:
        dt = datetime.fromtimestamp(int(ts))
    except (ValueError, OSError, OverflowError):
        return ""
    out = jalali_str(dt)
    if with_time:
        out += f" — {dt.strftime('%H:%M')}"
    return out


def now_str():
    """تاریخ و ساعت فعلی به شمسی برای سربرگ گزارش"""
    dt = datetime.now()
    return f"{jalali_str(dt)} — {dt.strftime('%H:%M')}"
