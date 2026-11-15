# -*- coding: utf-8 -*-
"""ساخت گزارش HTML تعاملی، قابل ویرایش و دارای خروجی پاورپوینت (نسخه ۵)

قابلیت‌های گزارش نسخه ۵:
    - گروه‌بندی دلخواه: بر اساس «دسته موضوعی»، «تاریخ ارسال» (شمسی) یا «فرستنده»
      و مرتب‌سازی صعودی/نزولی بر اساس زمان، فرستنده یا دسته
    - فیلترها: جست‌وجوی زنده در متن/کپشن/کامنت‌ها، فیلتر چندگانه دسته‌ها (چیپ‌ها)،
      فرستنده، گروه، تاریخ ارسال و «فقط پیام‌های عکس‌دار»
    - حالت انتخاب: تیک‌زدن پیام‌ها و حذف گروهی
    - حذف هر پیام با دکمه ✕ — وقتی گزارش از داخل برنامه باز شده باشد، حذف به
      پایگاه داده برنامه هم همگام می‌شود؛ حذف‌ها در «ذخیره نسخه ویرایش‌شده» هم می‌مانند
    - حالت ویرایش: ویرایش متن پیام‌ها، عنوان گزارش و «موضوع گزارش» (برای تبدیل
      خروجی به گزارش عملکرد حوزه درباره موضوع دلخواه) + تغییر دسته هر پیام
    - ذخیره نسخه ویرایش‌شده: دانلود یک فایل HTML جدید شامل همه ویرایش‌ها/حذف‌ها
    - خروجی پاورپوینت: ۴ تم رنگی، فرمت 16:9 یا 4:3، شامل عکس‌ها (اختیاری) و
      گروه‌بندی اسلایدها بر اساس موضوع یا تاریخ — کتابخانه داخل فایل جاسازی
      شده و حتی بدون اینترنت کار می‌کند
    - عکس‌ها به‌صورت base64 داخل خود فایل جاسازی می‌شوند تا گزارش هر جا و
      بدون برنامه قابل باز کردن باشد
    - مرتبط‌سازی: کامنت‌ها/پاسخ‌ها به‌صورت تو در تو زیر پیام اصلی + پیوند
      «در پاسخ به» با پرش و هایلایت پیام مرتبط
"""

import base64
import html
import io
import os
from collections import Counter
from string import Template

from categorizer import DEFAULT_RULES, parse_rules
from jalali import format_ts, now_str
from version import VERSION

PALETTE = [
    "#0e9f6e", "#2563eb", "#d97706", "#dc2626", "#7c3aed",
    "#0d9488", "#db2777", "#475569", "#9333ea", "#0891b2",
]

PPTX_LIB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "lib", "pptxgen.bundle.js"
)

# ---------------------------------------------------------------- قالب صفحه

