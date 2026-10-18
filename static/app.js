const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

const STEPS = [
  ["read", "Read the letter", "Pulls out insurer, codes, reason, dates and policy cited"],
  ["triage", "Understand the denial", "Classifies the denial and plans what evidence to look for"],
  ["research", "Find the evidence", "Searches insurer policies, clinical guidelines and appeal rules"],
  ["strategy", "Build the argument", "Reasons over the evidence to find the strongest honest case"],
  ["draft", "Write the appeal", "Drafts your letter and a template for your doctor"],
  ["verify", "Check every citation", "Confirms each cited claim is supported by its source"],
];
const shortModel = (m) => (m || "").split("/").pop();

let files = [];
let state = {};

// ---------- mode ----------
fetch("/api/health").then((r) => r.json()).then((h) => {
  const el = $("#mode");
  el.textContent = h.demo ? "Sample mode" : "Live · Nebius Token Factory";
  el.classList.toggle("live", !h.demo);
}).catch(() => ($("#mode").textContent = "offline"));

// ---------- intake ----------
const drop = $("#drop");
const setFiles = (list) => {
  files = [...list].slice(0, 4);
  $("#filelist").textContent = files.map((f) => f.name).join(" · ");
};
$("#file").addEventListener("change", (e) => setFiles(e.target.files));
["dragenter", "dragover"].forEach((t) => drop.addEventListener(t, (e) => { e.preventDefault(); drop.classList.add("over"); }));
["dragleave", "drop"].forEach((t) => drop.addEventListener(t, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
drop.addEventListener("drop", (e) => setFiles(e.dataTransfer.files));

$("#sample").addEventListener("click", async () => {
  const blob = await fetch("/sample-letter.png").then((r) => r.blob());
  setFiles([new File([blob], "sample_denial.png", { type: "image/png" })]);
  $("#notes").value = "I did 7 weeks of supervised physical therapy (Aug 4 – Sep 22) plus ibuprofen and it didn't help. Over the last two weeks my left foot has gotten weaker and I trip on stairs. Dr. Okafor wants the MRI to decide on an injection or surgery.";
});

$("#form").addEventListener("submit", (e) => { e.preventDefault(); start(); });
$("#restart").addEventListener("click", () => location.reload());

// ---------- run ----------
function renderSteps() {
  $("#steps").innerHTML = STEPS.map(([id, title, sub], i) => `
    <li class="step" id="step-${id}">
      <span class="dot">${i + 1}</span>
      <div><h4>${title}</h4><p data-sub>${sub}</p><div class="mini" data-mini></div></div>
      <span class="chip" data-model></span>
    </li>`).join("");
}

function onStep(ev) {
  const li = $(`#step-${ev.id}`);
  if (!li) return;
  li.className = `step ${ev.status}`;
  li.querySelector("[data-model]").textContent = ev.model === "Tavily" ? "Tavily search" : shortModel(ev.model);
  if (ev.status === "done") li.querySelector(".dot").textContent = "✓";
  const mini = li.querySelector("[data-mini]");
  const d = ev.data || {};
  if (ev.status === "running") $("#run-title").textContent = STEPS.find((s) => s[0] === ev.id)[1] + "…";
  if (ev.id === "read" && ev.status === "done")
    mini.innerHTML = [d.insurer, d.service, ...(d.codes || [])].filter(Boolean).map((x) => `<span>${esc(x)}</span>`).join("");
  if (ev.id === "triage" && ev.status === "done") mini.innerHTML = `<span>${esc(d.category_label)}</span>`;
  if (ev.id === "research" && d.queries && ev.status === "running")
    mini.innerHTML = d.queries.map((q) => `<span>${esc(q.q)}</span>`).join("");
  if (ev.id === "research" && ev.status === "done")
    li.querySelector("[data-sub]").textContent = `Found ${d.sources.length} sources`;
  if (ev.id === "strategy" && ev.status === "done")
    mini.innerHTML = (d.arguments || []).map((a) => `<span>${esc(a.title)}</span>`).join("");
  if (ev.id === "verify" && ev.status === "done")
    li.querySelector("[data-sub]").textContent = `${d.supported}/${d.checked} citations supported`;
}

async function start() {
  const fd = new FormData();
  files.forEach((f) => fd.append("files", f));
  fd.append("text", $("#text").value);
  fd.append("notes", $("#notes").value);
  if (!files.length && !$("#text").value.trim() && !$("#mode").textContent.startsWith("Sample")) {
    alert("Upload your denial letter, paste its text, or try the sample.");
    return;
  }
  $("#go").disabled = true;
  $("#intake").classList.add("hidden");
  $("#run").classList.remove("hidden");
  renderSteps();
  window.scrollTo({ top: 0 });

  const res = await fetch("/api/appeal", { method: "POST", body: fd });
  if (!res.ok) { fail((await res.json()).error || res.statusText); return; }
  const reader = res.body.getReader();
  const dec = new TextDecoder();
  let buf = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let i;
    while ((i = buf.indexOf("\n\n")) >= 0) {
      const chunk = buf.slice(0, i); buf = buf.slice(i + 2);
      if (!chunk.startsWith("data: ")) continue;
      const ev = JSON.parse(chunk.slice(6));
      if (ev.type === "step") onStep(ev);
      else if (ev.type === "result") showResult(ev);
      else if (ev.type === "error") fail(ev.message);
    }
  }
}

function fail(msg) {
  $("#run-title").textContent = "Something went wrong";
  $("#steps").insertAdjacentHTML("beforeend", `<li class="step running"><span class="dot">!</span><div><h4>Error</h4><p>${esc(msg)}</p></div></li>`);
}

// ---------- markdown (tiny, safe) ----------
function inline(s) {
  return esc(s)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^*])\*(?!\s)(.+?)\*(?!\*)/g, "$1<em>$2</em>")
    .replace(/\[(\d+)\]/g, '<a class="cite" href="#src-$1" data-src="$1">$1</a>')
    .replace(/\[([^\]\d][^\]]*)\]/g, '<span class="ph">[$1]</span>');
}
function md(text) {
  const out = []; let list = null;
  const close = () => { if (list) { out.push(`</${list}>`); list = null; } };
  for (const raw of (text || "").split("\n")) {
    const line = raw.trimEnd();
    let m;
    if (!line.trim()) { close(); continue; }
    if ((m = line.match(/^(#{1,3})\s+(.*)/))) { close(); out.push(`<h${m[1].length + 1}>${inline(m[2])}</h${m[1].length + 1}>`); continue; }
    if ((m = line.match(/^\s*[-*]\s+(.*)/))) { if (list !== "ul") { close(); out.push("<ul>"); list = "ul"; } out.push(`<li>${inline(m[1])}</li>`); continue; }
    if ((m = line.match(/^\s*\d+[.)]\s+(.*)/))) { if (list !== "ol") { close(); out.push("<ol>"); list = "ol"; } out.push(`<li>${inline(m[1])}</li>`); continue; }
    close(); out.push(`<p>${inline(line)}</p>`);
  }
  close();
  return out.join("");
}

// ---------- result ----------
function showResult(r) {
  state = r;
  $("#run").classList.add("hidden");
  $("#result").classList.remove("hidden");
  $("#demo-banner").classList.toggle("hidden", !r.demo);

  const dl = r.deadline;
  $("#days").textContent = dl.days_left;
  const fmt = (d) => new Date(d + "T12:00:00").toLocaleDateString(undefined, { weekday: "short", month: "long", day: "numeric", year: "numeric" });
  $("#due").innerHTML = `Due <strong>${fmt(dl.due)}</strong><br>Aim to send by ${fmt(dl.send_by)}`;
  $("#basis").textContent = dl.basis;
  $("#ics").href = `/api/ics?due=${dl.due}&send_by=${dl.send_by}&insurer=${encodeURIComponent(r.facts.insurer || "your insurer")}`;

  $("#category").textContent = r.triage.category_label;
  $("#plain").textContent = r.triage.plain_english;
  const s = Math.max(1, Math.min(5, r.strategy.strength || 3));
  $("#meter").innerHTML = [1, 2, 3, 4, 5].map((i) => `<i class="${i <= s ? "on" : ""}"></i>`).join("");
  $("#meter").setAttribute("aria-label", `${s} out of 5`);
  $("#strength-reason").textContent = r.strategy.strength_reason;

  $("#letter").innerHTML = md(r.letter);
  $("#doctor").innerHTML = md(r.doctor_letter);
  const v = r.verification || {};
  const issues = (v.issues || []).length;
  $("#verify").textContent = issues ? `⚠ ${issues} citation${issues > 1 ? "s" : ""} to double-check` : `✓ ${v.supported}/${v.checked} citations checked against sources`;
  $("#verify").classList.toggle("warn", !!issues);
  if (issues) $("#verify").title = v.issues.map((x) => `[${x.cite}] ${x.problem}`).join("\n");

  $("#evidence").innerHTML = (r.strategy.evidence_to_gather || []).map((e) =>
    `<li><label><input type="checkbox"><span><strong>${esc(e.item)}</strong><span class="who">${esc(e.from)}</span><small>${esc(e.why)}</small></span></label></li>`).join("");
  $("#path").innerHTML = (r.triage.appeal_path || []).map((p) => `<li>${esc(p)}</li>`).join("");
  $("#askfor").innerHTML = (r.strategy.ask_for || []).map((p) => `<li>${esc(p)}</li>`).join("");

  $("#args").innerHTML = (r.strategy.arguments || []).map((a, i) => `
    <div class="card arg"><span class="n">${i + 1}</span><div><h3>${esc(a.title)}</h3>
    <p>${esc(a.point)} ${(a.cites || []).map((c) => `<a class="cite" href="#src-${c}" data-src="${c}">${c}</a>`).join("")}</p></div></div>`).join("");
  $("#weak").innerHTML = (r.strategy.insurer_weaknesses || []).map((w) => `<li>${esc(w)}</li>`).join("");

  $("#sources").innerHTML = r.sources.map((s) => `
    <li id="src-${s.id}"><span class="kind">[${s.id}] ${esc(s.kind)}</span>
    <a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a><p>${esc(s.content.slice(0, 320))}…</p></li>`).join("");

  $("#ledger").innerHTML = r.ledger.map((l) => `<tr><td>${esc(l.step)}</td><td><span class="chip">${esc(shortModel(l.model))}</span></td>
    <td>${l.prompt_tokens || "—"} / ${l.completion_tokens || "—"}</td><td>${l.seconds}</td></tr>`).join("");
  $("#facts").innerHTML = Object.entries(r.facts).filter(([, v]) => v !== null && v !== "" && !(Array.isArray(v) && !v.length))
    .map(([k, v]) => `<dt>${esc(k.replace(/_/g, " "))}</dt><dd>${esc(Array.isArray(v) ? v.join(", ") : v)}</dd>`).join("");
  window.scrollTo({ top: 0 });
}

// ---------- tabs & tools ----------
const showTab = (name) => {
  document.querySelectorAll(".tabs button").forEach((b) => b.classList.toggle("on", b.dataset.tab === name));
  document.querySelectorAll(".panel").forEach((p) => p.classList.toggle("hidden", p.dataset.panel !== name));
};
document.querySelectorAll(".tabs button").forEach((b) => b.addEventListener("click", () => showTab(b.dataset.tab)));
document.addEventListener("click", (e) => {
  const c = e.target.closest(".cite");
  if (c) { e.preventDefault(); showTab("sources"); location.hash = `src-${c.dataset.src}`; }
});
const raw = { letter: () => state.letter, doctor: () => state.doctor_letter };
document.querySelectorAll("[data-copy]").forEach((b) => b.addEventListener("click", async () => {
  await navigator.clipboard.writeText(raw[b.dataset.copy]());
  const t = b.textContent; b.textContent = "Copied"; setTimeout(() => (b.textContent = t), 1200);
}));
document.querySelectorAll("[data-download]").forEach((b) => b.addEventListener("click", () => {
  const refs = "\n\n---\nSources\n" + state.sources.map((s) => `[${s.id}] ${s.title} — ${s.url}`).join("\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([state.letter + refs], { type: "text/markdown" }));
  a.download = "appeal-letter.md"; a.click();
}));
$("#print").addEventListener("click", () => window.print());
