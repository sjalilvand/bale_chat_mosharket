# کتابخانه جاسازی‌شده PptxGenJS

این فایل نسخه bundle کتابخانه **PptxGenJS نسخه ۳.۱۲.۰** است که به‌صورت
آفلاین داخل فایل گزارش HTML جاسازی می‌شود تا دکمه «خروجی پاورپوینت» حتی
بدون اینترنت کار کند.

- پروژه: https://github.com/gitbrent/PptxGenJS
- مجوز: MIT License — Copyright (c) 2016-2023 Brent Ely
- npm: https://www.npmjs.com/package/pptxgenjs

فایل report.py این فایل را هنگام ساخت گزارش داخل تگ `<script>` قرار می‌دهد
(تابع `_load_pptx_lib`). در صورت نبود این فایل، گزارش به‌طور خودکار از CDN
بارگذاری می‌کند (نیازمند اینترنت).