PAGE = Template("""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>گزارش عملکرد — $title</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css">
<style>
:root{--primary:#0e9f6e;--primary-dark:#0b7a55;--ink:#1f2937;--muted:#6b7280;
--bg:#f2f5f3;--card:#ffffff;--border:#e5e7eb}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{font-family:Vazirmatn,Tahoma,'Segoe UI',sans-serif;background:var(--bg);
color:var(--ink);margin:0;padding:24px 16px}
.wrap{max-width:960px;margin:0 auto}
.hero{background:linear-gradient(135deg,var(--primary),var(--primary-dark));color:#fff;
border-radius:16px;padding:26px 30px;margin-bottom:18px}
.hero h1{margin:0 0 10px;font-size:21px;line-height:1.7}
.hero p{margin:2px 0;opacity:.92;font-size:13px}
.subject-line{font-size:14px;margin-top:6px}
.subject-box{border-bottom:1px dashed rgba(255,255,255,.55);padding:0 6px;font-weight:bold}
.edit-hint{display:none;background:#fef9c3;color:#854d0e;font-size:12.5px;
border-radius:10px;padding:8px 14px;margin-bottom:12px;line-height:1.9}
body.edit-mode .edit-hint{display:block}
.stats{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:18px}
.stat{flex:1 1 120px;background:var(--card);border:1px solid var(--border);
border-radius:12px;padding:14px;text-align:center}
.stat b{display:block;font-size:20px;color:var(--primary-dark);margin-bottom:4px}
.stat span{font-size:12px;color:var(--muted)}
.box{background:var(--card);border:1px solid var(--border);border-radius:12px;
padding:18px;margin-bottom:18px}
.box h3{margin:0 0 12px;font-size:15px}
.two-col{display:flex;gap:14px;flex-wrap:wrap}
.two-col .box{flex:1 1 320px;margin-bottom:14px}
.bar-row{display:flex;align-items:center;gap:10px;margin:9px 0}
.bar-label{width:150px;font-size:13px;flex-shrink:0;overflow:hidden;
text-overflow:ellipsis;white-space:nowrap}
.bar-track{flex:1;background:#edf1ef;border-radius:999px;height:14px;overflow:hidden}
.bar-fill{height:100%;border-radius:999px;min-width:6px}
.bar-num{width:40px;font-size:12px;color:var(--muted);text-align:left}
.bar-note{font-size:11.5px;color:var(--muted);margin-top:6px}

/* ---------- نوار ابزار ---------- */
.toolbar{background:var(--card);border:1px solid var(--border);border-radius:12px;
padding:14px;margin-bottom:18px;position:sticky;top:8px;z-index:5;
box-shadow:0 4px 14px rgba(15,40,30,.07)}
.tb-row{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.toolbar input[type=search]{flex:1 1 220px;font-family:inherit;font-size:13.5px;
border:1px solid var(--border);border-radius:10px;padding:9px 14px;background:#fbfdfc}
.toolbar select{font-family:inherit;font-size:13px;border:1px solid var(--border);
border-radius:10px;padding:8px 10px;background:#fbfdfc;color:var(--ink);max-width:210px}
.tb-check{font-size:12.5px;color:var(--muted);display:inline-flex;gap:6px;
align-items:center;cursor:pointer;white-space:nowrap}
.tb-chips{display:flex;flex-wrap:wrap;gap:7px;margin-top:10px}
.chip-btn{font-family:inherit;font-size:12.5px;cursor:pointer;border:1px solid var(--border);
background:#fff;border-radius:999px;padding:5px 13px;color:var(--ink);
display:inline-flex;align-items:center;gap:6px}
.chip-btn b{font-weight:600;color:var(--muted)}
.chip-btn.active{background:var(--primary);color:#fff;border-color:var(--primary)}
.chip-btn.active b{color:#eafff6}
.chip-btn .dot{width:9px;height:9px;border-radius:50%;display:inline-block}
.tb-actions{margin-top:10px;padding-top:10px;border-top:1px dashed var(--border)}
.tb-btn{font-family:inherit;font-size:12.5px;border:1px solid var(--border);background:#fff;
color:var(--ink);border-radius:999px;padding:7px 14px;cursor:pointer;white-space:nowrap}
.tb-btn:hover{border-color:#c9d6d0;background:#f6faf8}
.tb-btn.active{background:var(--primary);border-color:var(--primary);color:#fff}
.tb-btn.primary{background:var(--primary);border-color:var(--primary);color:#fff}
.tb-btn.primary:hover{background:var(--primary-dark)}
.tb-sep{width:1px;height:22px;background:var(--border);margin:0 3px}
.tb-label{font-size:12px;color:var(--muted)}
.tb-info{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-top:10px;
font-size:12.5px;color:var(--muted)}
.link-btn{font-family:inherit;font-size:12.5px;background:none;border:none;
color:var(--primary-dark);cursor:pointer;text-decoration:underline;padding:0}
.sel-bar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-top:10px;
background:#ecfdf5;border:1px solid #a7f3d0;border-radius:10px;padding:8px 12px;
font-size:12.5px}
.sel-bar.hidden{display:none}
.sel-bar button{font-family:inherit;font-size:12px;border:1px solid var(--border);
background:#fff;border-radius:999px;padding:5px 12px;cursor:pointer}
.sel-bar button.danger{background:#fee2e2;color:#b91c1c;border-color:#fca5a5}
.sel-bar button:disabled{opacity:.5;cursor:not-allowed}

/* ---------- حالت ویرایش ---------- */
body.edit-mode .msg .body{background:#fffdf3;border:1px dashed #d9c98a;
border-radius:8px;padding:6px 9px;cursor:text;min-height:22px}
body.edit-mode .msg .body:focus{outline:2px solid var(--primary);background:#fff}
body.edit-mode #reportTitle,body.edit-mode #reportSubject{
outline:1px dashed rgba(255,255,255,.65);cursor:text}
body.edit-mode #reportTitle:focus,body.edit-mode #reportSubject:focus{
outline:2px solid #fff;background:rgba(255,255,255,.09)}
.cat-edit{display:none;font-family:inherit;font-size:11px;border:1px solid var(--border);
border-radius:8px;padding:3px 6px;background:#fff;color:var(--ink);max-width:150px}
body.edit-mode .cat-edit{display:inline-block}

/* ---------- حالت انتخاب ---------- */
.pick{display:none;position:absolute;top:9px;right:10px;z-index:2}
body.sel-mode .pick{display:inline-flex}
body.sel-mode .msg{padding-right:36px}
.pick input{width:16px;height:16px;accent-color:var(--primary);cursor:pointer}
.msg.picked{background:#eefaf5;border-color:var(--primary)}

section.cat{background:var(--card);border:1px solid var(--border);border-radius:12px;
padding:16px;margin-bottom:14px}
section.cat h2{font-size:15px;margin:0 0 10px;display:flex;align-items:center;
gap:8px;flex-wrap:wrap}
.dot{width:11px;height:11px;border-radius:50%;display:inline-block;flex-shrink:0}
.badge{font-size:11px;background:#e8f7f1;color:var(--primary-dark);
border-radius:999px;padding:2px 10px}
.msg{border:1px solid var(--border);border-radius:10px;padding:10px 12px;
margin:8px 0;font-size:13.5px;line-height:1.9;background:#fcfdfc;position:relative}
.msg:hover{border-color:#c9d6d0}
.msg .meta{font-size:11.5px;color:var(--muted);margin-bottom:4px;display:flex;
flex-wrap:wrap;align-items:center;gap:4px}
.msg .meta b{color:var(--ink)}
.msg .body{white-space:pre-wrap;word-wrap:break-word}
.msg:target{outline:2px solid var(--primary);background:#eefaf5}
.hide-btn{position:absolute;top:7px;left:7px;width:22px;height:22px;border-radius:7px;
border:1px solid var(--border);background:#fff;color:#9ca3af;font-size:11px;
cursor:pointer;line-height:1;opacity:0;transition:.15s}
.msg:hover .hide-btn{opacity:1}
.hide-btn:hover{background:#fee2e2;color:#b91c1c;border-color:#fca5a5}
.chip{display:inline-block;font-size:10.5px;background:#eef2f0;color:#4b5563;
border-radius:999px;padding:1px 9px;vertical-align:middle}
.chip.fwd{background:#fef3c7;color:#92400e}
.chip.media{background:#dbeafe;color:#1d4ed8}
.chip.edit{background:#fde8e8;color:#b91c1c}
.chip.rel{background:#ede9fe;color:#5b21b6;text-decoration:none}
.chip.rel:hover{background:#ddd6fe}
.chip.replies-n{background:#e0f2fe;color:#0369a1}
.gallery{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));
gap:8px;margin:10px 0}
.gallery.single{grid-template-columns:minmax(0,560px)}
.gallery img{width:100%;display:block;border-radius:10px;
border:1px solid var(--border);cursor:zoom-in}
.gallery.single img{max-height:460px;object-fit:cover;width:100%}
#imgOverlay{position:fixed;inset:0;background:rgba(10,15,12,.86);display:none;
align-items:center;justify-content:center;z-index:50;cursor:zoom-out;padding:20px}
#imgOverlay img{max-width:100%;max-height:100%;border-radius:12px}
.missing-img{border:1px dashed #c6cdc9;border-radius:10px;padding:18px;
text-align:center;color:var(--muted);font-size:12px;background:#f6f8f7}
.files{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}
.file-chip{display:inline-flex;align-items:center;gap:6px;font-size:12px;
background:#f1f5f9;border:1px solid var(--border);border-radius:999px;
padding:5px 12px;color:#334155}
.replies{margin-top:10px;border-top:1px dashed var(--border);padding-top:8px}
.replies-title{font-size:11px;color:var(--muted);margin-bottom:4px}
.reply{background:#f4f7f5;border:1px solid var(--border);border-radius:8px;
padding:7px 10px;margin:6px 6px 6px 0;font-size:12.5px;line-height:1.8}
.reply .rmeta{font-size:11px;color:var(--muted);margin-bottom:2px}
.reply .rmeta b{color:var(--ink)}
.reply img{max-width:200px;border-radius:8px;border:1px solid var(--border);
display:block;margin-top:4px}
.reply .rbody{white-space:pre-wrap;word-wrap:break-word}
.empty{text-align:center;color:var(--muted);padding:30px;font-size:14px;
background:var(--card);border:1px dashed var(--border);border-radius:12px}
.hidden{display:none!important}
#cardPool{display:none}
.toast{position:fixed;bottom:18px;right:50%;transform:translateX(50%) translateY(80px);
background:#1f2937;color:#f9fafb;border-radius:999px;padding:9px 20px;font-size:12.5px;
opacity:0;transition:.25s;z-index:70;box-shadow:0 6px 20px rgba(0,0,0,.25)}
.toast.show{opacity:1;transform:translateX(50%) translateY(0)}
.toast.warn{background:#92400e}

/* ---------- مودال خروجی پاورپوینت ---------- */
.overlay{position:fixed;inset:0;background:rgba(10,15,12,.55);display:flex;
align-items:center;justify-content:center;z-index:60;padding:18px}
.overlay.hidden{display:none}
.modal{background:var(--card);border-radius:16px;padding:22px 24px;max-width:500px;
width:100%;box-shadow:0 20px 60px rgba(0,0,0,.3)}
.modal h3{margin:0 0 6px;font-size:16px}
.m-sub{font-size:12px;color:var(--muted);margin:0 0 12px}
.m-row{display:flex;align-items:center;gap:10px;margin:10px 0;font-size:13px}
.m-row label:first-child{width:110px;color:var(--muted);flex-shrink:0}
.m-row select{flex:1;font-family:inherit;font-size:13px;border:1px solid var(--border);
border-radius:10px;padding:8px 10px;background:#fbfdfc;color:var(--ink)}
.m-check{display:inline-flex;gap:7px;align-items:center;cursor:pointer;font-size:13px}
.m-hint{font-size:11.5px;color:var(--muted);background:#f6f8f7;border-radius:8px;
padding:7px 10px;margin:8px 0;line-height:1.9}
.m-actions{display:flex;gap:10px;margin-top:14px}
.m-btn{font-family:inherit;font-size:13px;border:none;border-radius:10px;padding:9px 18px;
cursor:pointer;background:#eef2f0;color:var(--ink)}
.m-btn.primary{background:var(--primary);color:#fff}
.m-btn.primary:hover{background:var(--primary-dark)}
.m-status{font-size:12px;color:var(--primary-dark);margin:10px 0 0;min-height:16px;
line-height:1.8}
.m-status.err{color:#b91c1c}
footer{text-align:center;color:var(--muted);font-size:12px;padding:8px 0 0}
@media print{.toolbar,.sel-bar,.hide-btn,.pick,.cat-edit,.edit-hint,.toast,.overlay,
#cardPool{display:none!important}
body{background:#fff;padding:0}
section.cat{page-break-inside:avoid}}
</style>
</head>
<body data-group="$group_attr" data-range="$range" data-generated="$generated">
<div class="wrap">
  <div class="hero">
    <div class="edit-hint" id="editHint">حالت ویرایش فعال است — روی عنوان، «موضوع گزارش» و متن پیام‌ها کلیک کنید و تغییر دهید؛ دستهٔ هر پیام را هم از فهرست کنار نام آن عوض کنید. برای ماندگاری تغییرها و حذف‌ها، «ذخیره نسخه ویرایش‌شده» را بزنید.</div>
    <h1 id="reportTitle">گزارش عملکرد — $title</h1>
    <p class="subject-line">موضوع گزارش: <span class="subject-box" id="reportSubject">$subject</span></p>
    <p>تاریخ تولید گزارش: $generated</p>
    <p>گروه: $title &nbsp;|&nbsp; تعداد پیام‌ها: $total &nbsp;|&nbsp; بازه زمانی: $range</p>
  </div>
  <div class="stats">
    <div class="stat"><b>$total</b><span>کل پیام‌ها</span></div>
    <div class="stat"><b>$participants</b><span>شرکت‌کنندگان</span></div>
    <div class="stat"><b>$photos</b><span>عکس‌ها</span></div>
    <div class="stat"><b>$media</b><span>کل رسانه‌ها</span></div>
    <div class="stat"><b>$replies</b><span>کامنت‌ها و پاسخ‌ها</span></div>
    <div class="stat"><b>$ncats</b><span>تعداد موضوعات</span></div>
    <div class="stat"><b>$ndates</b><span>تعداد روزهای فعال</span></div>
    <div class="stat"><b>$topcat</b><span>موضوع پرپیام</span></div>
  </div>
  <div class="two-col">
    <div class="box">
      <h3>توزیع پیام‌ها بر اساس موضوع (بر اساس داده‌های موجود)</h3>
      $bars
    </div>
    <div class="box">
      <h3>توزیع پیام‌ها بر اساس تاریخ ارسال (شمسی)</h3>
      $date_bars
    </div>
  </div>

  <div class="toolbar">
    <div class="tb-row">
      <input type="search" id="q" placeholder="جست‌وجو در متن پیام، کپشن، فرستنده، کامنت‌ها ...">
      <select id="dateSel">
        <option value="">همه تاریخ‌ها</option>
        $date_options
      </select>
      <select id="senderSel">
        <option value="">همه فرستنده‌ها</option>
        $sender_options
      </select>
      <select id="chatSel" $chat_hidden>
        <option value="">همه گروه‌ها</option>
        $chat_options
      </select>
      <label class="tb-check"><input type="checkbox" id="photoOnly"> فقط پیام‌های عکس‌دار</label>
    </div>
    <div class="tb-chips" id="catChips">
      <button type="button" class="chip-btn active" data-cat="">همه موضوعات</button>
      $cat_chips
    </div>
    <div class="tb-row tb-actions">
      <span class="tb-label">گروه‌بندی:</span>
      <select id="groupBySel">
        <option value="cat">دسته موضوعی</option>
        <option value="date">تاریخ ارسال</option>
        <option value="sender">فرستنده</option>
      </select>
      <span class="tb-label">مرتب‌سازی:</span>
      <select id="sortSel">
        <option value="ts">زمان ارسال</option>
        <option value="sender">فرستنده</option>
        <option value="cat">موضوع</option>
      </select>
      <button type="button" class="tb-btn" id="btnSortDir">صعودی ↑</button>
      <span class="tb-sep"></span>
      <button type="button" class="tb-btn" id="btnSelectMode">حالت انتخاب</button>
      <button type="button" class="tb-btn" id="btnEditMode">حالت ویرایش</button>
      <span class="tb-sep"></span>
      <button type="button" class="tb-btn primary" id="btnPptx">خروجی پاورپوینت</button>
      <button type="button" class="tb-btn" id="btnSaveCopy">ذخیره نسخه ویرایش‌شده</button>
      <button type="button" class="tb-btn" id="btnPrint">چاپ / PDF</button>
    </div>
    <div class="sel-bar hidden" id="selBar">
      <span><b id="selCount">۰</b> پیام انتخاب شده</span>
      <button type="button" id="btnSelAll">انتخاب نمایش‌داده‌شده‌ها</button>
      <button type="button" id="btnSelNone">لغو انتخاب</button>
      <button type="button" class="danger" id="btnSelDelete">حذف پیام‌های انتخاب‌شده</button>
    </div>
    <div class="tb-info">
      <span id="visCount"></span>
      <button type="button" class="link-btn" id="btnClearFilters">پاک‌کردن فیلترها</button>
      <span>حذف هر پیام با دکمه ✕ روی کارت؛ حذف‌ها با «ذخیره نسخه ویرایش‌شده» در فایل نهایی هم حذف می‌مانند</span>
    </div>
  </div>

  <div id="content"></div>
  <div class="empty hidden" id="noResult">هیچ پیامی با این فیلترها پیدا نشد — «پاک‌کردن فیلترها» را بزنید.</div>
  $sections

  <footer>تولیدشده با برنامه Bale Chat Mosharket نسخه $version — گزارش عملکرد تعاملی: گروه‌بندی، فیلتر، ویرایش، حذف و خروجی پاورپوینت</footer>
</div>

<div id="cardPool" aria-hidden="true">$pool</div>

<div id="imgOverlay"><img id="imgOverlayImg" src="" alt=""></div>

<div class="overlay hidden" id="pptxOverlay">
  <div class="modal">
    <h3>خروجی پاورپوینت</h3>
    <p class="m-sub">فایل pptx با تم و فرمت دلخواه — آماده برای ارائه عملکرد حوزه</p>
    <div class="m-row">
      <label>تم رنگی:</label>
      <select id="pptxTheme">
        <option value="green">سبز رسمی</option>
        <option value="blue">آبی سازمانی</option>
        <option value="navy">سرمه‌ای شب</option>
        <option value="mono">ساده خاکستری</option>
      </select>
    </div>
    <div class="m-row">
      <label>فرمت اسلاید:</label>
      <select id="pptxFmt">
        <option value="16:9">عریض ۱۶:۹ (نمایش مدرن)</option>
        <option value="4:3">کلاسیک ۴:۳</option>
      </select>
    </div>
    <div class="m-row">
      <label>گروه‌بندی اسلایدها:</label>
      <select id="pptxGroup">
        <option value="cat">بر اساس موضوع</option>
        <option value="date">بر اساس تاریخ ارسال</option>
      </select>
    </div>
    <div class="m-row">
      <label>دامنه خروجی:</label>
      <select id="pptxScope">
        <option value="auto">هوشمند (انتخاب‌شده‌ها؛ وگرنه پیام‌های فیلترشده)</option>
        <option value="all">همه پیام‌ها</option>
        <option value="selected">فقط پیام‌های انتخاب‌شده</option>
      </select>
    </div>
    <div class="m-row">
      <label>&nbsp;</label>
      <label class="m-check"><input type="checkbox" id="pptxImages" checked> شامل عکس‌ها در اسلایدها</label>
    </div>
    <p class="m-hint" id="pptxScopeHint"></p>
    <div class="m-actions">
      <button type="button" class="m-btn primary" id="btnPptxGo">ساخت فایل پاورپوینت</button>
      <button type="button" class="m-btn" id="btnPptxClose">بستن</button>
    </div>
    <p class="m-status" id="pptxStatus"></p>
  </div>
</div>

<script>/*__PPTX_LIB__*/</script>
<script><!--MAIN_JS--></script>
</body>
</html>
""")

