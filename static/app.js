// Bale Chat Mosharket — منطق داشبورد (نسخه وب)
"use strict";

const $ = (id) => document.getElementById(id);
const RING_LEN = 326.7;

const PALETTE = ["#0e9f6e", "#2563eb", "#d97706", "#dc2626", "#7c3aed",
  "#0d9488", "#db2777", "#475569", "#9333ea", "#0891b2"];

const fa = (n) => String(n).replace(/\d/g, (d) => "۰۱۲۳۴۵۶۷۸۹"[d]);

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

async function api(path, body) {
  const opts = body
    ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
    : {};
  const resp = await fetch(path, opts);
  const data = await resp.json().catch(() => ({ ok: false, error: "پاسخ نامعتبر سرور" }));
  if (!resp.ok || data.ok === false) {
    const err = new Error(data.error || "خطای ناشناخته");
    err.data = data;
    throw err;
  }
  return data;
}

function toast(text, kind = "err") {
  const t = $("toast");
  t.textContent = text;
  t.className = "toast " + kind;
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.add("hidden"), 4200);
}

const guard = (fn) => async (...args) => {
  try { return await fn(...args); }
  catch (e) { toast(e.message || String(e), "err"); }
};

/* ---------- رندر وضعیت ---------- */

let lastLogCount = 0;
let lastRecentCount = 0;

function renderBot(s) {
  const connected = s.connected;
  $("botDot").className = "dot " + (connected ? "on" : "off");
  $("botChipText").textContent = connected
    ? `ربات متصل: ${s.bot.name} (@${s.bot.username})`
    : "ربات متصل نشده";
}

function renderProgress(p) {
  $("ringFg").style.strokeDashoffset = RING_LEN * (1 - p.percent / 100);
  $("ringPct").textContent = fa(p.percent) + "%";
  $("overallChip").textContent = fa(p.percent) + "٪";

  $("steps").innerHTML = p.steps.map((st) => `
    <div class="step ${st.done ? "done" : ""}">
      <span class="ic">${st.done ? "✓" : ""}</span>
      <span class="nm">${esc(st.name)}${st.note ? ` <span class="note">— ${esc(st.note)}</span>` : ""}</span>
      <span class="wt">${fa(st.weight)}٪</span>
    </div>`).join("");

  $("readingBar").style.width = p.reading_percent + "%";
  $("readingPct").textContent = fa(p.reading_percent) + "%";
  $("readingNote").textContent = `${fa(p.read)} پیام از هدف ${fa(p.target)}`;
}

function renderGroups(chat) {
  $("selectedChat").textContent = chat
    ? `گروه انتخاب‌شده: ${chat.title} (شناسه: ${fa(String(chat.id).replace(/\d/g, (d) => "۰۱۲۳۴۵۶۷۸۹"[d]))})`
    : "هیچ گروهی انتخاب نشده — همه گروه‌ها ذخیره می‌شوند";
}

function renderStats(st) {
  $("stTotal").textContent = fa(st.total);
  $("stSession").textContent = fa(st.session);
  $("stPeople").textContent = fa(st.participants);
  $("stPhotos").textContent = fa(st.photos || 0);
  $("stMedia").textContent = fa(st.media || 0);
  $("stFwd").textContent = fa(st.forwards || 0);
  $("stRaw").textContent = fa(st.raw || 0);
  $("stCats").textContent = fa(Object.keys(st.categories).length);

  const cats = Object.entries(st.categories);
  $("cats").innerHTML = cats.map(([name, count], i) => `
    <span class="cat-chip">
      <span class="d" style="background:${PALETTE[i % PALETTE.length]}"></span>
      ${esc(name)} <b>${fa(count)}</b>
    </span>`).join("") || `<span class="mini-hint">هنوز پیامی خوانده نشده</span>`;
}

function renderRecent(list) {
  $("recent").innerHTML = list.map((m) => `
    <div class="rmsg">
      <div class="top">
        <b>${esc(m.sender)}</b>
        <span class="badge">${esc(m.category)}</span>
        ${m.media ? `<span class="badge m">${fa(m.media)} رسانه</span>` : ""}
        <span class="w">${esc(m.when)}</span>
      </div>
      <div class="tx">${esc(m.text)}</div>
    </div>`).join("") || `<div class="empty-row">هنوز پیامی نیست</div>`;
}

