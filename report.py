# -*- coding: utf-8 -*-
"""ساخت گزارش HTML تک‌فایلی، راست‌به‌چپ و فارسی از پیام‌های دسته‌بندی‌شده

نسخه ۴.۶ — گزارش تعاملی با قابلیت‌های کامل:
    - نوار فیلتر: جست‌وجوی زنده در متن/کپشن/فرستنده/گروه، فیلتر چندگانه
      دسته‌ها (چیپ‌ها)، فیلتر فرستنده و گروه، فیلتر «فقط پیام‌های عکس‌دار»
    - دسته‌بندی: بخش‌بندی پیام‌ها بر اساس دسته با شمارش زنده هر بخش
    - مرتبط‌سازی: کامنت‌ها/پاسخ‌ها به‌صورت تو در تو زیر پیام اصلی +
      پیوند «در پاسخ به» با پرش و هایلایت پیام مرتبط
    - حذف هر پیام از نمایش با دکمه ✕ و نوار بازیابی (خروجی تمیز و دلخواه)
    - عکس‌ها و آلبوم‌ها به‌صورت base64 داخل خود فایل جاسازی می‌شوند تا
      گزارش هر جا و بدون برنامه قابل باز کردن باشد
"""

import base64
import html
import io
import os
from collections import Counter
from string import Template

from jalali import format_ts, now_str
from version import VERSION

PALETTE = [
    "#0e9f6e", "#2563eb", "#d97706", "#dc2626", "#7c3aed",
    "#0d9488", "#db2777", "#475569", "#9333ea", "#0891b2",
]