# ---------------------------------------------------------------- جاوااسکریپت گزارش

MAIN_JS = r"""
(function(){
"use strict";

/* ---------- ارجاع‌ها و وضعیت ---------- */
var PALETTE = ["#0e9f6e","#2563eb","#d97706","#dc2626","#7c3aed",
               "#0d9488","#db2777","#475569","#9333ea","#0891b2"];
var pool = document.getElementById("cardPool");
var content = document.getElementById("content");
var noResult = document.getElementById("noResult");
var visEl = document.getElementById("visCount");
var selBar = document.getElementById("selBar");
var selCountEl = document.getElementById("selCount");
var qEl = document.getElementById("q");
var dateSel = document.getElementById("dateSel");
var senderSel = document.getElementById("senderSel");
var chatEl = document.getElementById("chatSel");
var photoEl = document.getElementById("photoOnly");
var groupSel = document.getElementById("groupBySel");
var sortSel = document.getElementById("sortSel");
var catChips = document.getElementById("catChips");
var overlay = document.getElementById("imgOverlay");
var overlayImg = document.getElementById("imgOverlayImg");
var pptxOverlay = document.getElementById("pptxOverlay");
var toastEl = null;
var totalEl = null;

var cards = [].slice.call(pool.querySelectorAll(".msg"));
var state = { catSel:{}, selMode:false, editMode:false, selected:{}, sortDir:"asc" };
var catCounts = {};
var catColors = {};

/* ---------- ابزارها ---------- */
function faNum(n){
  return String(n).replace(/[0-9]/g, function(d){ return "۰۱۲۳۴۵۶۷۸۹".charAt(+d); });
}
function esc(s){
  return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;")
                  .replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}
function toast(msg, kind){
  if (!toastEl){
    toastEl = document.createElement("div");
    document.body.appendChild(toastEl);
  }
  toastEl.textContent = msg;
  toastEl.className = "toast show" + (kind === "warn" ? " warn" : "");
  if (toastEl._t) clearTimeout(toastEl._t);
  toastEl._t = setTimeout(function(){ toastEl.className = "toast"; }, 2800);
}
function stamp(){
  var d = new Date();
  function p(n){ return (n < 10 ? "0" : "") + n; }
  return d.getFullYear() + p(d.getMonth()+1) + p(d.getDate()) + "_" +
         p(d.getHours()) + p(d.getMinutes()) + p(d.getSeconds());
}
function downloadBlob(blob, name){
  var a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  document.body.appendChild(a);
  a.click();
  setTimeout(function(){
    URL.revokeObjectURL(a.href);
    a.remove();
  }, 800);
}
function syncApi(url, payload){
  /* همگام‌سازی با پایگاه داده برنامه — فقط وقتی گزارش از داخل برنامه (http) باز شده باشد */
  if (!/^http/.test(location.protocol)) return;
  try {
    fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }).catch(function(){});
  } catch (e) {}
}

/* ---------- آمار موضوعات و رنگ‌ها ---------- */
(function computeCats(){
  for (var i = 0; i < cards.length; i++){
    var c = cards[i].getAttribute("data-cat") || "سایر";
    catCounts[c] = (catCounts[c] || 0) + 1;
  }
  var names = Object.keys(catCounts).sort(function(a,b){
    return catCounts[b] - catCounts[a];
  });
  for (var j = 0; j < names.length; j++){
    catColors[names[j]] = PALETTE[j % PALETTE.length];
  }
})();

/* ---------- فیلترها ---------- */
function cardVisible(c){
  var keys = Object.keys(state.catSel);
  if (keys.length && !state.catSel[c.getAttribute("data-cat")]) return false;
  var s = senderSel.value;
  if (s && c.getAttribute("data-sender") !== s) return false;
  var ch = (chatEl && !chatEl.disabled) ? chatEl.value : "";
  if (ch && c.getAttribute("data-chat") !== ch) return false;
  var d = dateSel.value;
  if (d && c.getAttribute("data-date") !== d) return false;
  if (photoEl.checked && c.getAttribute("data-photo") !== "1") return false;
  var t = qEl.value.trim().toLowerCase();
  if (t && (c.getAttribute("data-txt") || "").indexOf(t) === -1) return false;
  return true;
}
function filtered(){
  var out = [];
  for (var i = 0; i < cards.length; i++){
    if (cardVisible(cards[i])) out.push(cards[i]);
  }
  return out;
}

/* ---------- مرتب‌سازی ---------- */
function sorted(list){
  var dir = state.sortDir === "asc" ? 1 : -1;
  var key = sortSel.value;
  return list.slice().sort(function(a,b){
    if (key === "sender"){
      var x = a.getAttribute("data-sender") || "";
      var y = b.getAttribute("data-sender") || "";
      if (x !== y) return dir * x.localeCompare(y, "fa");
      return dir * ((+a.getAttribute("data-ts") || 0) - (+b.getAttribute("data-ts") || 0));
    }
    if (key === "cat"){
      var ca = a.getAttribute("data-cat") || "سایر";
      var cb = b.getAttribute("data-cat") || "سایر";
      var na = catCounts[ca] || 0, nb = catCounts[cb] || 0;
      if (na !== nb) return dir * (nb - na);
      return dir * ((+a.getAttribute("data-ts") || 0) - (+b.getAttribute("data-ts") || 0));
    }
    return dir * ((+a.getAttribute("data-ts") || 0) - (+b.getAttribute("data-ts") || 0));
  });
}

/* ---------- گروه‌بندی ---------- */
function minTs(arr){
  var m = 0;
  for (var i = 0; i < arr.length; i++){
    var t = +arr[i].getAttribute("data-ts") || 0;
    if (t && (!m || t < m)) m = t;
  }
  return m;
}
function grouped(list, by){
  var map = {}, order = [];
  for (var i = 0; i < list.length; i++){
    var c = list[i];
    var k = (by === "date") ? (c.getAttribute("data-date") || "بدون تاریخ")
          : (by === "sender") ? (c.getAttribute("data-sender") || "ناشناس")
          : (c.getAttribute("data-cat") || "سایر");
    if (!map[k]){ map[k] = []; order.push(k); }
    map[k].push(c);
  }
  var dir = state.sortDir === "asc" ? 1 : -1;
  if (by === "date"){
    order.sort(function(a,b){
      if (a === "بدون تاریخ") return 1;
      if (b === "بدون تاریخ") return -1;
      return dir * (minTs(map[a]) - minTs(map[b]));
    });
  } else {
    order.sort(function(a,b){
      return (map[b].length - map[a].length) || a.localeCompare(b, "fa");
    });
  }
  return { keys: order, map: map };
}

/* ---------- رندر ---------- */
function sectionEl(title, color, count){
  var sec = document.createElement("section");
  sec.className = "cat";
  var h2 = document.createElement("h2");
  h2.innerHTML = '<span class="dot" style="background:' + color + '"></span>' +
    esc(title) + '<span class="badge">' + faNum(count) + ' پیام</span>';
  sec.appendChild(h2);
  return sec;
}
function render(){
  /* همه کارت‌ها اول به مخزن برمی‌گردند تا ترتیب DOM تازه ساخته شود */
  for (var i = 0; i < cards.length; i++){
    var c = cards[i];
    if (c.parentNode !== pool) pool.appendChild(c);
  }
  content.innerHTML = "";
  var list = sorted(filtered());
  var by = groupSel.value;
  var g = grouped(list, by);
  var shown = 0;
  for (var k = 0; k < g.keys.length; k++){
    var key = g.keys[k], arr = g.map[key];
    var color = (by === "cat") ? (catColors[key] || "#64748b")
              : (by === "date") ? "#475569" : "#0e9f6e";
    var sec = sectionEl(key, color, arr.length);
    for (var j = 0; j < arr.length; j++) sec.appendChild(arr[j]);
    content.appendChild(sec);
    shown += arr.length;
  }
  visEl.textContent = "نمایش " + faNum(shown) + " پیام از " + faNum(cards.length) + " پیام";
  noResult.classList.toggle("hidden", shown > 0);
  updateSelBar();
}

/* ---------- چیپ‌های موضوع ---------- */
function refreshChips(){
  var chips = catChips.querySelectorAll(".chip-btn");
  for (var i = 0; i < chips.length; i++){
    var cc = chips[i].getAttribute("data-cat");
    var on = (cc === "") ? (Object.keys(state.catSel).length === 0) : !!state.catSel[cc];
    chips[i].classList.toggle("active", on);
  }
}
catChips.addEventListener("click", function(ev){
  var b = ev.target.closest(".chip-btn");
  if (!b) return;
  var c = b.getAttribute("data-cat");
  if (c === "") state.catSel = {};
  else if (state.catSel[c]) delete state.catSel[c];
  else state.catSel[c] = true;
  refreshChips();
  render();
});

/* ---------- رویدادهای فیلتر و ترتیب ---------- */
qEl.addEventListener("input", render);
dateSel.addEventListener("change", render);
senderSel.addEventListener("change", render);
if (chatEl) chatEl.addEventListener("change", render);
photoEl.addEventListener("change", render);
groupSel.addEventListener("change", render);
sortSel.addEventListener("change", render);
document.getElementById("btnSortDir").addEventListener("click", function(){
  state.sortDir = (state.sortDir === "asc") ? "desc" : "asc";
  this.textContent = (state.sortDir === "asc") ? "صعودی ↑" : "نزولی ↓";
  render();
});
document.getElementById("btnClearFilters").addEventListener("click", function(){
  state.catSel = {};
  refreshChips();
  qEl.value = "";
  dateSel.value = "";
  senderSel.value = "";
  if (chatEl) chatEl.value = "";
  photoEl.checked = false;
  render();
});
document.getElementById("btnPrint").addEventListener("click", function(){
  window.print();
});

/* ---------- انتخاب و حذف ---------- */
function cardKey(c){ return c.id || c.getAttribute("data-mids") || ""; }
function cardMids(c){
  return (c.getAttribute("data-mids") || "").split(",").filter(function(x){ return x; });
}
function updateSelBar(){
  var n = Object.keys(state.selected).length;
  selCountEl.textContent = faNum(n);
  document.getElementById("btnSelDelete").disabled = (n === 0);
  selBar.classList.toggle("hidden", !state.selMode);
}
document.getElementById("btnSelectMode").addEventListener("click", function(){
  state.selMode = !state.selMode;
  document.body.classList.toggle("sel-mode", state.selMode);
  this.classList.toggle("active", state.selMode);
  this.textContent = state.selMode ? "پایان حالت انتخاب" : "حالت انتخاب";
  updateSelBar();
});
document.getElementById("btnSelAll").addEventListener("click", function(){
  var vis = filtered();
  for (var i = 0; i < vis.length; i++){
    var c = vis[i];
    var box = c.querySelector(".pick-box");
    if (box) box.checked = true;
    c.classList.add("picked");
    state.selected[cardKey(c)] = c;
  }
  updateSelBar();
  toast(faNum(vis.length) + " پیام نمایش‌داده‌شده انتخاب شد");
});
document.getElementById("btnSelNone").addEventListener("click", function(){
  state.selected = {};
  var all = content.querySelectorAll(".msg");
  for (var i = 0; i < all.length; i++){
    var box = all[i].querySelector(".pick-box");
    if (box) box.checked = false;
    all[i].classList.remove("picked");
  }
  updateSelBar();
});
function removeCardNode(card){
  var idx = cards.indexOf(card);
  if (idx > -1) cards.splice(idx, 1);
  var k = cardKey(card);
  if (state.selected[k]) delete state.selected[k];
  if (card.parentNode) card.parentNode.removeChild(card);
}
document.getElementById("btnSelDelete").addEventListener("click", function(){
  var keys = Object.keys(state.selected);
  if (!keys.length) return;
  if (!confirm("حذف " + faNum(keys.length) + " پیام انتخاب‌شده؟ اگر گزارش از داخل برنامه باز شده باشد، این پیام‌ها از پایگاه داده برنامه هم حذف می‌شوند.")) return;
  var allIds = [];
  for (var i = 0; i < keys.length; i++){
    var card = state.selected[keys[i]];
    allIds = allIds.concat(cardMids(card));
    removeCardNode(card);
  }
  state.selected = {};
  syncApi("/api/messages/delete", { ids: allIds });
  render();
  toast(faNum(keys.length) + " پیام حذف شد", "warn");
});

/* ---------- حالت ویرایش ---------- */
function setEditMode(on){
  state.editMode = on;
  document.body.classList.toggle("edit-mode", on);
  var bodies = document.querySelectorAll(".msg .body");
  for (var i = 0; i < bodies.length; i++){
    bodies[i].contentEditable = on ? "true" : "false";
  }
  var t = document.getElementById("reportTitle");
  var s = document.getElementById("reportSubject");
  t.contentEditable = on ? "true" : "false";
  s.contentEditable = on ? "true" : "false";
  var btn = document.getElementById("btnEditMode");
  btn.classList.toggle("active", on);
  btn.textContent = on ? "پایان حالت ویرایش" : "حالت ویرایش";
}
document.getElementById("btnEditMode").addEventListener("click", function(){
  setEditMode(!state.editMode);
  if (state.editMode) toast("حالت ویرایش روشن شد — متن‌ها، عنوان و موضوع قابل ویرایش است");
});

/* تغییر دسته هر پیام در حالت ویرایش */
function recategorize(card, val){
  card.setAttribute("data-cat", val);
  var mids = cardMids(card);
  if (mids.length) syncApi("/api/messages/category", { ids: mids, category: val });
  var c = val;
  catCounts[c] = (catCounts[c] || 0);
  if (!catColors[c]) catColors[c] = PALETTE[Object.keys(catColors).length % PALETTE.length];
  render();
  toast("دسته پیام به «" + val + "» تغییر کرد");
}
content.addEventListener("change", function(ev){
  var box = ev.target.closest(".pick-box");
  if (box){
    var card = box.closest(".msg");
    if (!card) return;
    if (box.checked){
      state.selected[cardKey(card)] = card;
      card.classList.add("picked");
    } else {
      delete state.selected[cardKey(card)];
      card.classList.remove("picked");
    }
    updateSelBar();
    return;
  }
  var sel = ev.target.closest(".cat-edit");
  if (sel){
    var card2 = sel.closest(".msg");
    if (card2 && sel.value) recategorize(card2, sel.value);
  }
});

/* ---------- حذف تک پیام + بزرگ‌نمایی عکس ---------- */
content.addEventListener("click", function(ev){
  var btn = ev.target.closest(".hide-btn");
  if (btn){
    var card = btn.closest(".msg");
    if (!card) return;
    if (!confirm("این پیام از گزارش حذف شود؟ اگر گزارش از داخل برنامه باز شده باشد، از پایگاه داده برنامه هم حذف می‌شود.")) return;
    var mids = cardMids(card);
    removeCardNode(card);
    if (mids.length) syncApi("/api/messages/delete", { ids: mids });
    render();
    toast("پیام حذف شد", "warn");
    return;
  }
  var img = ev.target.closest(".gallery img");
  if (img){
    overlayImg.src = img.src;
    overlay.style.display = "flex";
  }
});
overlay.addEventListener("click", function(){
  overlay.style.display = "none";
  overlayImg.src = "";
});
document.addEventListener("keydown", function(ev){
  if (ev.key === "Escape"){
    if (overlay.style.display === "flex"){
      overlay.style.display = "none";
      overlayImg.src = "";
    }
    if (!pptxOverlay.classList.contains("hidden")) pptxOverlay.classList.add("hidden");
  }
});

/* ---------- ذخیره نسخه ویرایش‌شده ---------- */
document.getElementById("btnSaveCopy").addEventListener("click", function(){
  /* کارت‌ها موقتاً به مخزن برمی‌گردند تا فایل ذخیره‌شده سبک و کامل باشد */
  for (var i = 0; i < cards.length; i++){
    var c = cards[i];
    if (c.parentNode && c.parentNode !== pool) pool.appendChild(c);
  }
  content.innerHTML = "";
  var htmlStr = "<!DOCTYPE html>\n" + document.documentElement.outerHTML;
  render();
  var blob = new Blob([htmlStr], { type: "text/html;charset=utf-8" });
  downloadBlob(blob, "report_edited_" + stamp() + ".html");
  toast("نسخه ویرایش‌شده ذخیره شد — فایل دانلود شد");
});

/* ---------- خروجی پاورپوینت ---------- */
var THEMES = {
  green: { accent:"0E9F6E", dark:"0B7A55", bg:"FFFFFF", ink:"1F2937", sub:"6B7280", name:"سبز رسمی" },
  blue:  { accent:"2563EB", dark:"1E3A8A", bg:"FFFFFF", ink:"1F2937", sub:"6B7280", name:"آبی سازمانی" },
  navy:  { accent:"38BDF8", dark:"0EA5E9", bg:"0F172A", ink:"E2E8F0", sub:"94A3B8", name:"سرمه‌ای شب" },
  mono:  { accent:"475569", dark:"334155", bg:"FFFFFF", ink:"111827", sub:"6B7280", name:"ساده خاکستری" }
};
var FONT = "Tahoma";

function ensureLib(cb){
  if (window.PptxGenJS) return cb(true);
  var urls = [
    "https://cdnjs.cloudflare.com/ajax/libs/pptxgenjs/3.12.0/pptxgen.bundle.js",
    "https://unpkg.com/pptxgenjs@3.12.0/dist/pptxgen.bundle.js",
    "https://cdn.jsdelivr.net/npm/pptxgenjs@3.12.0/dist/pptxgen.bundle.js"
  ];
  var i = 0;
  (function next(){
    if (i >= urls.length) return cb(false);
    var s = document.createElement("script");
    s.src = urls[i++];
    s.onload = function(){ cb(!!window.PptxGenJS); };
    s.onerror = function(){ next(); };
    document.head.appendChild(s);
  })();
}

document.getElementById("btnPptx").addEventListener("click", function(){
  pptxOverlay.classList.remove("hidden");
  updateScopeHint();
});
document.getElementById("btnPptxClose").addEventListener("click", function(){
  pptxOverlay.classList.add("hidden");
});
document.getElementById("pptxScope").addEventListener("change", updateScopeHint);

function scopeList(){
  var scope = document.getElementById("pptxScope").value;
  if (scope === "all") return cards.slice();
  if (scope === "selected"){
    var arr = [];
    for (var k in state.selected){
      if (Object.prototype.hasOwnProperty.call(state.selected, k)) arr.push(state.selected[k]);
    }
    return arr;
  }
  /* هوشمند: اگر چیزی انتخاب شده، همان؛ وگرنه فیلترشده‌ها */
  if (Object.keys(state.selected).length) return scopeListSelected();
  return filtered();
}
function scopeListSelected(){
  var arr = [];
  for (var k in state.selected){
    if (Object.prototype.hasOwnProperty.call(state.selected, k)) arr.push(state.selected[k]);
  }
  return arr;
}
function updateScopeHint(){
  var n = scopeList().length;
  var sel = Object.keys(state.selected).length;
  var txt = "دامنه فعلی: " + faNum(n) + " پیام";
  if (sel) txt += " (" + faNum(sel) + " پیام انتخاب شده است)";
  document.getElementById("pptxScopeHint").textContent = txt;
}

function collectModel(list){
  return list.map(function(c){
    var b = c.querySelector(".body");
    var text = b ? b.innerText.replace(/\u00a0/g, " ").trim() : "";
    if (text === "—") text = "";
    var imgs = [].map.call(c.querySelectorAll(".gallery img"), function(im){
      var src = im.getAttribute("src") || "";
      return (src.indexOf("data:") === 0) ? src : "";
    }).filter(function(s){ return s; });
    var replies = [].map.call(c.querySelectorAll(".reply"), function(r){
      var rm = r.querySelector(".rmeta b");
      var rb = r.querySelector(".rbody");
      var ri = r.querySelector("img");
      return {
        sender: rm ? rm.innerText.trim() : "",
        text: rb ? rb.innerText.replace(/\u00a0/g, " ").trim() : "",
        img: ri ? (ri.getAttribute("src") || "") : ""
      };
    }).filter(function(r){ return r.text || r.img; });
    return {
      sender: c.getAttribute("data-sender") || "",
      when: c.getAttribute("data-when") || "",
      date: c.getAttribute("data-date") || "",
      cat: c.getAttribute("data-cat") || "سایر",
      ts: +c.getAttribute("data-ts") || 0,
      text: text,
      imgs: imgs,
      replies: replies
    };
  });
}

function groupModel(list, by){
  var map = {}, order = [];
  for (var i = 0; i < list.length; i++){
    var m = list[i];
    var k = (by === "date") ? (m.date || "بدون تاریخ") : m.cat;
    if (!map[k]){ map[k] = []; order.push(k); }
    map[k].push(m);
  }
  if (by === "date"){
    order.sort(function(a,b){
      if (a === "بدون تاریخ") return 1;
      if (b === "بدون تاریخ") return -1;
      var ta = minTsModel(map[a]), tb = minTsModel(map[b]);
      return (ta - tb);
    });
  } else {
    order.sort(function(a,b){
      return (map[b].length - map[a].length) || a.localeCompare(b, "fa");
    });
  }
  return { keys: order, map: map };
}
function minTsModel(arr){
  var m = 0;
  for (var i = 0; i < arr.length; i++){
    if (arr[i].ts && (!m || arr[i].ts < m)) m = arr[i].ts;
  }
  return m;
}
function trunc(s, n){
  s = (s || "").replace(/\s*\n+\s*/g, " · ").trim();
  return s.length > n ? (s.slice(0, n) + "…") : s;
}

document.getElementById("btnPptxGo").addEventListener("click", function(){
  var statusEl = document.getElementById("pptxStatus");
  statusEl.classList.remove("err");
  statusEl.textContent = "در حال آماده‌سازی ...";
  ensureLib(function(ok){
    if (!ok){
      statusEl.classList.add("err");
      statusEl.textContent = "کتابخانه پاورپوینت پیدا نشد — برای ساخت فایل pptx یک بار به اینترنت نیاز است (نسخه بعدی گزارش کتابخانه را داخل خود فایل نگه می‌دارد).";
      return;
    }
    statusEl.textContent = "در حال ساخت اسلایدها ...";
    setTimeout(function(){
      try {
        var list = scopeList();
        if (!list.length){
          statusEl.classList.add("err");
          statusEl.textContent = "پیامی برای خروجی پیدا نشد — ابتدا فیلترها را پاک کنید یا پیام انتخاب کنید.";
          return;
        }
        var model = collectModel(list);
        buildPptx(model, statusEl);
      } catch (e){
        statusEl.classList.add("err");
        statusEl.textContent = "خطا در ساخت فایل: " + (e && e.message ? e.message : e);
      }
    }, 40);
  });
});

function buildPptx(model, statusEl){
  var themeKey = document.getElementById("pptxTheme").value;
  var T = THEMES[themeKey] || THEMES.green;
  var fmt = document.getElementById("pptxFmt").value;
  var groupBy = document.getElementById("pptxGroup").value;
  var includeImages = document.getElementById("pptxImages").checked;

  var pptx = new PptxGenJS();
  pptx.layout = (fmt === "4:3") ? "LAYOUT_4x3" : "LAYOUT_16x9";
  var W = (fmt === "4:3") ? 10 : 13.33, H = 7.5;
  var RECT = (pptx.ShapeType && pptx.ShapeType.rect) || "rect";

  var title = (document.getElementById("reportTitle").innerText || "").trim();
  var subject = (document.getElementById("reportSubject").innerText || "").trim();
  var group = document.body.getAttribute("data-group") || "";
  var range = document.body.getAttribute("data-range") || "";
  var generated = document.body.getAttribute("data-generated") || "";

  /* آمار */
  var senders = {}, photos = 0, repliesN = 0, catCountsP = {};
  for (var i = 0; i < model.length; i++){
    var m = model[i];
    if (m.sender) senders[m.sender] = 1;
    photos += m.imgs.length;
    repliesN += m.replies.length;
    catCountsP[m.cat] = (catCountsP[m.cat] || 0) + 1;
  }
  var nSenders = Object.keys(senders).length;
  var catList = Object.keys(catCountsP).sort(function(a,b){
    return catCountsP[b] - catCountsP[a];
  });
  var slideNo = 0;

  /* ---------- اسلاید عنوان ---------- */
  var s1 = pptx.addSlide(); slideNo++;
  s1.background = { color: T.bg };
  s1.addShape(RECT, { x:0, y:0, w:W, h:0.14, fill:{ color:T.accent } });
  s1.addShape(RECT, { x:W-0.75, y:1.25, w:0.16, h:2.0, fill:{ color:T.accent } });
  s1.addText(title, { x:0.6, y:1.25, w:W-1.75, h:1.0, fontSize:24, bold:true,
    color:T.ink, align:"right", fontFace:FONT, rtlMode:true, valign:"middle" });
  s1.addText([
    { text:"موضوع گزارش: " + subject, options:{ fontSize:16, bold:true, color:T.dark, breakLine:true } },
    { text:"گروه / حوزه: " + group, options:{ fontSize:12.5, color:T.sub, breakLine:true } },
    { text:"بازه زمانی: " + range, options:{ fontSize:12.5, color:T.sub, breakLine:true } },
    { text:"تاریخ تولید گزارش: " + generated, options:{ fontSize:11, color:T.sub } }
  ], { x:0.6, y:2.7, w:W-1.6, h:2.3, align:"right", fontFace:FONT, rtlMode:true,
       valign:"top", lineSpacingMultiple:1.45 });
  s1.addText(
    "تعداد پیام‌ها: " + faNum(model.length) + "   |   شرکت‌کنندگان: " + faNum(nSenders) +
    "   |   عکس‌ها: " + faNum(photos) + "   |   کامنت‌ها و پاسخ‌ها: " + faNum(repliesN) +
    "   |   موضوعات: " + faNum(catList.length),
    { x:0.6, y:5.7, w:W-1.2, h:0.8, fontSize:11.5, color:T.sub, align:"right",
      fontFace:FONT, rtlMode:true });

  /* ---------- اسلاید خلاصه آماری ---------- */
  var s2 = pptx.addSlide(); slideNo++;
  s2.background = { color: T.bg };
  s2.addShape(RECT, { x:0, y:0, w:W, h:0.72, fill:{ color:T.accent } });
  s2.addText("خلاصه آماری گزارش", { x:0.5, y:0.06, w:W-1, h:0.6, fontSize:17, bold:true,
    color:"FFFFFF", align:"right", fontFace:FONT, rtlMode:true, valign:"middle" });
  var statItems = [
    ["پیام", faNum(model.length)],
    ["شرکت‌کننده", faNum(nSenders)],
    ["عکس", faNum(photos)],
    ["کامنت", faNum(repliesN)]
  ];
  var bw = (W - 1.2 - (statItems.length - 1) * 0.25) / statItems.length;
  for (var si = 0; si < statItems.length; si++){
    var bx = 0.6 + si * (bw + 0.25);
    s2.addShape(RECT, { x:bx, y:1.05, w:bw, h:1.15,
      fill:{ color: (T.bg === "FFFFFF") ? "F1F5F9" : "1E293B" } });
    s2.addText(statItems[si][1], { x:bx, y:1.12, w:bw, h:0.55, fontSize:20, bold:true,
      color:T.accent, align:"center", fontFace:FONT });
    s2.addText(statItems[si][0], { x:bx, y:1.68, w:bw, h:0.4, fontSize:11,
      color:T.sub, align:"center", fontFace:FONT, rtlMode:true });
  }
  s2.addText("توزیع پیام‌ها بر اساس موضوع", { x:0.5, y:2.5, w:W-1, h:0.45,
    fontSize:14, bold:true, color:T.ink, align:"right", fontFace:FONT, rtlMode:true });
  var maxCat = catCountsP[catList[0]] || 1;
  var trackX = 0.6, trackW = W - 3.4, rowY = 3.1;
  var showCats = catList.slice(0, 8);
  for (var ci = 0; ci < showCats.length; ci++){
    var cn = showCats[ci];
    var fillW = Math.max(0.15, trackW * catCountsP[cn] / maxCat);
    s2.addText(cn + " (" + faNum(catCountsP[cn]) + ")",
      { x:W-2.75, y:rowY, w:2.15, h:0.32, fontSize:11, color:T.ink, align:"right",
        fontFace:FONT, rtlMode:true, valign:"middle" });
    s2.addShape(RECT, { x:trackX, y:rowY+0.07, w:trackW, h:0.18,
      fill:{ color: (T.bg === "FFFFFF") ? "EDF1EF" : "1E293B" } });
    s2.addShape(RECT, { x:trackX + trackW - fillW, y:rowY+0.07, w:fillW, h:0.18,
      fill:{ color:T.accent } });
    rowY += 0.44;
  }
  if (catList.length > 8){
    s2.addText("… و " + faNum(catList.length - 8) + " موضوع دیگر",
      { x:0.6, y:rowY, w:W-1.2, h:0.35, fontSize:10.5, color:T.sub, align:"right",
        fontFace:FONT, rtlMode:true });
  }

  /* ---------- اسلایدهای پیام‌ها ---------- */
  var groups = groupModel(model, groupBy);
  for (var gk = 0; gk < groups.keys.length; gk++){
    var gname = groups.keys[gk];
    var garr = groups.map[gname];
    var perSlide = 4;
    var pages = Math.ceil(garr.length / perSlide);
    for (var p = 0; p < pages; p++){
      var sp = pptx.addSlide(); slideNo++;
      sp.background = { color: T.bg };
      sp.addShape(RECT, { x:0, y:0, w:W, h:0.72, fill:{ color:T.accent } });
      sp.addText(gname + "  (" + faNum(garr.length) + " پیام — بخش " + faNum(p+1) +
        " از " + faNum(pages) + ")", { x:0.5, y:0.06, w:W-1, h:0.6, fontSize:15,
        bold:true, color:"FFFFFF", align:"right", fontFace:FONT, rtlMode:true, valign:"middle" });
      var chunk = garr.slice(p * perSlide, p * perSlide + perSlide);
      var runs = [];
      for (var mi = 0; mi < chunk.length; mi++){
        var mm = chunk[mi];
        runs.push({ text: mm.sender + "  —  " + mm.when,
          options:{ fontSize:11, bold:true, color:T.dark, breakLine:true } });
        var body = mm.text ? trunc(mm.text, 430) : "—";
        runs.push({ text: body, options:{ fontSize:11.5, color:T.ink, breakLine:true } });
        for (var ri = 0; ri < Math.min(2, mm.replies.length); ri++){
          var rr = mm.replies[ri];
          runs.push({ text: "↩ " + rr.sender + ": " + trunc(rr.text || "[عکس]", 130),
            options:{ fontSize:10, color:T.sub, breakLine:true, italic:true } });
        }
        if (mm.imgs.length){
          runs.push({ text: "[" + faNum(mm.imgs.length) + " عکس" +
            (includeImages ? " — در اسلایدهای تصاویر" : "") + "]",
            options:{ fontSize:9.5, color:T.sub, breakLine:true, italic:true } });
        }
        runs.push({ text: " ", options:{ fontSize:5, breakLine:true } });
      }
      sp.addText(runs, { x:0.55, y:0.95, w:W-1.1, h:H-1.5, align:"right", valign:"top",
        fontFace:FONT, rtlMode:true, lineSpacingMultiple:1.25 });
      sp.addText(group + " — اسلاید " + faNum(slideNo),
        { x:0.5, y:H-0.42, w:W-1, h:0.3, fontSize:9, color:T.sub, align:"left",
          fontFace:FONT, rtlMode:true });
    }
  }

  /* ---------- اسلایدهای تصاویر ---------- */
  var imgNote = "";
  if (includeImages){
    var imgMsgs = model.filter(function(m){ return m.imgs.length > 0; });
    var MAX_IMG_MSGS = 40;
    if (imgMsgs.length > MAX_IMG_MSGS){
      imgNote = imgMsgs.length - MAX_IMG_MSGS;
      imgMsgs = imgMsgs.slice(0, MAX_IMG_MSGS);
    }
    for (var im2 = 0; im2 < imgMsgs.length; im2++){
      var m2 = imgMsgs[im2];
      for (var ch2 = 0; ch2 < Math.ceil(m2.imgs.length / 4); ch2++){
        var si2 = pptx.addSlide(); slideNo++;
        si2.background = { color: T.bg };
        si2.addShape(RECT, { x:0, y:0, w:W, h:0.6, fill:{ color:T.dark } });
        si2.addText(m2.sender + " — " + m2.when + "   (" + m2.cat + ")",
          { x:0.5, y:0.03, w:W-1, h:0.54, fontSize:12.5, bold:true, color:"FFFFFF",
            align:"right", fontFace:FONT, rtlMode:true, valign:"middle" });
        var imgs = m2.imgs.slice(ch2 * 4, ch2 * 4 + 4);
        var cellW = (W - 0.7 - 0.25) / 2;
        var cellH = (H - 1.45 - 0.45) / 2;
        for (var ii = 0; ii < imgs.length; ii++){
          var col = ii % 2, row = Math.floor(ii / 2);
          var x = (col === 0) ? (W - 0.35 - cellW) : 0.35;
          var y = 1.45 + row * (cellH + 0.2);
          try {
            si2.addImage({ data: imgs[ii].replace(/^data:/, ""),
              x:x, y:y, w:cellW, h:cellH,
              sizing:{ type:"contain", w:cellW, h:cellH } });
          } catch (eImg) {}
        }
        if (ch2 === 0 && m2.text){
          si2.addText(trunc(m2.text, 150), { x:0.5, y:H-0.5, w:W-1, h:0.42,
            fontSize:10, color:T.sub, align:"right", fontFace:FONT, rtlMode:true });
        }
        if (m2.imgs.length > 4 && ch2 === Math.ceil(m2.imgs.length / 4) - 1){
          si2.addText("… " + faNum(m2.imgs.length) + " عکس در این پیام",
            { x:0.5, y:H-0.9, w:W-1, h:0.35, fontSize:10, color:T.sub, align:"left",
              fontFace:FONT, rtlMode:true });
        }
      }
    }
    if (imgNote){
      var sn = pptx.addSlide(); slideNo++;
      sn.background = { color: T.bg };
      sn.addText("به دلیل حجم بالا، " + faNum(imgNote) +
        " پیام عکس‌دار آخر در پاورپوینت قرار نگرفت.",
        { x:1, y:H/2-0.5, w:W-2, h:1, fontSize:14, color:T.ink, align:"center",
          fontFace:FONT, rtlMode:true, valign:"middle" });
    }
  }

  var fname = "گزارش_پاورپوینت_" + stamp() + ".pptx";
  statusEl.textContent = "در حال ذخیره فایل (" + faNum(slideNo) + " اسلاید) ...";
  pptx.writeFile({ fileName: fname }).then(function(){
    statusEl.textContent = "فایل «" + fname + "» با " + faNum(slideNo) +
      " اسلاید ساخته و دانلود شد — " + faNum(model.length) + " پیام، تم " + T.name +
      "، فرمت " + (fmt === "4:3" ? "4:3" : "16:9");
  }).catch(function(err){
    statusEl.classList.add("err");
    statusEl.textContent = "ذخیره فایل ناموفق بود: " + (err && err.message ? err.message : err);
  });
}

/* ---------- نرمال‌سازی اولیه و اجرا ---------- */
(function init(){
  /* اگر فایل از قبل در حالت ویرایش/انتخاب ذخیره شده باشد، پاک می‌شود */
  document.body.classList.remove("edit-mode", "sel-mode");
  var boxes = pool.querySelectorAll(".pick-box");
  for (var i = 0; i < boxes.length; i++){
    boxes[i].checked = false;
    var pc = boxes[i].closest(".msg");
    if (pc) pc.classList.remove("picked");
  }
  state.selected = {};
  setEditMode(false);
  refreshChips();
  render();
})();
})();
"""