function renderExports(list) {
  const box = $("exportList");
  const chip = $("exportCountChip");
  if (chip) chip.textContent = fa(list.length) + " خروجی";
  if (!list.length) {
    box.innerHTML = `<div class="empty-row">هنوز خروجی جداگانه‌ای گرفته نشده — هر بار با دکمه بالا یک فایل HTML جدید با تاریخ و ساعت ساخته می‌شود</div>`;
    return;
  }
  box.innerHTML = list.map((e) => `
    <div class="export-item">
      <div class="e-info">
        <b>${esc(e.name)}</b>
        <span>${esc(e.when || "")} · ${fa(e.count)} پیام · ${fmtSize(e.size)}${e.title ? " · " + esc(e.title) : ""}</span>
      </div>
      <div class="e-actions">
        <a class="mini-btn view" href="${esc(e.url)}?ts=${e.time || 0}" target="_blank">مشاهده</a>
        <button class="mini-btn del" data-name="${esc(e.name)}">حذف</button>
      </div>
    </div>`).join("");
  box.querySelectorAll(".mini-btn.del").forEach((b) => {
    b.onclick = guard(async () => {
      if (!confirm(`فایل خروجی «${b.dataset.name}» حذف شود؟ این کار فقط فایل خروجی را پاک می‌کند و پیام‌های ذخیره‌شده دست‌نخورده می‌مانند.`)) return;
      await api("/api/exports/delete", { name: b.dataset.name });
      toast("خروجی حذف شد", "ok");
      refresh();
    });
  });
}

function fmtSize(n) {
  n = parseInt(n, 10);
  if (!n || isNaN(n)) return "—";
  if (n >= 1048576) return fa((n / 1048576).toFixed(1)) + " MB";
  if (n >= 1024) return fa(Math.round(n / 1024)) + " KB";
  return fa(n) + " B";
}

function renderLog(logs, running, draining, phase) {
  const box = $("log");
  box.innerHTML = logs.map((l) => `
    <div class="ln ${esc(l.kind)}">
      <span class="t">${esc(l.t)}</span>
      <span class="x">${esc(l.text)}</span>
    </div>`).join("") || `<div class="ln info"><span class="x">آماده دریافت پیام‌ها...</span></div>`;
  box.scrollTop = box.scrollHeight;

  const chip = $("liveChip");
  chip.classList.remove("backlog");
  if (phase === "backlog") {
    chip.textContent = "در حال خواندن پیام‌های قبلی...";
    chip.classList.add("backlog");
  } else {
    chip.textContent = draining ? "در حال خواندن همه پیام‌ها" : "دریافت زنده فعال";
  }
  chip.classList.toggle("hidden", !running);
  $("btnStart").disabled = running;
  $("btnReadAll").disabled = running;
  $("btnStop").disabled = !running;
}

let refreshCount = 0;

