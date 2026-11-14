# -*- coding: utf-8 -*-
"""کلاینت سبک برای API رسمی ربات‌های بله (بر پایه مستندات docs.bale.ai)

API بله تقریباً مشابه API ربات تلگرام است:
    https://tapi.bale.ai/bot<TOKEN>/<METHOD>
"""

import requests

API_BASE = "https://tapi.bale.ai/bot"


class BaleBotError(Exception):
    """خطای سطح بالای API بله (شبکه، توکن نامعتبر، پاسخ ناقص و ...)"""


class BaleClient:
    """پوشش ساده روی متدهای موردنیاز برنامه"""

    def __init__(self, token, timeout=35):
        token = (token or "").strip()
        if not token:
            raise BaleBotError("توکن ربات خالی است")
        if ":" not in token:
            raise BaleBotError("قالب توکن معتبر نیست (مثال: 123456:ABC-DEF)")
        self._base = f"{API_BASE}{token}"
        self.timeout = timeout

    def _call(self, method, params=None, timeout=None):
        params = params or {}
        try:
            resp = requests.get(
                f"{self._base}/{method}",
                params=params,
                timeout=timeout or self.timeout,
            )
        except requests.RequestException as exc:
            raise BaleBotError(f"خطای شبکه در تماس با سرور بله: {exc}") from exc
        try:
            data = resp.json()
        except ValueError as exc:
            raise BaleBotError(
                f"پاسخ نامعتبر از سرور بله (کد HTTP {resp.status_code})"
            ) from exc
        if not data.get("ok"):
            desc = data.get("description") or f"خطای API (کد HTTP {resp.status_code})"
            raise BaleBotError(str(desc))
        return data.get("result")

    # ----- متدهای مورداستفاده برنامه -----

    def get_me(self):
        """اطلاعات خود ربات — برای تست اعتبار توکن"""
        return self._call("getMe")

    def get_updates(self, offset=0, limit=100, timeout=20):
        """دریافت آپدیت‌های جدید (long polling).

        سرور بله آخرین ۲۰۰۰ آپدیت را تا ۲۴ ساعت نگه می‌دارد؛
        با ارسال offset آپدیت‌های قبلی تأیید می‌شوند.
        """
        return self._call(
            "getUpdates",
            {"offset": offset, "limit": limit, "timeout": timeout},
            timeout=timeout + 15,
        )

    def get_chat(self, chat_id):
        """اطلاعات یک گفتگو (گروه/کانال/چت خصوصی)"""
        return self._call("getChat", {"chat_id": chat_id})