# ---------------------------------------------------------------- قالب کارت

CARD = Template("""<article class="msg" id="$anchor" data-cat="$attr_cat" data-sender="$attr_sender" data-chat="$attr_chat" data-photo="$attr_photo" data-ts="$attr_ts" data-date="$attr_date" data-when="$attr_when" data-mids="$attr_mids" data-txt="$attr_txt">
<button class="hide-btn" type="button" title="حذف این پیام از گزارش">✕</button>
<label class="pick" title="انتخاب برای عملیات گروهی"><input type="checkbox" class="pick-box"></label>
<div class="meta"><b>$sender</b><span>$when</span>$cat_edit$chips</div>
$gallery
<div class="body">$text</div>
$files
</article>""")

REPLY = Template("""<div class="reply">
<div class="rmeta"><b>$sender</b> — $when</div>
<div class="rbody">$text</div>$img
</div>""")


def _attr(s):
    """امن‌سازی برای استفاده داخل attributeهای HTML"""
    return html.escape(str(s or ""), quote=True)


def _body(s):
    """امن‌سازی متن پیام برای نمایش داخل صفحه"""
    return html.escape(str(s or ""), quote=False)


def _when(msg):
    """نمایش زمان پیام؛ یا timestamp یونیکس یا متن تاریخ خروجی CSV"""
    if msg.get("date"):
        return format_ts(msg["date"])
    parts = []
    dt = str(msg.get("date_text") or "").strip()
    ht = str(msg.get("hour_text") or "").strip()
    if dt and dt != "نامشخص":
        parts.append(dt)
    if ht and ht != "نامشخص":
        parts.append(ht)
    return " ".join(parts) or "بدون تاریخ"