async function refresh() {
  try {
    const s = await fetch("/api/state").then((r) => r.json());
    renderBot(s);
    // بنر هشدار «صف سرور بله خالی است» (نسخه ۴.۵)
    if ($("queueBanner")) {
      $("queueBanner").classList.toggle("hidden", !s.queue_hint);
    }
    // محل ذخیره داده‌ها در بخش «درباره» (نسخه ۴.۵)
    if (s.data_info && $("msgPath")) {
      $("msgPath").innerHTML =
        "محل ذخیره داده‌ها: " + esc(s.data_info.messages) +
        "<br>آرشیو خام: " + esc(s.data_info.raw) +
        "<br>پوشه گزارش: " + esc(s.data_info.output);
    }
    if (s.version) {
      $("verChip").textContent = "نسخه " + fa(s.version);
      $("verFooter").textContent = "نسخه وب " + fa(s.version);
    }
    renderProgress(s.progress);
    renderGroups(s.chat);
    renderStats(s.stats);
    renderRecent(s.recent);
    renderLog(s.log, s.running, s.draining, s.phase);
    if (s.draining) {
      $("readingNote").textContent = `${fa(s.progress.read)} پیام خوانده شد — در حال خواندن همه پیام‌های بات ...`;
    }
    // فهرست گروه‌ها هر ۱۵ ثانیه خودکار به‌روز می‌شود (با رسیدن اولین پیام گروه، گروه ظاهر می‌شود)
    refreshCount += 1;
    if (refreshCount % 15 === 1 && s.connected) {
      fetch("/api/groups", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" })
        .then((r) => r.json())
        .then((g) => { if (g.ok) renderGroupList(g.groups); })
        .catch(() => {});
    }
    if (s.rules && document.activeElement !== $("rulesInput") && !$("rulesInput").value) {
      $("rulesInput").value = s.rules;
    }
    if (s.report_ready && s.report_url) {
      $("btnOpen").classList.remove("hidden");
      $("btnOpen").href = s.report_url;
    } else {
      $("btnOpen").classList.add("hidden");
    }
    renderExports(s.exports || []);
    if (s.error) {
      toast(s.error, "err");
      await fetch("/api/clear_error", { method: "POST" }).catch(() => {});
    }
  } catch (e) { /* سرور موقتاً در دسترس نیست */ }
}

/* ---------- اکشن‌ها ---------- */

$("btnConnect").onclick = guard(async () => {
  const token = $("tokenInput").value.trim();
  if (!token) return toast("توکن ربات را وارد کنید", "err");
  const r = await api("/api/connect", { token });
  toast(`اتصال موفق: ${r.bot.name} (@${r.bot.username})`, "ok");
  refresh();
});

$("btnGroups").onclick = guard(async () => {
  const r = await api("/api/groups", {});
  renderGroupList(r.groups);
});

function renderGroupList(groups) {
  const box = $("groupList");
  if (!groups.length) {
    box.innerHTML = `<div class="empty-row">گفتگویی پیدا نشد؛ ربات را به گروه اضافه کنید یا در گروه یک پیام بفرستید و دوباره تلاش کنید</div>`;
    return;
  }
  box.innerHTML = groups.map((g) => `
    <div class="group-item" data-id="${esc(g.id)}" data-title="${esc(g.title)}">
      <span class="ttl">${esc(g.title)}</span>
      <span class="tp">${esc(g.type_label || g.type)} · ${fa(g.count)} پیام</span>
      <button>انتخاب</button>
    </div>`).join("");
  box.querySelectorAll("button").forEach((b) => {
    b.onclick = guard(async () => {
      const item = b.closest(".group-item");
      await api("/api/group/select", {
        id: item.dataset.id,
        title: item.dataset.title,
      });
      box.querySelectorAll(".group-item").forEach((x) => x.classList.remove("sel"));
      item.classList.add("sel");
      toast("گروه انتخاب شد", "ok");
      refresh();
    });
  });
}

$("btnAllGroups").onclick = guard(async () => {
  await api("/api/group/select", { id: "all" });
  toast("حالت «همه گفتگوها» فعال شد", "ok");
  refresh();
});

$("btnAddGroup").onclick = guard(async () => {
  const link = $("groupLink").value.trim();
  if (!link) return toast("لینک یا شناسه گروه را وارد کنید", "err");
  const help = $("groupHelp");
  try {
    const r = await api("/api/group/add", { link });
    help.classList.add("hidden");
    toast(`گفتگو «${r.chat.title}» (${r.chat.type_label}) انتخاب شد`, "ok");
    $("groupLink").value = "";
  } catch (e) {
    // خطای نرم با راهنمای گام‌به‌گام (عضویت با لینک برای ربات ممکن نیست)
    const data = e.data || {};
    if (data.need_manual && data.steps) {
      help.innerHTML = `<b>${esc(data.error)}</b><ol>${data.steps.map((s) => `<li>${esc(s)}</li>`).join("")}</ol>`;
      help.classList.remove("hidden");
      toast("ربات نمی‌تواند با لینک وارد گروه شود — راهنما نمایش داده شد", "err");
    } else {
      toast(e.message || "افزودن گروه ناموفق بود", "err");
    }
  }
  refresh();
});

$("btnRules").onclick = guard(async () => {
  const r = await api("/api/rules", { rules: $("rulesInput").value });
  toast(`${fa(r.count)} دسته فعال شد و بر پیام‌های ذخیره‌شده اعمال گردید`, "ok");
  refresh();
});

$("btnStart").onclick = guard(async () => {
  await api("/api/start", {});
  toast("دریافت زنده پیام‌ها آغاز شد", "ok");
  refresh();
});

$("btnReadAll").onclick = guard(async () => {
  await api("/api/read_all", {});
  toast("همگام‌سازی آغاز شد؛ همه پیام‌های موجود خوانده می‌شوند و در پایان گزارش خودکار ساخته می‌شود", "ok");
  refresh();
});

$("btnStop").onclick = guard(async () => {
  await api("/api/stop", {});
  toast("دستور توقف صادر شد", "ok");
  refresh();
});

$("targetInput").onchange = guard(async () => {
  const r = await api("/api/target", { target: parseInt($("targetInput").value, 10) || 50 });
  $("targetInput").value = r.target;
  refresh();
});

$("btnExport").onclick = guard(async () => {
  const r = await api("/api/export", {});
  toast(`خروجی جداگانه ساخته شد: ${r.name} (${fa(r.count)} پیام)`, "ok");
  window.open(r.url, "_blank");
  refresh();
});

$("btnReset").onclick = guard(async () => {
  const clearRaw = $("optClearRaw").checked;
  const clearReports = $("optClearReports").checked;
  const skipServer = $("optSkipServer").checked;
  const resync = $("optResync").checked;
  const parts = ["همه پیام‌های ذخیره‌شده پاک شود؟"];
  if (clearRaw) parts.push("آرشیو خام و عکس‌ها هم حذف می‌شوند");
  if (clearReports) parts.push("همه فایل‌های خروجی قبلی هم حذف می‌شوند");
  if (skipServer) parts.push("پیام‌های موجود در صف سرور بله برای همیشه رد می‌شوند و دیگر خوانده نمی‌شوند");
  if (resync) parts.push("بعد از پاک‌سازی، دوباره از بات همگام‌سازی می‌شود");
  if (!confirm(parts.join("\n"))) return;
  const r = await api("/api/reset", {
    clear_raw: clearRaw,
    clear_reports: clearReports,
    skip_server: skipServer,
    resync: resync,
  });
  toast(
    clearReports
      ? `پاک‌سازی کامل شد (${fa(r.removed_reports)} فایل خروجی هم حذف شد)`
      : "پاک‌سازی کامل شد — دور جدید آماده است",
    "ok"
  );
  refresh();
});

$("btnDemo").onclick = guard(async () => {
  const r = await api("/api/demo", { count: 10 });
  toast(`${fa(r.added)} پیام نمونه اضافه شد`, "ok");
  refresh();
});

$("btnImport").onclick = () => $("importFile").click();

$("btnRecover").onclick = guard(async () => {
  const r = await api("/api/recover_raw", {});
  toast(
    r.recovered
      ? `${fa(r.recovered)} پیام از آرشیو خام بازیابی شد`
      : "چیزی برای بازیابی در آرشیو خام نبود",
    "ok"
  );
  refresh();
});

$("btnBackup").onclick = () => window.open("/api/backup", "_blank");

$("importFile").onchange = guard(async () => {
  const f = $("importFile").files[0];
  if (!f) return;
  const fd = new FormData();
  fd.append("file", f);
  const resp = await fetch("/api/import", { method: "POST", body: fd });
  const data = await resp.json().catch(() => ({ ok: false, error: "پاسخ نامعتبر" }));
  if (!resp.ok || data.ok === false) throw new Error(data.error || "ورود فایل ناموفق بود");
  toast(`${fa(data.added)} پیام از فایل «${f.name}» وارد شد`, "ok");
  $("importFile").value = "";
  refresh();
});

/* ---------- شروع ---------- */

fetch("/api/state").then((r) => r.json()).then((s) => {
  if (s.rules) $("rulesInput").value = s.rules;
  $("targetInput").value = s.target || 50;
}).catch(() => {});

setInterval(refresh, 1000);
refresh();