PAGE = Template("""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>گزارش پیام‌های گروه — $title</title>
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
.hero h1{margin:0 0 8px;font-size:21px}
.hero p{margin:2px 0;opacity:.92;font-size:13px}
.stats{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:18px}
.stat{flex:1 1 130px;background:var(--card);border:1px solid var(--border);
border-radius:12px;padding:14px;text-align:center}
.stat b{display:block;font-size:21px;color:var(--primary-dark);margin-bottom:4px}
.stat span{font-size:12px;color:var(--muted)}
.box{background:var(--card);border:1px solid var(--border);border-radius:12px;
padding:18px;margin-bottom:18px}
.box h3{margin:0 0 12px;font-size:15px}
.bar-row{display:flex;align-items:center;gap:10px;margin:9px 0}
.bar-label{width:150px;font-size:13px;flex-shrink:0;overflow:hidden;
text-overflow:ellipsis;white-space:nowrap}
.bar-track{flex:1;background:#edf1ef;border-radius:999px;height:14px;overflow:hidden}
.bar-fill{height:100%;border-radius:999px;min-width:6px}
.bar-num{width:36px;font-size:12px;color:var(--muted);text-align:left}

/* ---------- نوار فیلتر ---------- */
.toolbar{background:var(--card);border:1px solid var(--border);border-radius:12px;
padding:14px;margin-bottom:18px;position:sticky;top:8px;z-index:5;
box-shadow:0 4px 14px rgba(15,40,30,.07)}
.tb-row{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.toolbar input[type=search]{flex:1 1 220px;font-family:inherit;font-size:13.5px;
border:1px solid var(--border);border-radius:10px;padding:9px 14px;background:#fbfdfc}
.toolbar select{font-family:inherit;font-size:13px;border:1px solid var(--border);
border-radius:10px;padding:8px 10px;background:#fbfdfc;color:var(--ink);max-width:200px}
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
.tb-info{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-top:10px;
font-size:12.5px;color:var(--muted)}
.link-btn{font-family:inherit;font-size:12.5px;background:none;border:none;
color:var(--primary-dark);cursor:pointer;text-decoration:underline;padding:0}

section.cat{background:var(--card);border:1px solid var(--border);border-radius:12px;
padding:16px;margin-bottom:14px}
section.cat h2{font-size:15px;margin:0 0 10px;display:flex;align-items:center;
gap:8px;flex-wrap:wrap}
.dot{width:11px;height:11px;border-radius:50%;display:inline-block;flex-shrink:0}
.badge{font-size:11px;background:#e8f7f1;color:var(--primary-dark);
border-radius:999px;padding:2px 10px}
.badge.vis-badge{background:#f1f5f9;color:#64748b;display:none}
section.cat.filtered .badge.vis-badge{display:inline-block}
.msg{border:1px solid var(--border);border-radius:10px;padding:10px 12px;
margin:8px 0;font-size:13.5px;line-height:1.9;background:#fcfdfc;position:relative}
.msg:hover{border-color:#c9d6d0}
.msg .meta{font-size:11.5px;color:var(--muted);margin-bottom:4px}
.msg .meta b{color:var(--ink)}
.msg .body{white-space:pre-wrap;word-wrap:break-word}
.msg:target{outline:2px solid var(--primary);background:#eefaf5}
.hide-btn{position:absolute;top:7px;left:7px;width:22px;height:22px;border-radius:7px;
border:1px solid var(--border);background:#fff;color:#9ca3af;font-size:11px;
cursor:pointer;line-height:1;opacity:0;transition:.15s}
.msg:hover .hide-btn{opacity:1}
.hide-btn:hover{background:#fee2e2;color:#b91c1c;border-color:#fca5a5}
.msg.hidden-card{display:none!important}
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
#hiddenBar{position:fixed;bottom:16px;right:50%;transform:translateX(50%);
background:#1f2937;color:#f9fafb;border-radius:999px;padding:9px 18px;
font-size:12.5px;display:flex;gap:12px;align-items:center;z-index:40;
box-shadow:0 6px 20px rgba(0,0,0,.25)}
#hiddenBar button{font-family:inherit;font-size:12px;background:#374151;color:#fbbf24;
border:none;border-radius:999px;padding:5px 12px;cursor:pointer}
footer{text-align:center;color:var(--muted);font-size:12px;padding:8px 0 0}
@media print{.toolbar,#hiddenBar,.hide-btn{display:none!important}
body{background:#fff;padding:0}}
</style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <h1>گزارش پیام‌های گروه: $title</h1>
    <p>تاریخ تولید گزارش: $generated</p>
    <p>تعداد پیام‌ها: $total &nbsp;|&nbsp; بازه زمانی: $range</p>
  </div>
  <div class="stats">
    <div class="stat"><b>$total</b><span>کل پیام‌ها</span></div>
    <div class="stat"><b>$participants</b><span>شرکت‌کنندگان</span></div>
    <div class="stat"><b>$photos</b><span>عکس‌ها</span></div>
    <div class="stat"><b>$media</b><span>کل رسانه‌ها</span></div>
    <div class="stat"><b>$replies</b><span>کامنت‌ها و پاسخ‌ها</span></div>
    <div class="stat"><b>$ncats</b><span>تعداد دسته‌ها</span></div>
    <div class="stat"><b>$topcat</b><span>دسته پرپیام</span></div>
  </div>
  <div class="box">
    <h3>توزیع پیام‌ها بر اساس دسته</h3>
    $bars
  </div>

  <div class="toolbar">
    <div class="tb-row">
      <input type="search" id="q" placeholder="جست‌وجو در متن پیام، کپشن، فرستنده، گروه ...">
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
      <button type="button" class="chip-btn active" data-cat="">همه دسته‌ها</button>
      $cat_chips
    </div>
    <div class="tb-info">
      <span id="visCount"></span>
      <button type="button" class="link-btn" id="btnClearFilters">پاک‌کردن فیلترها</button>
      <span>برای تمیزکردن خروجی، هر پیام را با دکمه ✕ (روی کارت) از نمایش حذف کنید</span>
    </div>
  </div>

  <div id="sections">
  $sections
  </div>
  <div class="empty hidden" id="noResult">هیچ پیامی با این فیلترها پیدا نشد — «پاک‌کردن فیلترها» را بزنید.</div>

  <footer>تولیدشده با برنامه Bale Chat Mosharket نسخه $version — دریافت و دسته‌بندی پیام‌های گروه بله</footer>
</div>

<div id="imgOverlay"><img id="imgOverlayImg" src="" alt=""></div>
<div id="hiddenBar" class="hidden">
  <span><b id="hiddenCount">۰</b> پیام از نمایش حذف شد</span>
  <button type="button" id="btnShowAll">نمایش همه دوباره</button>
</div>

<script>
(function(){
"use strict";
var totalMsgs = $total;
var catSel = {};
var qEl = document.getElementById("q");
var senderEl = document.getElementById("senderSel");
var chatEl = document.getElementById("chatSel");
var photoEl = document.getElementById("photoOnly");
var visEl = document.getElementById("visCount");
var noResult = document.getElementById("noResult");
var hiddenBar = document.getElementById("hiddenBar");
var hiddenCount = document.getElementById("hiddenCount");
var sections = [].slice.call(document.querySelectorAll("#sections > section"));
var hiddenTotal = 0;

function faNum(n){
  return String(n).replace(/[0-9]/g, function(d){ return "۰۱۲۳۴۵۶۷۸۹"[d]; });
}

function cardVisible(c){
  if (c._hidden) return false;
  var keys = Object.keys(catSel);
  if (keys.length && !catSel[c.getAttribute("data-cat")]) return false;
  var s = senderEl.value;
  if (s && c.getAttribute("data-sender") !== s) return false;
  var ch = chatEl ? chatEl.value : "";
  if (ch && c.getAttribute("data-chat") !== ch) return false;
  if (photoEl.checked && c.getAttribute("data-photo") !== "1") return false;
  var t = qEl.value.trim().toLowerCase();
  if (t && (c.getAttribute("data-txt") || "").indexOf(t) === -1) return false;
  return true;
}

function apply(){
  var vis = 0;
  for (var i = 0; i < sections.length; i++){
    var sec = sections[i];
    var msgEls = sec.querySelectorAll(".msg");
    var secVis = 0;
    for (var j = 0; j < msgEls.length; j++){
      var show = cardVisible(msgEls[j]);
      msgEls[j].style.display = show ? "" : "none";
      if (show) secVis++;
    }
    sec.style.display = secVis ? "" : "none";
    sec.classList.toggle("filtered", secVis !== msgEls.length);
    var badge = sec.querySelector(".vis-badge");
    if (badge) badge.textContent = "نمایش " + faNum(secVis) + " از " + faNum(msgEls.length);
    vis += secVis;
  }
  visEl.textContent = "نمایش " + faNum(vis) + " پیام از " + faNum(totalMsgs) + " پیام";
  noResult.classList.toggle("hidden", vis > 0);
}

function refreshChipStates(){
  var chips = document.querySelectorAll("#catChips .chip-btn");
  for (var i = 0; i < chips.length; i++){
    var cc = chips[i].getAttribute("data-cat");
    var on = (cc === "") ? (Object.keys(catSel).length === 0) : !!catSel[cc];
    chips[i].classList.toggle("active", on);
  }
}

document.getElementById("catChips").addEventListener("click", function(ev){
  var b = ev.target.closest(".chip-btn");
  if (!b) return;
  var c = b.getAttribute("data-cat");
  if (c === "") { catSel = {}; }
  else if (catSel[c]) { delete catSel[c]; }
  else { catSel[c] = true; }
  refreshChipStates();
  apply();
});

qEl.addEventListener("input", apply);
senderEl.addEventListener("change", apply);
if (chatEl) chatEl.addEventListener("change", apply);
photoEl.addEventListener("change", apply);

document.getElementById("btnClearFilters").addEventListener("click", function(){
  catSel = {};
  refreshChipStates();
  qEl.value = "";
  senderEl.value = "";
  if (chatEl) chatEl.value = "";
  photoEl.checked = false;
  apply();
});

document.getElementById("sections").addEventListener("click", function(ev){
  var btn = ev.target.closest(".hide-btn");
  if (!btn) return;
  var card = btn.closest(".msg");
  if (!card) return;
  card._hidden = true;
  card.classList.add("hidden-card");
  hiddenTotal++;
  hiddenCount.textContent = faNum(hiddenTotal);
  hiddenBar.classList.remove("hidden");
  apply();
});

document.getElementById("btnShowAll").addEventListener("click", function(){
  var all = document.querySelectorAll("#sections .msg.hidden-card");
  for (var i = 0; i < all.length; i++){
    all[i]._hidden = false;
    all[i].classList.remove("hidden-card");
  }
  hiddenTotal = 0;
  hiddenBar.classList.add("hidden");
  apply();
});

/* بزرگ‌نمایی عکس با کلیک */
var overlay = document.getElementById("imgOverlay");
var overlayImg = document.getElementById("imgOverlayImg");
document.getElementById("sections").addEventListener("click", function(ev){
  var img = ev.target.closest(".gallery img");
  if (!img) return;
  overlayImg.src = img.src;
  overlay.style.display = "flex";
});
overlay.addEventListener("click", function(){
  overlay.style.display = "none";
  overlayImg.src = "";
});
document.addEventListener("keydown", function(ev){
  if (ev.key === "Escape" && overlay.style.display === "flex"){
    overlay.style.display = "none";
    overlayImg.src = "";
  }
});

apply();
})();
</script>
</body>
</html>
""")