def _date_str(msg):
    """تاریخ شمسی پیام برای گروه‌بندی و فیلتر بر اساس تاریخ ارسال"""
    if msg.get("date"):
        return format_ts(msg["date"], with_time=False) or "بدون تاریخ"
    dt = str(msg.get("date_text") or "").strip()
    return dt if dt and dt != "نامشخص" else "بدون تاریخ"


def _data_uri(path):
    """تبدیل فایل تصویر به data URI جاسازی‌شده در HTML (خودکفا شدن گزارش)"""
    if not path or not os.path.exists(path):
        return ""
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return ""
    if not data:
        return ""
    # کوچک‌سازی با Pillow در صورت وجود (خطا گزارش را متوقف نمی‌کند)
    try:
        from PIL import Image

        im = Image.open(io.BytesIO(data))
        im.thumbnail((1100, 1100))
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=72, optimize=True)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:
        ext = os.path.splitext(path)[1].lower()
        mime = {".png": "image/png", ".webp": "image/webp", ".gif": "image/gif"}.get(
            ext, "image/jpeg"
        )
        return f"data:{mime};base64," + base64.b64encode(data).decode("ascii")


def _fmt_size(size):
    try:
        size = int(size)
    except (TypeError, ValueError):
        return ""
    if size >= 1024 * 1024:
        return f" · {size / 1048576:.1f}MB"
    if size >= 1024:
        return f" · {size / 1024:.0f}KB"
    return f" · {size}B"


