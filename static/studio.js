/* استودیوی گزارش عملکرد حوزه — نسخه ۵.۱
   فقط با پیام‌های واقعی ذخیره‌شده (messages.json) کار می‌کند؛ هیچ داده نمونه‌ای وجود ندارد. */
(function(){
"use strict";

/* ---------- ابزار ---------- */
function faNum(n){ return String(n).replace(/[0-9]/g, function(d){ return "۰۱۲۳۴۵۶۷۸۹".charAt(+d); }); }
function esc(s){
  return String(s == null ? "" : s).replace(/&/g,"&amp;").replace(/</g,"&lt;")
                  .replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}
function toast(msg, kind){
  var t = document.getElementById("toast");
  t.textContent = msg;
  t.className = "toast show" + (kind ? " " + kind : "");
  if (t._t) clearTimeout(t._t);
  t._t = setTimeout(function(){ t.className = "toast"; }, 3200);
}
function setStatus(msg, err){
  var s = document.getElementById("statusLine");
  s.textContent = msg || "";
  s.classList.toggle("err", !!err);
}
function api(url, body){
  return fetch(url, {
    method: body ? "POST" : "GET",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined
  }).then(function(r){ return r.json(); });
}
function trunc(s, n){
  s = String(s || "").trim();
  return s.length > n ? (s.slice(0, n) + "…") : s;
}

/* ---------- عناصر ---------- */
var el = function(id){ return document.getElementById(id); };
var msgList = el("msgList"), orderList = el("orderList");
var qEl = el("q"), catSel = el("catSel"), dateSel = el("dateSel"), chatSel = el("chatSel"), photoOnly = el("photoOnly");
var topicInput = el("topicInput"), titleInput = el("titleInput"), authorInput = el("authorInput"),
    groupInput = el("groupLabel"), introInput = el("introInput");
var LS_KEY = "bale_studio_config_v1";

var state = { msgs: [], byKey: {}, picked: [], shown: 200 };

/* ---------- ذخیره/بازیابی تنظیمات استودیو ---------- */
function saveConfig(){
  try {
    localStorage.setItem(LS_KEY, JSON.stringify({
      topic: topicInput.value, title: titleInput.value, author: authorInput.value,
      group: groupInput.value, intro: introInput.value,
      theme: currentTheme, fmt: currentFmt,
      pptxGroup: el("pptxGroupSel").value, htmlGroup: el("htmlGroupSel").value,
      inclPhotos: el("inclPhotos").checked
    }));
  } catch (e) {}
}
function loadConfig(){
  try {
    var raw = localStorage.getItem(LS_KEY);
    if (!raw) return;
    var c = JSON.parse(raw);
    if (c.topic) topicInput.value = c.topic;
    if (c.title) titleInput.value = c.title;
    if (c.author) authorInput.value = c.author;
    if (c.group) groupInput.value = c.group;
    if (c.intro) introInput.value = c.intro;
    if (c.theme) setTheme(c.theme);
    if (c.fmt) setFmt(c.fmt);
    if (c.pptxGroup) el("pptxGroupSel").value = c.pptxGroup;
    if (c.htmlGroup) el("htmlGroupSel").value = c.htmlGroup;
    if (typeof c.inclPhotos === "boolean") el("inclPhotos").checked = c.inclPhotos;
  } catch (e) {}
}

/* ---------- بارگذاری پیام‌ها (فقط داده واقعی) ---------- */
function loadMessages(){
  return api("/api/studio/messages").then(function(res){
    if (!res.ok) throw new Error(res.error || "خطا در خواندن پیام‌ها");
    state.msgs = res.messages || [];
    state.byKey = {};
    for (var i = 0; i < state.msgs.length; i++){
      state.byKey[state.msgs[i].key] = state.msgs[i];
    }
    el("totalChip").textContent = faNum(state.msgs.length);
    if (!state.msgs.length){
      el("emptyState").classList.remove("hidden");
      el("mainWrap").classList.add("hidden");
      return;
    }
    fillOptions();
    renderList();
    renderOrder();
  });
}

function fillOptions(){
  var cats = {}, dates = {}, chats = {};
  for (var i = 0; i < state.msgs.length; i++){
    var m = state.msgs[i];
    if (m.category) cats[m.category] = (cats[m.category] || 0) + 1;
    if (m.date_text) dates[m.date_text] = (dates[m.date_text] || 0) + 1;
    if (m.chat_title) chats[m.chat_title] = (chats[m.chat_title] || 0) + 1;
  }
  function fill(sel, map, prefix){
    var keys = Object.keys(map).sort(function(a,b){ return map[b] - map[a]; });
    var html = '<option value="">' + prefix + '</option>';
    for (var j = 0; j < keys.length; j++){
      html += '<option value="' + esc(keys[j]) + '">' + esc(keys[j]) +
              " (" + faNum(map[keys[j]]) + ")</option>";
    }
    sel.innerHTML = html;
  }
  fill(catSel, cats, "همه موضوعات");
  fill(dateSel, dates, "همه تاریخ‌ها (شمسی)");
  fill(chatSel, chats, "همه گفتگوها");
  /* پیشنهاد موضوع گزارش از موضوعات واقعی موجود */
  var dl = el("topicList");
  var top = Object.keys(cats).sort(function(a,b){ return cats[b] - cats[a]; });
  var dlHtml = "";
  for (var k = 0; k < top.length; k++) dlHtml += '<option value="' + esc(top[k]) + '"></option>';
  dl.innerHTML = dlHtml;
}

/* ---------- فیلتر ---------- */
function filtered(){
  var out = [];
  var t = qEl.value.trim().toLowerCase();
  var c = catSel.value, d = dateSel.value, ch = chatSel.value;
  for (var i = 0; i < state.msgs.length; i++){
    var m = state.msgs[i];
    if (c && m.category !== c) continue;
    if (d && m.date_text !== d) continue;
    if (ch && m.chat_title !== ch) continue;
    if (photoOnly.checked && !m.has_photo) continue;
    if (t && (m.search || "").indexOf(t) === -1) continue;
    out.push(m);
  }
  return out;
}

function renderList(){
  var list = filtered();
  var shown = list.slice(0, state.shown);
  var html = "";
  for (var i = 0; i < shown.length; i++){
    var m = shown[i];
    var pos = state.picked.indexOf(m.key);
    var tags = '<span class="tag cat">' + esc(m.category || "سایر") + '</span>';
    if (m.has_photo) tags += '<span class="tag photo">عکس</span>';
    if (m.media_count > 1) tags += '<span class="tag">' + faNum(m.media_count) + ' رسانه</span>';
    if (m.is_reply) tags += '<span class="tag rel">پاسخ/کامنت</span>';
    html += '<div class="mrow' + (pos > -1 ? " picked" : "") + '" data-key="' + esc(m.key) + '">' +
      '<input type="checkbox" class="pick-box"' + (pos > -1 ? " checked" : "") + '>' +
      '<div class="m-main">' +
        '<div class="m-meta"><b>' + esc(m.sender || "ناشناس") + '</b>' +
        '<span>' + esc(m.date_text || "") + (m.hour_text ? " — " + esc(m.hour_text) : "") + '</span>' +
        (pos > -1 ? '<span class="tag" style="background:#0e9f6e;color:#fff">در چیدمان: ' + faNum(pos + 1) + '</span>' : "") +
        tags + '</div>' +
        '<div class="m-txt">' + esc(trunc(m.text || m.caption || (m.has_photo ? "[عکس]" : ""), 220)) + '</div>' +
      '</div></div>';
  }
  msgList.innerHTML = html || '<div class="empty-row">پیامی با این فیلترها پیدا نشد</div>';
  el("visInfo").textContent = "نمایش " + faNum(shown.length) + " از " + faNum(list.length) + " پیام فیلترشده (کل: " + faNum(state.msgs.length) + ")";
  el("btnMore").classList.toggle("hidden", list.length <= state.shown);
}

/* ---------- انتخاب و چیدمان ---------- */
function togglePick(key){
  var pos = state.picked.indexOf(key);
  if (pos > -1) state.picked.splice(pos, 1);
  else state.picked.push(key);
  renderList();
  renderOrder();
}
msgList.addEventListener("click", function(ev){
  var row = ev.target.closest(".mrow");
  if (!row) return;
  togglePick(row.getAttribute("data-key"));
});
msgList.addEventListener("change", function(ev){
  if (ev.target.classList.contains("pick-box")){
    var row = ev.target.closest(".mrow");
    if (row) togglePick(row.getAttribute("data-key"));
  }
});
el("btnPickShown").addEventListener("click", function(){
  var vis = filtered();
  for (var i = 0; i < vis.length; i++){
    if (state.picked.indexOf(vis[i].key) === -1) state.picked.push(vis[i].key);
  }
  renderList(); renderOrder();
  toast(faNum(vis.length) + " پیام نمایش‌داده‌شده به چیدمان اضافه شد");
});
el("btnPickNone").addEventListener("click", function(){
  var vis = filtered();
  var visKeys = {};
  for (var i = 0; i < vis.length; i++) visKeys[vis[i].key] = 1;
  state.picked = state.picked.filter(function(k){ return !visKeys[k]; });
  renderList(); renderOrder();
});
el("btnMore").addEventListener("click", function(){
  state.shown += 200;
  renderList();
});

qEl.addEventListener("input", function(){ state.shown = 200; renderList(); });
catSel.addEventListener("change", function(){ state.shown = 200; renderList(); });
dateSel.addEventListener("change", function(){ state.shown = 200; renderList(); });
chatSel.addEventListener("change", function(){ state.shown = 200; renderList(); });
photoOnly.addEventListener("change", function(){ state.shown = 200; renderList(); });

/* ---------- رندر چیدمان + کشیدن و رها کردن ---------- */
function renderOrder(){
  el("orderChip").textContent = faNum(state.picked.length) + " پیام در چیدمان";
  el("pickCountChip").textContent = faNum(state.picked.length) + " انتخاب شده";
  if (!state.picked.length){
    orderList.innerHTML = '<div class="empty-row">هنوز پیامی انتخاب نشده — از بخش بالا پیام‌ها را انتخاب کنید</div>';
    return;
  }
  var html = "";
  for (var i = 0; i < state.picked.length; i++){
    var m = state.byKey[state.picked[i]];
    if (!m) continue;
    html += '<div class="orow" draggable="true" data-idx="' + i + '" data-key="' + esc(m.key) + '">' +
      '<span class="num">' + faNum(i + 1) + '</span>' +
      '<span class="grab" title="کشیدن برای تغییر ترتیب">⠿</span>' +
      '<div class="o-main">' +
        '<div class="o-meta"><b>' + esc(m.sender || "ناشناس") + '</b> — ' + esc(m.date_text || "") +
        (m.hour_text ? " — " + esc(m.hour_text) : "") + ' — ' + esc(m.category || "سایر") + '</div>' +
        '<div class="o-txt">' + esc(trunc(m.text || m.caption || (m.has_photo ? "[عکس]" : ""), 160)) + '</div>' +
      '</div>' +
      '<button type="button" class="obtn" data-act="up" title="یک پله بالاتر">↑</button>' +
      '<button type="button" class="obtn" data-act="down" title="یک پله پایین‌تر">↓</button>' +
      '<button type="button" class="obtn del" data-act="remove" title="برداشتن از چیدمان">✕</button>' +
    '</div>';
  }
  orderList.innerHTML = html;
}
orderList.addEventListener("click", function(ev){
  var btn = ev.target.closest(".obtn");
  if (!btn) return;
  var row = btn.closest(".orow");
  var idx = +row.getAttribute("data-idx");
  var act = btn.getAttribute("data-act");
  if (act === "up" && idx > 0){
    state.picked.splice(idx - 1, 0, state.picked.splice(idx, 1)[0]);
  } else if (act === "down" && idx < state.picked.length - 1){
    state.picked.splice(idx + 1, 0, state.picked.splice(idx, 1)[0]);
  } else if (act === "remove"){
    state.picked.splice(idx, 1);
    renderList();
  }
  renderOrder();
});

/* کشیدن و رها کردن روی ردیف‌های چیدمان */
var dragIdx = -1;
orderList.addEventListener("dragstart", function(ev){
  var row = ev.target.closest(".orow");
  if (!row) return;
  dragIdx = +row.getAttribute("data-idx");
  row.classList.add("dragging");
  try { ev.dataTransfer.setData("text/plain", String(dragIdx)); } catch (e) {}
});
orderList.addEventListener("dragend", function(ev){
  var row = ev.target.closest(".orow");
  if (row) row.classList.remove("dragging");
  var overs = orderList.querySelectorAll(".dragover");
  for (var i = 0; i < overs.length; i++) overs[i].classList.remove("dragover");
});
orderList.addEventListener("dragover", function(ev){
  ev.preventDefault();
  var row = ev.target.closest(".orow");
  if (!row) return;
  var overs = orderList.querySelectorAll(".dragover");
  for (var i = 0; i < overs.length; i++) overs[i].classList.remove("dragover");
  row.classList.add("dragover");
});
orderList.addEventListener("drop", function(ev){
  ev.preventDefault();
  var row = ev.target.closest(".orow");
  if (!row || dragIdx < 0) return;
  var to = +row.getAttribute("data-idx");
  if (to === dragIdx) return;
  var moved = state.picked.splice(dragIdx, 1)[0];
  state.picked.splice(to, 0, moved);
  dragIdx = -1;
  renderOrder();
});

/* ---------- مرتب‌سازی خودکار ---------- */
function sortBy(fn){
  state.picked.sort(function(a, b){
    return fn(state.byKey[a] || {}, state.byKey[b] || {});
  });
  renderOrder();
}
el("autoNewest").addEventListener("click", function(){
  sortBy(function(a,b){ return (b.date || 0) - (a.date || 0); });
  toast("چیدمان بر اساس جدیدترین پیام مرتب شد");
});
el("autoOldest").addEventListener("click", function(){
  sortBy(function(a,b){ return (a.date || 0) - (b.date || 0); });
  toast("چیدمان بر اساس قدیمی‌ترین پیام مرتب شد");
});
el("autoCat").addEventListener("click", function(){
  sortBy(function(a,b){
    var ca = a.category || "سایر", cb = b.category || "سایر";
    if (ca !== cb) return ca.localeCompare(cb, "fa");
    return (a.date || 0) - (b.date || 0);
  });
  toast("چیدمان به تفکیک موضوع مرتب شد");
});
el("autoSender").addEventListener("click", function(){
  sortBy(function(a,b){
    var sa = a.sender || "", sb = b.sender || "";
    if (sa !== sb) return sa.localeCompare(sb, "fa");
    return (a.date || 0) - (b.date || 0);
  });
  toast("چیدمان به تفکیک فرستنده مرتب شد");
});
el("autoReverse").addEventListener("click", function(){
  state.picked.reverse();
  renderOrder();
});
el("btnClearOrder").addEventListener("click", function(){
  state.picked = [];
  renderList(); renderOrder();
});
el("btnDeleteFromDb").addEventListener("click", function(){
  if (!state.picked.length) return;
  if (!confirm("حذف " + faNum(state.picked.length) + " پیام انتخاب‌شده از پایگاه داده برنامه؟ این عمل قابل بازگشت نیست؛ پیام‌ها از همه خروجی‌های بعدی حذف می‌شوند.")) return;
  var keys = state.picked.slice();
  api("/api/messages/delete", { ids: keys }).then(function(res){
    if (res.ok){
      toast(faNum(res.removed) + " پیام از پایگاه داده حذف شد", "warn");
      state.picked = [];
      return loadMessages();
    }
    toast(res.error || "حذف ناموفق بود", "err");
  });
});

/* ---------- مشخصات گزارش ---------- */
var lastAutoTitle = "";
topicInput.addEventListener("input", function(){
  var t = topicInput.value.trim();
  if (!t) return;
  /* عنوان فقط وقتی خودکار پر می‌شود که کاربر دستی تغییرش نداده باشد */
  if (!titleInput.value.trim() || titleInput.value === lastAutoTitle){
    lastAutoTitle = "گزارش عملکرد حوزه " + t;
    titleInput.value = lastAutoTitle;
  }
});
[topicInput, titleInput, authorInput, groupInput, introInput].forEach(function(inp){
  inp.addEventListener("change", saveConfig);
  inp.addEventListener("blur", saveConfig);
});

/* ---------- تم و فرمت ---------- */
var currentTheme = "green", currentFmt = "16:9";
function setTheme(t){
  currentTheme = t;
  var btns = el("themePick").querySelectorAll(".theme");
  for (var i = 0; i < btns.length; i++){
    btns[i].classList.toggle("active", btns[i].getAttribute("data-theme") === t);
  }
}
function setFmt(f){
  currentFmt = f;
  var btns = el("fmtPick").querySelectorAll(".fmt");
  for (var i = 0; i < btns.length; i++){
    btns[i].classList.toggle("active", btns[i].getAttribute("data-fmt") === f);
  }
}
el("themePick").addEventListener("click", function(ev){
  var b = ev.target.closest(".theme");
  if (!b) return;
  setTheme(b.getAttribute("data-theme"));
  saveConfig();
});
el("fmtPick").addEventListener("click", function(ev){
  var b = ev.target.closest(".fmt");
  if (!b) return;
  setFmt(b.getAttribute("data-fmt"));
  saveConfig();
});
el("pptxGroupSel").addEventListener("change", saveConfig);
el("htmlGroupSel").addEventListener("change", saveConfig);
el("inclPhotos").addEventListener("change", saveConfig);

/* ---------- گرفتن خروجی ---------- */
function buildPayload(){
  return {
    keys: state.picked.slice(),
    topic: topicInput.value.trim(),
    title: titleInput.value.trim(),
    author: authorInput.value.trim(),
    group: groupInput.value.trim(),
    intro: introInput.value.trim(),
    theme: currentTheme,
    fmt: currentFmt,
    pptx_group: el("pptxGroupSel").value,
    html_group: el("htmlGroupSel").value,
    images: el("inclPhotos").checked
  };
}
function validate(){
  if (!state.msgs.length){ setStatus("هیچ پیامی ذخیره نشده است — اول از داشبورد پیام‌ها را بگیرید", true); return false; }
  if (!state.picked.length){ setStatus("هیچ پیامی انتخاب نشده — از بخش ۱ پیام‌ها را انتخاب کنید", true); return false; }
  return true;
}
el("btnBuildHtml").addEventListener("click", function(){
  if (!validate()) return;
  setStatus("در حال ساخت گزارش HTML ...");
  api("/api/studio/build", buildPayload()).then(function(res){
    if (!res.ok){ setStatus(res.error || "ساخت گزارش ناموفق بود", true); return; }
    setStatus("گزارش «" + res.name + "» با " + faNum(res.count) + " پیام ساخته شد — در تب جدید باز شد");
    window.open(res.url, "_blank");
    refreshExports();
  }).catch(function(e){ setStatus("خطا: " + e.message, true); });
});
el("btnBuildPptx").addEventListener("click", function(){
  if (!validate()) return;
  setStatus("در حال آماده‌سازی پاورپوینت ... (در تب جدید ساخته و دانلود می‌شود)");
  api("/api/studio/build", buildPayload()).then(function(res){
    if (!res.ok){ setStatus(res.error || "ساخت گزارش ناموفق بود", true); return; }
    setStatus("پاورپوینت با تم «" + currentTheme + "» و فرمت " + currentFmt + " در تب جدید در حال ساخت است");
    window.open(res.url + "?autopptx=1", "_blank");
    refreshExports();
  }).catch(function(e){ setStatus("خطا: " + e.message, true); });
});

/* ---------- فهرست خروجی‌های اخیر ---------- */
function refreshExports(){
  api("/api/state").then(function(s){
    if (!s.ok && !s.exports) return;
    var exps = (s.exports || []).slice(0, 6);
    var box = el("studioExports");
    if (!exps.length){ box.innerHTML = ""; return; }
    var html = '<div class="hint" style="margin-top:8px">خروجی‌های اخیر:</div>';
    for (var i = 0; i < exps.length; i++){
      var e = exps[i];
      html += '<div class="exp-row">' +
        '<a href="' + esc(e.url) + '" target="_blank">' + esc(e.name) + '</a>' +
        '<span class="meta">' + faNum(e.count) + ' پیام — ' + esc(e.when || "") + '</span></div>';
    }
    box.innerHTML = html;
  }).catch(function(){});
}

/* ---------- نسخه ---------- */
api("/api/state").then(function(s){
  if (s && s.version){
    el("verChip").textContent = "نسخه " + s.version;
    el("verFooter").textContent = "نسخه " + s.version;
  }
}).catch(function(){});

/* ---------- اجرا ---------- */
loadConfig();
loadMessages().then(refreshExports);
})();