SECTION = Template("""<section class="cat" data-cat="$attr">
<h2><span class="dot" style="background:$color"></span>$name
<span class="badge">$count پیام</span><span class="badge vis-badge"></span></h2>
$cards
</section>""")

CARD = Template("""<article class="msg" id="$anchor" data-cat="$attr_cat" data-sender="$attr_sender" data-chat="$attr_chat" data-photo="$attr_photo" data-txt="$attr_txt">
<button class="hide-btn" type="button" title="حذف این پیام از نمایش خروجی">✕</button>
<div class="meta"><b>$sender</b> — $when $chips</div>
$gallery
<div class="body">$text</div>
$files
$replies
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
        uris = []
        for x in photos:
            path = os.path.join(media_base, str(x.get("file") or "")) if x.get("file") else ""
            uri = _data_uri(path)
            uris.append(uri)
        cls = "gallery single" if len(uris) == 1 else "gallery"
        imgs = []
        for x, uri in zip(photos, uris):
            if uri:
                imgs.append(f'<img src="{uri}" alt="تصویر پیام">')
            else:
                imgs.append('<div class="missing-img">این تصویر ذخیره نشده است — '
                            'پس از دریافت مجدد پیام، عکس به‌طور خودکار دانلود می‌شود</div>')
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


def _options_html(counter):
    """ساخت گزینه‌های <select> فرستنده‌ها/گروه‌ها بر اساس تعداد پیام"""
    out = []
    for name, n in counter.most_common():
        if not name:
            continue
        out.append(f'<option value="{_attr(name)}">{_attr(name)} ({n})</option>')
    return "\n".join(out)


def build_report(messages, output_path, group_title=None, media_base=None):
    """ساخت فایل گزارش HTML و برگرداندن مسیر مطلق آن"""
    if media_base is None:
        media_base = os.path.dirname(os.path.abspath(output_path))

    msgs = [m for m in (messages or []) if isinstance(m, dict)]
    msgs.sort(key=lambda m: m.get("date") or 0)
    counter = Counter((m.get("category") or "سایر") for m in msgs)
    cats = [c for c, _ in counter.most_common()]
    color_map = {c: PALETTE[i % len(PALETTE)] for i, c in enumerate(cats)}

    if group_title:
        title = str(group_title)
    else:
        titles = [m.get("chat_title") for m in msgs if m.get("chat_title")]
        title = Counter(titles).most_common(1)[0][0] if titles else "بدون عنوان"

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

    # شمارنده‌های فرستنده و گروه برای فیلترها (روی همه پیام‌ها)
    sender_counter = Counter(
        (m.get("sender_name") or m.get("username") or "ناشناس") for m in msgs
    )
    chat_counter = Counter(m.get("chat_title") or "بدون گروه" for m in msgs)

    max_count = max(counter.values()) if counter else 0
    if counter:
        bars = "\n".join(
            '<div class="bar-row">'
            f'<div class="bar-label">{_attr(c)}</div>'
            f'<div class="bar-track"><div class="bar-fill" '
            f'style="width:{int(n * 100 / max_count)}%;background:{color_map[c]}"></div></div>'
            f'<div class="bar-num">{n}</div></div>'
            for c, n in counter.most_common()
        )
        cat_chips = "\n".join(
            f'<button type="button" class="chip-btn" data-cat="{_attr(c)}">'
            f'<span class="dot" style="background:{color_map[c]}"></span>'
            f'{_attr(c)} <b>{n}</b></button>'
            for c, n in counter.most_common()
        )
        sections = []
        for c, n in counter.most_common():
            rendered = []
            for card in top_cards:
                if (card["primary"].get("category") or "سایر") != c:
                    continue
                m = card["primary"]
                body = card["text"] or card["caption"]
                gallery = _gallery_html(card, media_base)
                text_html = _body(body) if (body or "").strip() else ""
                if not (body or "").strip() and not gallery:
                    text_html = "—"

                # متن کامل برای جست‌وجو: پیام + کپشن + متن همه پاسخ‌ها
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
                files = ""
                if card["replies"]:
                    rts = "".join(_reply_html(r["primary"], media_base) for r in card["replies"])
                    files = (
                        f'<div class="replies"><div class="replies-title">'
                        f"{len(card['replies'])} پاسخ / کامنت:</div>{rts}</div>"
                    )
                rendered.append(
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
                        attr_txt=_attr(search_text[:4000]),
                        sender=_attr(
                            m.get("sender_name") or m.get("username") or "ناشناس"
                        ),
                        when=_attr(_when(m)),
                        chips=chips,
                        gallery=gallery,
                        text=text_html,
                        files=files,
                        replies="",
                    )
                )
            cards_html = "\n".join(rendered)
            if not cards_html and n > 0:
                cards_html = (
                    '<div class="empty" style="padding:14px;font-size:12.5px">'
                    "همه پیام‌های این دسته به‌صورت پاسخ زیر پیام‌های دیگر نمایش داده می‌شوند."
                    "</div>"
                )
            sections.append(
                SECTION.substitute(
                    attr=_attr(c),
                    color=color_map[c],
                    name=_attr(c),
                    count=n,
                    cards=cards_html,
                )
            )
        sections_html = "\n".join(sections)
    else:
        bars = '<div class="empty">پیامی برای نمایش وجود ندارد.</div>'
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
        generated=now_str(),
        total=len(msgs),
        participants=len(participants),
        photos=photos_total,
        media=media_total,
        replies=replies_total,
        ncats=len(counter),
        topcat=_attr(topcat),
        bars=bars,
        sender_options=_options_html(sender_counter),
        chat_options=_options_html(chat_counter),
        chat_hidden="" if show_chat else "hidden",
        cat_chips=cat_chips,
        sections=sections_html,
        range=_attr(rng),
        version=VERSION,
    )

    directory = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(directory, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(out)
    return os.path.abspath(output_path)