def _gallery_html(card, media_base):
    """گالری عکس‌های کارت (آلبوم) — تصاویر داخل فایل جاسازی می‌شوند"""
    photos = [x for x in card["media"] if x.get("type") in ("photo", "sticker")]
    others = [x for x in card["media"] if x.get("type") not in ("photo", "sticker")]
    parts = []
    if photos:
        imgs = []
        for x in photos:
            path = os.path.join(media_base, str(x.get("file") or "")) if x.get("file") else ""
            uri = _data_uri(path)
            if uri:
                imgs.append(f'<img src="{uri}" alt="تصویر پیام">')
            else:
                imgs.append('<div class="missing-img">این تصویر ذخیره نشده است — '
                            'پس از دریافت مجدد پیام، عکس به‌طور خودکار دانلود می‌شود</div>')
        cls = "gallery single" if len(imgs) == 1 else "gallery"
        parts.append(f'<div class="{cls}">{"".join(imgs)}</div>')
    if others:
        chips = []
        for x in others:
            label = _attr(x.get("name") or "فایل")
            size = _fmt_size(x.get("size"))
            dur = x.get("duration")
            if dur:
                try:
                    m, s = divmod(int(dur), 60)
                    size += f" · {m}:{s:02d}"
                except (TypeError, ValueError):
                    pass
            chips.append(f'<span class="file-chip">📎 {label}{_attr(size)}</span>')
        parts.append(f'<div class="files">{"".join(chips)}</div>')
    return "".join(parts)


