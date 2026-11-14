# -*- coding: utf-8 -*-
"""ساخت گزارش HTML تک‌فایلی، راست‌به‌چپ و فارسی از پیام‌های دسته‌بندی‌شده"""

import html
import os
from collections import Counter
from string import Template

from jalali import format_ts, now_str

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
body{font-family:Vazirmatn,Tahoma,'Segoe UI',sans-serif;background:var(--bg);
color:var(--ink);margin:0;padding:24px 16px}
.wrap{max-width:920px;margin:0 auto}
.hero{background:linear-gradient(135deg,var(--primary),var(--primary-dark));color:#fff;
border-radius:16px;padding:26px 30px;margin-bottom:18px}
.hero h1{margin:0 0 8px;font-size:21px}
.hero p{margin:2px 0;opacity:.92;font-size:13px}
.stats{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:18px}
.stat{flex:1 1 150px;background:var(--card);border:1px solid var(--border);
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
.filters{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px}
.filters button{font-family:inherit;font-size:13px;cursor:pointer;
border:1px solid var(--border);background:#fff;border-radius:999px;
padding:6px 14px;color:var(--ink)}
.filters button.active{background:var(--primary);color:#fff;border-color:var(--primary)}
section.cat{background:var(--card);border:1px solid var(--border);border-radius:12px;
padding:16px;margin-bottom:14px}
section.cat h2{font-size:15px;margin:0 0 10px;display:flex;align-items:center;gap:8px}
.dot{width:11px;height:11px;border-radius:50%;display:inline-block;flex-shrink:0}
.badge{font-size:11px;background:#e8f7f1;color:var(--primary-dark);
border-radius:999px;padding:2px 10px;font-weight:normal}
.msg{border:1px solid var(--border);border-radius:10px;padding:10px 12px;
margin:8px 0;font-size:13.5px;line-height:1.9;background:#fcfdfc}
.msg .meta{font-size:11.5px;color:var(--muted);margin-bottom:4px}
.msg .meta b{color:var(--ink)}
.msg .body{white-space:pre-wrap;word-wrap:break-word}
.empty{text-align:center;color:var(--muted);padding:30px;font-size:14px}
footer{text-align:center;color:var(--muted);font-size:12px;padding:8px 0 0}
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
    <div class="stat"><b>$ncats</b><span>تعداد دسته‌ها</span></div>
    <div class="stat"><b>$topcat</b><span>دسته با بیشترین پیام</span></div>
  </div>
  <div class="box">
    <h3>توزیع پیام‌ها بر اساس دسته</h3>
    $bars
  </div>
  <div class="filters">
    <button class="active" data-cat="all" onclick="flt('all')">همه</button>
    $filter_buttons
  </div>
  <div id="sections">
  $sections
  </div>
  <footer>تولیدشده با برنامه Bale Chat Mosharket — دریافت و دسته‌بندی پیام‌های گروه بله</footer>
</div>
<script>
function flt(c){
var b=document.querySelectorAll('.filters button');
for(var i=0;i<b.length;i++){b[i].classList.toggle('active',b[i].getAttribute('data-cat')===c);}
var s=document.querySelectorAll('section.cat');
for(var i=0;i<s.length;i++){s[i].style.display=(c==='all'||s[i].getAttribute('data-cat')===c)?'':'none';}
}
</script>
</body>
</html>
""")

SECTION = Template("""<section class="cat" data-cat="$attr">
<h2><span class="dot" style="background:$color"></span>$name
<span class="badge">$count پیام</span></h2>
$cards
</section>""")

CARD = Template("""<div class="msg">
<div class="meta"><b>$sender</b> — $when</div>
<div class="body">$text</div>
</div>""")


def _attr(s):
    """امن‌سازی برای استفاده داخل attributeهای HTML"""
    return html.escape(str(s or ""), quote=True)


def _body(s):
    """امن‌سازی متن پیام برای نمایش داخل صفحه"""
    return html.escape(str(s or ""), quote=False)


def _js_arg(s):
    """پاکسازی نام دسته برای استفاده در آرگومان onclick"""
    return str(s or "").replace("\\", "").replace("'", "").replace('"', "")


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


def build_report(messages, output_path, group_title=None):
    """ساخت فایل گزارش HTML و برگرداندن مسیر مطلق آن"""
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
    for m in msgs:
        p = m.get("sender_name") or m.get("username") or m.get("sender_id")
        if p:
            participants.add(str(p))

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
        filter_buttons = "\n".join(
            f'<button data-cat="{_attr(c)}" onclick="flt(\'{_js_arg(c)}\')">{_attr(c)}</button>'
            for c in cats
        )
        sections = []
        for c, n in counter.most_common():
            cards = "\n".join(
                CARD.substitute(
                    sender=_attr(
                        m.get("sender_name") or m.get("username") or "ناشناس"
                    ),
                    when=_attr(_when(m)),
                    text=_body(m.get("text") or "—"),
                )
                for m in msgs
                if (m.get("category") or "سایر") == c
            )
            sections.append(
                SECTION.substitute(
                    attr=_attr(c),
                    color=color_map[c],
                    name=_attr(c),
                    count=n,
                    cards=cards,
                )
            )
        sections_html = "\n".join(sections)
    else:
        bars = '<div class="empty">پیامی برای نمایش وجود ندارد.</div>'
        filter_buttons = ""
        sections_html = (
            '<div class="box empty">پیامی برای نمایش وجود ندارد؛ '
            "ابتدا از تب «دریافت پیام» شروع کنید یا فایل CSV پیام‌های قدیمی را وارد کنید.</div>"
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
        ncats=len(counter),
        topcat=_attr(topcat),
        bars=bars,
        filter_buttons=filter_buttons,
        sections=sections_html,
        range=_attr(rng),
    )

    directory = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(directory, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(out)
    return os.path.abspath(output_path)
