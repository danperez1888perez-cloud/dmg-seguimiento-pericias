const DATA_INDEX_URL = "./data/index.json";

const CODE_HASH = "3b612c75a7b5048a435fb6ec81e52ff92d6d795a8b5a9c17070f6a63c97a53b2"; // SHA-256("Admin123")

const $ = (id) => document.getElementById(id);

const viewHome = $("view-home");
const viewCase = $("view-case");
const casesDiv = $("cases");
const q = $("q");
const filterEstado = $("filterEstado");
const refreshBtn = $("refresh");
const backBtn = $("back");

const caseHeader = $("caseHeader");
const periciasBody = $("periciasBody");

const exportBox = $("exportBox");
const btnExport = $("btnExportXlsx");
const authModal = $("authModal");
const codeInput = $("codeInput");
const msg = $("msg");
const btnCancel = $("btnCancel");
const btnOk = $("btnOk");

let index = [];
let currentCase = null;

function showHome() {
  viewCase.classList.add("hidden");
  viewHome.classList.remove("hidden");
  currentCase = null;
  renderCards();
}

function showCase() {
  viewHome.classList.add("hidden");
  viewCase.classList.remove("hidden");
}

function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
  }[c]));
}

async function loadIndex() {
  const res = await fetch(DATA_INDEX_URL, { cache: "no-store" });
  if (!res.ok) throw new Error("No se pudo cargar data/index.json");
  index = await res.json();
}

async function loadCase(casoId) {
  const res = await fetch(`./data/casos/${casoId}.json`, { cache: "no-store" });
  if (!res.ok) throw new Error("No se pudo cargar el caso");
  return await res.json();
}

function normalizeEstadoGeneral(caso) {
  const ests = (caso.pericias || []).map(p => p.estado);
  if (ests.includes("No iniciada")) return "No iniciada";
  if (ests.includes("En proceso")) return "En proceso";
  return (ests.length ? "Realizada" : "No iniciada");
}

function badge(text) {
  return `<span class="badge">${escapeHtml(text || "")}</span>`;
}

function renderCards() {
  const term = q.value.trim().toUpperCase();
  const estFilter = filterEstado.value;

  const filtered = index
    .filter(c => !term || String(c.caso).toUpperCase().includes(term))
    .filter(c => !estFilter || c.estado_general === estFilter);

  casesDiv.innerHTML = filtered.map(c => `
    <div class="card" data-caso="${escapeHtml(c.caso)}">
      <div class="row">
        <div style="font-weight:800">${escapeHtml(c.caso)}</div>
        ${badge(c.estado_general)}
      </div>
      <div class="meta">
        <div><b>Tipo:</b> ${escapeHtml(c.tipo || "")}</div>
        <div><b>Fecha hecho:</b> ${escapeHtml(c.fecha_hecho || "")}</div>
        <div><b>Pericias:</b> ${escapeHtml(String(c.total_pericias ?? 0))}</div>
        <div><b>Últ. actualización:</b> ${escapeHtml(c.ultima_actualizacion || "")}</div>
      </div>
    </div>
  `).join("");

  [...casesDiv.querySelectorAll(".card")].forEach(el => {
    el.addEventListener("click", async () => {
      const id = el.getAttribute("data-caso");
      const data = await loadCase(id);
      currentCase = data;
      renderCase(data);
      showCase();
    });
  });
}

function renderCase(caso) {
  const estadoGeneral = normalizeEstadoGeneral(caso);
  caseHeader.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:12px;">
      <div>
        <div style="font-size:22px;font-weight:900">${escapeHtml(caso.caso)}</div>
        <div style="opacity:.8;margin-top:2px">
          <b>Tipo:</b> ${escapeHtml(caso.tipo || "")} ·
          <b>Fecha hecho:</b> ${escapeHtml(caso.fecha_hecho || "")} ·
          <b>Estado:</b> ${escapeHtml(estadoGeneral)}
        </div>
      </div>
      ${badge(estadoGeneral)}
    </div>
  `;

  const pericias = (caso.pericias || []).slice().sort((a,b) => (a.id||"").localeCompare(b.id||""));
  periciasBody.innerHTML = pericias.map(p => `
    <tr>
      <td>${escapeHtml(p.id)}</td>
      <td>${escapeHtml(p.tipo_pericia)}</td>
      <td>${escapeHtml(p.seccion)}</td>
      <td>${escapeHtml(p.estado)}</td>
      <td>${escapeHtml(p.fecha_disposicion || "")}</td>
      <td>${escapeHtml(p.ultima_actualizacion || "")}</td>
      <td>${escapeHtml(p.avance || "")}</td>
      <td>${escapeHtml(p.responsable || "")}</td>
      <td>${escapeHtml(p.observaciones || "")}</td>
    </tr>
  `).join("");
}

// --- Export oculto: Ctrl + Alt + A ---
function openModal() {
  msg.classList.add("hidden");
  codeInput.value = "";
  authModal.classList.remove("hidden");
  setTimeout(() => codeInput.focus(), 60);
}
function closeModal() {
  authModal.classList.add("hidden");
}

async function sha256(text) {
  const enc = new TextEncoder().encode(text);
  const buf = await crypto.subtle.digest("SHA-256", enc);
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, "0")).join("");
}

async function authorize() {
  const input = codeInput.value.trim();
  const h = await sha256(input);
  if (h === CODE_HASH) {
    sessionStorage.setItem("ops_export_enabled", "1");
    exportBox.classList.remove("hidden");
    closeModal();
  } else {
    msg.classList.remove("hidden");
  }
}

document.addEventListener("keydown", (e) => {
  if (e.ctrlKey && e.altKey && e.key.toLowerCase() === "a") {
    e.preventDefault();
    openModal();
  }
  if (e.key === "Escape") closeModal();
});

btnCancel.addEventListener("click", closeModal);
btnOk.addEventListener("click", authorize);
codeInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") authorize();
});

if (sessionStorage.getItem("ops_export_enabled") === "1") {
  exportBox.classList.remove("hidden");
}

btnExport.addEventListener("click", () => {
  const url = "./exports/Matriz_Oficial.xlsx";
  const a = document.createElement("a");
  a.href = url;
  a.download = "Matriz_Oficial.xlsx";
  document.body.appendChild(a);
  a.click();
  a.remove();
});

// UI wiring
q.addEventListener("input", renderCards);
filterEstado.addEventListener("change", renderCards);
refreshBtn.addEventListener("click", async () => { await boot(); });
backBtn.addEventListener("click", showHome);

async function boot() {
  try {
    await loadIndex();
    renderCards();
    showHome();
  } catch (e) {
    casesDiv.innerHTML = `<div class="card">Error cargando datos: ${escapeHtml(e.message)}</div>`;
  }
}
boot();