def _chips_html(card, show_chat, parent_anchor):
    """چیپ‌های کارت: رسانه، بازنشر، ویرایش، گروه، شمارش پاسخ و پیوند پیام مرتبط"""
    chips = []
    m = card["primary"]
    n_photos = sum(1 for x in card["media"] if x.get("type") in ("photo", "sticker"))
    n_other = len(card["media"]) - n_photos
    if n_photos:
        chips.append(f'<span class="chip media">{n_photos} عکس</span>')
    if n_other:
        chips.append(f'<span class="chip media">{n_other} رسانه</span>')
    if card["replies"]:
        chips.append(
            f'<span class="chip replies-n">{len(card["replies"])} پاسخ / کامنت</span>'
        )
    if (m.get("forward") or {}).get("source"):
        src = _attr(m["forward"]["source"] or "نامشخص")
        chips.append(f'<span class="chip fwd">بازنشر از {src}</span>')
    if m.get("edited"):
        chips.append('<span class="chip edit">ویرایش‌شده</span>')
    if show_chat and m.get("chat_title"):
        chips.append(f'<span class="chip">{_attr(m["chat_title"])}</span>')
    rt = card.get("reply_to")
    if rt:
        snippet = _attr((rt or {}).get("snippet") or "")
        sender = _attr((rt or {}).get("sender") or "پیام دیگر")
        if parent_anchor:
            chips.append(
                f'<a class="chip rel" href="#{parent_anchor}" '
                f'title="پرش به پیام مرتبط">↩ در پاسخ به {sender}: {snippet}</a>'
            )
        else:
            chips.append(f'<span class="chip rel">↩ در پاسخ به {sender}: {snippet}</span>')
    return "".join(chips)


def _reply_html(msg, media_base):
    """کارت فشرده برای کامنت/پاسخ زیر پیام اصلی"""
    text = msg.get("text") or msg.get("caption") or ""
    imgs = []
    for x in msg.get("media") or []:
        path = os.path.join(media_base, str(x.get("file") or "")) if x.get("file") else ""
        uri = _data_uri(path)
        if uri:
            imgs.append(f'<img src="{uri}" alt="تصویر">')
    img_html = "".join(imgs)
    text_html = _body(text) if text else _body(
        "[عکس]" if msg.get("media") else "—"
    )
    return REPLY.substitute(
        sender=_attr(msg.get("sender_name") or msg.get("username") or "ناشناس"),
        when=_attr(_when(msg)),
        text=text_html,
        img=img_html,
    )


def _key(chat_id, message_id):
    return (str(chat_id), str(message_id))


def _anchor_for(chat_id, message_id):
    """شناسه لنگر HTML کارت — برای پیوند «در پاسخ به»"""
    return f"m_{str(chat_id).replace('-', 'n')}_{str(message_id).replace('-', 'n')}"


def _build_cards(msgs):
    """ساخت کارت‌ها: ادغام آلبوم عکس‌ها + نگاشت شناسه‌ها"""
    cards = []
    alias = {}  # (chat_id, message_id) → کارت
    last = None
    for m in msgs:
        mg = m.get("media_group_id")
        if mg and last is not None and last["media_group_id"] == mg \
                and last["chat_id"] == m.get("chat_id"):
            last["media"].extend(m.get("media") or [])
            last["ids"].append(m.get("message_id"))
            if not last["text"] and m.get("text"):
                last["text"] = m.get("text")
            if not last["caption"] and m.get("caption"):
                last["caption"] = m.get("caption")
        else:
            card = {
                "primary": m,
                "chat_id": m.get("chat_id"),
                "media_group_id": mg,
                "media": list(m.get("media") or []),
                "ids": [m.get("message_id")],
                "text": m.get("text") or "",
                "caption": m.get("caption") or "",
                "replies": [],
            }
            cards.append(card)
            last = card
    for card in cards:
        for mid in card["ids"]:
            alias[_key(card["chat_id"], mid)] = card
    return cards, alias


def _options_html(counter, ordered=None):
    """ساخت گزینه‌های <select> بر اساس شمارش (یا ترتیب داده‌شده)"""
    items = ordered if ordered is not None else [c for c, _ in counter.most_common()]
    out = []
    for name in items:
        n = counter.get(name, 0)
        if not name:
            continue
        out.append(f'<option value="{_attr(name)}">{_attr(name)} ({n})</option>')
    return "\n".join(out)


def _cat_select_html(cats, current):
    """فهرست تغییر دسته پیام در حالت ویرایش

    فهرست کامل: دسته‌های موجود در داده‌ها + همه دسته‌های استاندارد قوانین
    پیش‌فرض (حتی اگر هنوز پیامی در آن‌ها نباشد) تا کاربر بتواند هر پیام را
    به هر موضوع استاندارد حوزه منتقل کند.
    """
    names = list(cats)
    for c in [n for n, _ in parse_rules(DEFAULT_RULES)]:
        if c not in names:
            names.append(c)
    if not names:
        return ""
    opts = []
    for c in names:
        sel = " selected" if c == current else ""
        opts.append(f'<option value="{_attr(c)}"{sel}>{_attr(c)}</option>')
    return (
        '<select class="cat-edit" title="تغییر دسته این پیام">'
        + "".join(opts) + "</select>"
    )


def _load_pptx_lib():
    """خواندن کتابخانه PptxGenJS برای جاسازی داخل فایل گزارش (کارکرد آفلاین)"""
    try:
        with open(PPTX_LIB_PATH, encoding="utf-8") as f:
            code = f.read()
    except OSError:
        return ""
    # جلوگیری از بسته‌شدن زودهنگام تگ script داخل کد جاوااسکریپت
    return code.replace("</script", "<\\/script")


def _bars_html(counter, ordered, color_of):
    """ساخت نوارهای توزیع (موضوع یا تاریخ)"""
    if not counter:
        return '<div class="empty" style="padding:14px">داده‌ای برای نمایش نیست.</div>'
    max_count = max(counter.values()) if counter else 1
    rows = []
    for name in ordered:
        n = counter.get(name, 0)
        rows.append(
            '<div class="bar-row">'
            f'<div class="bar-label">{_attr(name)}</div>'
            f'<div class="bar-track"><div class="bar-fill" '
            f'style="width:{max(2, int(n * 100 / max_count))}%;'
            f'background:{color_of(name)}"></div></div>'
            f'<div class="bar-num">{n}</div></div>'
        )
    return "\n".join(rows)


def build_report(messages, output_path, group_title=None, media_base=None):
    """ساخت فایل گزارش HTML تعاملی و برگرداندن مسیر مطلق آن"""
    if media_base is None:
        media_base = os.path.dirname(os.path.abspath(output_path))

    msgs = [m for m in (messages or []) if isinstance(m, dict)]
    msgs.sort(key=lambda m: m.get("date") or 0)
    counter = Counter((m.get("category") or "سایر") for m in msgs)
    cats = [c for c, _ in counter.most_common()]
    color_map = {c: PALETTE[i % len(PALETTE)] for i, c in enumerate(cats)}

    # آمار تاریخ‌ها (بر اساس تاریخ ارسال شمسی)
    date_counter = Counter(_date_str(m) for m in msgs)
    date_min = {}
    for m in msgs:
        d = _date_str(m)
        ts = m.get("date") or 0
        if d not in date_min:
            date_min[d] = ts
        elif ts and (date_min[d] == 0 or ts < date_min[d]):
            date_min[d] = ts
    dates = sorted(
        date_counter.keys(),
        key=lambda d: (1, 0) if not date_min[d] else (0, date_min[d]),
    )

    if group_title:
        title = str(group_title)
    else:
        titles = [m.get("chat_title") for m in msgs if m.get("chat_title")]
        title = Counter(titles).most_common(1)[0][0] if titles else "بدون عنوان"

    subject = "عملکرد " + title.split("(")[0].strip()

    participants = set()
    photos_total = 0
    media_total = 0
    chat_titles = set()
    for m in msgs:
        p = m.get("sender_name") or m.get("username") or m.get("sender_id")
        if p:
            participants.add(str(p))
        for x in m.get("media") or []:
            media_total += 1
            if x.get("type") in ("photo", "sticker"):
                photos_total += 1
        if m.get("chat_title"):
            chat_titles.add(m["chat_title"])
    show_chat = len(chat_titles) > 1

    cards, alias = _build_cards(msgs)

    # اتصال پاسخ‌ها/کامنت‌ها به کارت پیام اصلی (مرتبط‌سازی)
    top_cards = []
    for card in cards:
        m = card["primary"]
        rt = m.get("reply_to")
        parent = None
        if rt:
            parent = alias.get(_key(rt.get("chat_id", m.get("chat_id")),
                                    rt.get("message_id")))
            if parent is None:
                parent = alias.get(_key(m.get("chat_id"), rt.get("message_id")))
        if parent is not None and parent is not card:
            parent["replies"].append(card)
        else:
            top_cards.append(card)
            card["reply_to"] = rt

    replies_total = sum(len(c["replies"]) for c in cards)

    sender_counter = Counter(
        (m.get("sender_name") or m.get("username") or "ناشناس") for m in msgs
    )
    chat_counter = Counter(m.get("chat_title") or "بدون گروه" for m in msgs)

    # ---------- کارت‌ها داخل مخزن (رندر نهایی در مرورگر با گروه‌بندی دلخواه) ----------
    pool_parts = []
    for card in top_cards:
        m = card["primary"]
        body = card["text"] or card["caption"]
        gallery = _gallery_html(card, media_base)
        text_html = _body(body) if (body or "").strip() else ""
        if not (body or "").strip() and not gallery:
            text_html = "—"

        search_text = " ".join(
            filter(None, [
                body,
                m.get("sender_name") or "",
                m.get("username") or "",
                m.get("chat_title") or "",
                m.get("category") or "",
                " ".join(
                    (r["primary"].get("text") or "")
                    + " "
                    + (r["primary"].get("caption") or "")
                    + " "
                    + (r["primary"].get("sender_name") or "")
                    for r in card["replies"]
                ),
            ])
        ).lower().replace('"', " ")

        anchor = _anchor_for(card["chat_id"], card["ids"][0])
        rt = card.get("reply_to")
        parent_anchor = ""
        if rt:
            pk = _key(rt.get("chat_id", card["chat_id"]), rt.get("message_id"))
            if pk in alias and alias[pk] is not card:
                parent_anchor = _anchor_for(pk[0], pk[1])
            else:
                pk = _key(card["chat_id"], rt.get("message_id"))
                if pk in alias and alias[pk] is not card:
                    parent_anchor = _anchor_for(pk[0], pk[1])

        chips = _chips_html(card, show_chat, parent_anchor)
        if card["replies"]:
            rts = "".join(_reply_html(r["primary"], media_base) for r in card["replies"])
            card["_replies_html"] = (
                f'<div class="replies"><div class="replies-title">'
                f"{len(card['replies'])} پاسخ / کامنت:</div>{rts}</div>"
            )

        mids = ",".join(
            f"{card['chat_id']}:{mid}" for mid in card["ids"] if mid is not None
        )
        pool_parts.append(
            CARD.substitute(
                anchor=_attr(anchor),
                attr_cat=_attr(m.get("category") or "سایر"),
                attr_sender=_attr(
                    m.get("sender_name") or m.get("username") or "ناشناس"
                ),
                attr_chat=_attr(m.get("chat_title") or "بدون گروه"),
                attr_photo="1" if any(
                    x.get("type") in ("photo", "sticker") for x in card["media"]
                ) else "0",
                attr_ts=_attr(m.get("date") or 0),
                attr_date=_attr(_date_str(m)),
                attr_when=_attr(_when(m)),
                attr_mids=_attr(mids),
                attr_txt=_attr(search_text[:4000]),
                sender=_attr(
                    m.get("sender_name") or m.get("username") or "ناشناس"
                ),
                when=_attr(_when(m)),
                cat_edit=_cat_select_html(cats, m.get("category") or "سایر"),
                chips=chips,
                gallery=gallery + card.get("_replies_html", ""),
                text=text_html,
                files="",
            )
        )
    pool_html = "\n".join(pool_parts)

    if msgs:
        bars = _bars_html(counter, cats, lambda c: color_map.get(c, "#64748b"))
        date_colors = {d: PALETTE[i % len(PALETTE)] for i, d in enumerate(dates)}
        shown_dates = dates[:16]
        date_bars = _bars_html(date_counter, shown_dates, lambda d: date_colors.get(d, "#475569"))
        if len(dates) > 16:
            date_bars += (
                f'<div class="bar-note">… و {len(dates) - 16} تاریخ دیگر — '
                "برای دیدن هر روز از فیلتر «تاریخ» در نوار ابزار استفاده کنید</div>"
            )
        cat_chips = "\n".join(
            f'<button type="button" class="chip-btn" data-cat="{_attr(c)}">'
            f'<span class="dot" style="background:{color_map[c]}"></span>'
            f'{_attr(c)} <b>{n}</b></button>'
            for c, n in counter.most_common()
        )
        sections_html = ""  # رندر بخش‌ها با جاوااسکریپت انجام می‌شود (گروه‌بندی دلخواه)
        if not pool_html:
            sections_html = (
                '<div class="box empty">همه پیام‌ها به‌صورت پاسخ زیر پیام‌های دیگر '
                "نمایش داده می‌شوند.</div>"
            )
    else:
        bars = '<div class="empty">پیامی برای نمایش وجود ندارد.</div>'
        date_bars = '<div class="empty">پیامی برای نمایش وجود ندارد.</div>'
        cat_chips = ""
        sections_html = (
            '<div class="box empty">پیامی برای نمایش وجود ندارد؛ '
            "ابتدا از بخش «دریافت پیام» شروع کنید یا فایل CSV پیام‌های قدیمی را وارد کنید."
            "</div>"
        )

    dated = [m for m in msgs if m.get("date")]
    if dated:
        rng = (
            f"{format_ts(dated[0]['date'], with_time=False)}"
            f" تا {format_ts(dated[-1]['date'], with_time=False)}"
        )
    else:
        texts = [str(m.get("date_text")) for m in msgs if m.get("date_text")]
        rng = f"{texts[0]} تا {texts[-1]}" if texts else "—"

    topcat = counter.most_common(1)[0][0] if counter else "—"

    out = PAGE.substitute(
        title=_attr(title),
        subject=_attr(subject),
        group_attr=_attr(title),
        generated=now_str(),
        total=len(msgs),
        participants=len(participants),
        photos=photos_total,
        media=media_total,
        replies=replies_total,
        ncats=len(counter),
        ndates=len(dates),
        topcat=_attr(topcat),
        bars=bars,
        date_bars=date_bars,
        date_options=_options_html(date_counter, ordered=dates),
        sender_options=_options_html(sender_counter),
        chat_options=_options_html(chat_counter),
        chat_hidden="" if show_chat else "hidden",
        cat_chips=cat_chips,
        sections=sections_html,
        pool=pool_html,
        range=_attr(rng),
        version=VERSION,
    )
    out = out.replace("<!--MAIN_JS-->", MAIN_JS)
    out = out.replace("/*__PPTX_LIB__*/", _load_pptx_lib())

    directory = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(directory, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(out)
    return os.path.abspath(output_path)
