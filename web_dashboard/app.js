/**
 * CareFlow - Clinical Pathway Process Mining Dashboard
 * Author: Annagiri Goutham (Data Associate L1 Intern, Infotact Solutions)
 * Interactivity: Vis.js Network, Chart.js, Dynamic Filtering, ROI Simulation
 */

let appState = {
  data: null,
  network: null,
  nodesDataSet: null,
  edgesDataSet: null,
  activeFilter: 'ALL',
  activeView: 'ALL',
  complianceRate: 100
};

// Department Color Map for sleek visualization
const DEPT_COLORS = {
  "Front Desk": { bg: "#0284c7", border: "#38bdf8" },
  "Emergency Triage": { bg: "#e11d48", border: "#fb7185" },
  "ED Acute Ward": { bg: "#7c3aed", border: "#a78bfa" },
  "Radiology Department": { bg: "#d97706", border: "#fbbf24" },
  "Central Pathology": { bg: "#059669", border: "#34d399" },
  "ED Treatment Bays": { bg: "#2563eb", border: "#60a5fa" },
  "ED Short Stay Unit": { bg: "#4f46e5", border: "#818cf8" },
  "Discharge Lounge": { bg: "#0d9488", border: "#2dd4bf" },
  "Inpatient Ward": { bg: "#16a34a", border: "#4ade80" },
  "General": { bg: "#475569", border: "#94a3b8" }
};

document.addEventListener("DOMContentLoaded", () => {
  initDashboard();
});

async function initDashboard() {
  try {
    const response = await fetch("data.json");
    if (!response.ok) throw new Error("Could not load data.json");
    appState.data = await response.json();

    hideSpinner();
    renderKpis();
    initNetworkGraph();
    renderVariantsList();
    renderBottleneckTable();
    initCharts();
    initROICalculator();
    initEventListeners();
    initSampleTrace("PAT-10004");
  } catch (error) {
    console.error("Dashboard init error:", error);
    document.getElementById("canvasSpinner").innerHTML = `
      <div style="color: #f43f5e; text-align: center; padding: 2rem;">
        <i class="fa-solid fa-circle-exclamation" style="font-size: 2rem; margin-bottom: 0.5rem;"></i><br>
        Failed to load process data: ${error.message}<br>
        <small style="color: #94a3b8;">Ensure server is running and data.json exists.</small>
      </div>`;
  }
}

function hideSpinner() {
  const spinner = document.getElementById("canvasSpinner");
  if (spinner) spinner.style.display = "none";
}

function renderKpis() {
  const s = appState.data.summary;
  const roi = appState.data.roi_metrics;

  document.getElementById("kpiTotalCases").textContent = s.total_cases.toLocaleString();
  document.getElementById("kpiTotalEvents").textContent = s.total_events.toLocaleString();
  document.getElementById("kpiLoopbackRate").textContent = `${roi.radiology_loopback_rate_pct}%`;
  document.getElementById("kpiDelayPenalty").textContent = `+${roi.avg_minutes_lost_per_patient} min`;
  document.getElementById("kpiFitness").textContent = `${s.model_fitness_pct}%`;
}

function initNetworkGraph() {
  const container = document.getElementById("processNetworkCanvas");
  const rawNodes = appState.data.nodes;
  const rawEdges = appState.data.edges;

  // Transform nodes for Vis.js
  const visNodes = rawNodes.map((n) => {
    const deptTheme = DEPT_COLORS[n.department] || DEPT_COLORS["General"];
    const isBottleneck = n.is_bottleneck;

    return {
      id: n.id,
      label: formatNodeLabel(n.label, n.execution_count),
      shape: "box",
      margin: { top: 10, right: 14, bottom: 10, left: 14 },
      borderWidth: isBottleneck ? 3 : 1.5,
      color: {
        background: isBottleneck ? "#881337" : "#1e293b",
        border: isBottleneck ? "#f43f5e" : deptTheme.border,
        highlight: {
          background: isBottleneck ? "#9f1239" : "#334155",
          border: "#38bdf8"
        }
      },
      font: {
        color: "#f8fafc",
        face: "Plus Jakarta Sans",
        size: 13,
        bold: true,
        multi: true
      },
      shadow: {
        enabled: isBottleneck,
        color: "rgba(244, 63, 94, 0.6)",
        size: 12
      },
      raw: n
    };
  });

  // Transform edges for Vis.js
  const visEdges = rawEdges.map((e, index) => {
    const isLoop = e.is_loopback;
    const width = Math.max(1.8, Math.min(7, Math.log2(e.frequency) * 0.9));

    return {
      id: `edge_${index}`,
      from: e.source,
      to: e.target,
      label: `${e.frequency}x\n(${e.avg_duration_minutes}m)`,
      font: {
        size: 10,
        face: "JetBrains Mono",
        color: isLoop ? "#fb7185" : "#94a3b8",
        align: "middle",
        strokeWidth: 3,
        strokeColor: "#0f172a"
      },
      arrows: { to: { enabled: true, scaleFactor: isLoop ? 1.2 : 0.8 } },
      width: width,
      color: {
        color: isLoop ? "#f43f5e" : "#38bdf8",
        highlight: "#ffffff",
        hover: isLoop ? "#fb7185" : "#7dd3fc"
      },
      smooth: {
        enabled: true,
        type: isLoop ? "curvedCW" : "cubicBezier",
        roundness: isLoop ? 0.35 : 0.2
      },
      dashes: isLoop,
      raw: e
    };
  });

  appState.nodesDataSet = new vis.DataSet(visNodes);
  appState.edgesDataSet = new vis.DataSet(visEdges);

  const data = {
    nodes: appState.nodesDataSet,
    edges: appState.edgesDataSet
  };

  const options = {
    physics: {
      enabled: true,
      solver: "forceAtlas2Based",
      forceAtlas2Based: {
        gravitationalConstant: -70,
        centralGravity: 0.015,
        springLength: 140,
        springConstant: 0.08,
        damping: 0.4
      },
      stabilization: {
        iterations: 150
      }
    },
    interaction: {
      hover: true,
      tooltipDelay: 100,
      zoomView: false,
      dragView: false
    }
  };

  appState.network = new vis.Network(container, data, options);

  // Click handler
  appState.network.on("click", (params) => {
    if (params.nodes.length > 0) {
      const nodeId = params.nodes[0];
      const nodeObj = appState.nodesDataSet.get(nodeId);
      showNodeModal(nodeObj.raw);
    } else if (params.edges.length > 0) {
      const edgeId = params.edges[0];
      const edgeObj = appState.edgesDataSet.get(edgeId);
      showEdgeModal(edgeObj.raw);
    }
  });
}

function formatNodeLabel(title, count) {
  // Wrap text cleanly
  const words = title.split(" ");
  let lines = [];
  let currentLine = "";

  words.forEach(w => {
    if ((currentLine + " " + w).length > 22) {
      lines.push(currentLine.trim());
      currentLine = w;
    } else {
      currentLine += " " + w;
    }
  });
  if (currentLine.trim()) lines.push(currentLine.trim());

return lines.join("\n") + `\n[${count.toLocaleString("en-US")} cases]`;
}

function renderVariantsList() {
  const container = document.getElementById("variantsListContainer");
  container.innerHTML = "";

  appState.data.variants.forEach((v, index) => {
    const card = document.createElement("div");
    card.className = `variant-card ${v.has_paperwork_loop ? 'loopback-variant' : ''}`;
    
    card.innerHTML = `
      <div class="variant-header">
        <span class="variant-title">${v.variant_id}</span>
        <span class="variant-badge ${v.has_paperwork_loop ? 'danger' : ''}">
          ${v.has_paperwork_loop ? '<i class="fa-solid fa-triangle-exclamation"></i> Loopback' : 'Standard'}
        </span>
      </div>
      <div class="variant-stats">
        <span><strong>${v.case_count}</strong> patients (${v.percentage}%)</span>
        <span>${v.path.length} steps</span>
      </div>
    `;

    card.addEventListener("click", () => {
      highlightVariantPath(v.path);
    });

    container.appendChild(card);
  });
}

function highlightVariantPath(path) {
  if (!appState.network) return;

  const pathNodes = new Set(path);
  const pathTransitions = new Set();
  for (let i = 0; i < path.length - 1; i++) {
    pathTransitions.add(`${path[i]}->${path[i+1]}`);
  }

  // Update nodes style
  appState.nodesDataSet.forEach(node => {
    const inPath = pathNodes.has(node.id);
    appState.nodesDataSet.update({
      id: node.id,
      opacity: inPath ? 1.0 : 0.2,
      font: { color: inPath ? "#ffffff" : "#475569" }
    });
  });

  // Update edges style
  appState.edgesDataSet.forEach(edge => {
    const edgeKey = `${edge.from}->${edge.to}`;
    const inPath = pathTransitions.has(edgeKey);
    appState.edgesDataSet.update({
      id: edge.id,
      color: {
        color: inPath ? (edge.raw.is_loopback ? "#f43f5e" : "#38bdf8") : "rgba(100, 116, 139, 0.15)"
      },
      width: inPath ? 4.5 : 1
    });
  });
}

function renderBottleneckTable() {
  const tbody = document.getElementById("bottleneckTableBody");
  tbody.innerHTML = "";

  // Sort edges by avg duration descending
  const sorted = [...appState.data.edges].sort((a, b) => b.avg_duration_minutes - a.avg_duration_minutes);

  sorted.forEach(e => {
    const tr = document.createElement("tr");
    let pillClass = "normal";
    let pillLabel = "Standard";

    if (e.is_loopback) {
      pillClass = "critical";
      pillLabel = "Bottleneck Loop";
    } else if (e.avg_duration_minutes > 35) {
      pillClass = "rework";
      pillLabel = "High Latency";
    }

    tr.innerHTML = `
      <td>
        <strong style="color: #f8fafc;">${e.source}</strong><br>
        <span style="font-size: 0.72rem; color: #94a3b8;">↳ ${e.target}</span>
      </td>
      <td>${e.frequency}</td>
      <td style="font-family: 'JetBrains Mono'; font-weight: 600;">${e.avg_duration_minutes}m</td>
      <td><span class="status-pill ${pillClass}">${pillLabel}</span></td>
    `;
    tbody.appendChild(tr);
  });
}

function initROICalculator() {
  const slider = document.getElementById("sliderCompliance");
  const sliderVal = document.getElementById("sliderComplianceVal");
  
  const roi = appState.data.roi_metrics;
  const baseAffected = roi.affected_patients_count; // 210 in 30-day sample
  const baseMinutesSaved = roi.avg_minutes_lost_per_patient; // 66.6 mins

  slider.addEventListener("input", (e) => {
    const compliancePct = parseInt(e.target.value);
    sliderVal.textContent = `${compliancePct}% compliance`;

    // Projected savings
    const fixedRate = compliancePct / 100.0;
    const casesSavedMonth = baseAffected * fixedRate;
    const minutesSavedTotal = casesSavedMonth * baseMinutesSaved;
    const hoursSavedAnnual = Math.round((minutesSavedTotal / 60.0) * 12);
    const costAvoidedAnnual = Math.round((casesSavedMonth * 235.0) * 12);
    const bedBoost = (14.2 * fixedRate).toFixed(1);

    document.getElementById("roiWaitSaved").textContent = `${(baseMinutesSaved * fixedRate).toFixed(1)} mins`;
    document.getElementById("roiHoursRecovered").textContent = `${hoursSavedAnnual.toLocaleString()} hrs`;
    document.getElementById("roiCostAvoided").textContent = `$${costAvoidedAnnual.toLocaleString()} /yr`;
    document.getElementById("roiBedBoost").textContent = `+${bedBoost}%`;
  });
}

function initCharts() {
  // Chart 1: Archetypes Donut Chart
  const ctxArch = document.getElementById("archetypeChart").getContext("2d");
  new Chart(ctxArch, {
    type: "doughnut",
    data: {
      labels: ["Trauma / Imaging", "Acute Medical", "Combined Diagnostic", "Low Acuity Fast-Track", "Critical Emergent"],
      datasets: [{
        data: [420, 310, 160, 250, 60],
        backgroundColor: ["#f59e0b", "#38bdf8", "#a855f7", "#10b981", "#f43f5e"],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: "#94a3b8", font: { family: "Plus Jakarta Sans", size: 10 } }
        }
      },
      cutout: "65%"
    }
  });

  // Chart 2: Length of Stay Comparison Bar Chart
  const ctxStay = document.getElementById("stayComparisonChart").getContext("2d");
  new Chart(ctxStay, {
    type: "bar",
    data: {
      labels: ["Standard Non-Loopback", "Radiology Loop-Back Cohort"],
      datasets: [{
        label: "Average Stay (Minutes)",
        data: [140.6, 207.2],
        backgroundColor: ["#0ea5e9", "#f43f5e"],
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: { ticks: { color: "#94a3b8" }, grid: { display: false } },
        y: { 
          ticks: { color: "#94a3b8" }, 
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          title: { display: true, text: "Minutes", color: "#64748b" }
        }
      }
    }
  });
}

function initSampleTrace(caseId) {
  const list = document.getElementById("traceTimelineList");
  list.innerHTML = "";

  const sampleEvents = [
    { time: "00:00", act: "Registration & Arrival", dept: "Front Desk" },
    { time: "00:14", act: "Triage Assessment", dept: "Emergency Triage" },
    { time: "00:46", act: "Physician Initial Consultation", dept: "ED Acute Ward" },
    { time: "00:58", act: "Diagnostic Imaging Order", dept: "ED Acute Ward" },
    { time: "01:24", act: "Diagnostic Radiology (X-Ray)", dept: "Radiology Department" },
    { time: "01:33", act: "Missing Paperwork Flagged", dept: "Radiology Department", delay: true },
    { time: "01:52", act: "Return to Triage (Paperwork Resolution)", dept: "Emergency Triage", delay: true },
    { time: "02:18", act: "Physician Re-consultation", dept: "ED Acute Ward", delay: true },
    { time: "02:35", act: "Clinical Treatment & Medication Admin", dept: "ED Treatment Bays" },
    { time: "03:12", act: "Observation & Vital Re-check", dept: "ED Short Stay Unit" },
    { time: "03:38", act: "Discharge Planning & Summary", dept: "Discharge Lounge" }
  ];

  sampleEvents.forEach(e => {
    const li = document.createElement("li");
    li.className = "timeline-item";
    li.innerHTML = `
      <span class="timeline-time">${e.time}</span>
      <span class="timeline-text ${e.delay ? 'delay' : ''}">
        ${e.act} <small style="color: #64748b;">(${e.dept})</small>
        ${e.delay ? ' <i class="fa-solid fa-triangle-exclamation"></i>' : ''}
      </span>
    `;
    list.appendChild(li);
  });
}

function initEventListeners() {
  // Theme Toggle
  const themeBtn = document.getElementById("themeToggleBtn");
  themeBtn.addEventListener("click", () => {
    const current = document.body.getAttribute("data-theme");
    const next = current === "light" ? "dark" : "light";
    document.body.setAttribute("data-theme", next);
    themeBtn.innerHTML = next === "light" ? '<i class="fa-solid fa-sun"></i>' : '<i class="fa-solid fa-moon"></i>';
  });

  // Tab Navigation
  const tabs = document.querySelectorAll(".tab-btn");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");

      document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
      const targetId = tab.getAttribute("data-tab");
      document.getElementById(targetId).classList.add("active");
    });
  });

  // Reset View
  document.getElementById("resetViewBtn").addEventListener("click", () => {
    resetNetworkView();
  });

  // View Controls
  document.getElementById("viewAllBtn").addEventListener("click", (e) => {
    setToggleActive(e.target);
    resetNetworkView();
  });

  document.getElementById("viewBottleneckBtn").addEventListener("click", (e) => {
    setToggleActive(e.target);
    isolateBottleneckView();
  });

  document.getElementById("viewHappyPathBtn").addEventListener("click", (e) => {
    setToggleActive(e.target);
    isolateHappyPathView();
  });

  // Modal Close
  document.getElementById("modalCloseBtn").addEventListener("click", () => {
    document.getElementById("nodeDetailModal").classList.remove("open");
  });

  document.getElementById("showSolutionModalBtn").addEventListener("click", () => {
    document.querySelector('[data-tab="tabROI"]').click();
  });
}

function setToggleActive(btn) {
  document.querySelectorAll(".toggle-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
}

function resetNetworkView() {
  if (!appState.network) return;
  appState.nodesDataSet.forEach(node => {
    appState.nodesDataSet.update({ id: node.id, opacity: 1.0, hidden: false });
  });
  appState.edgesDataSet.forEach(edge => {
    appState.edgesDataSet.update({
      id: edge.id,
      color: { color: edge.raw.is_loopback ? "#f43f5e" : "#38bdf8" },
      width: edge.raw.is_loopback ? 3.5 : 2,
      hidden: false
    });
  });
  appState.network.fit({ animation: { duration: 800 } });
}

function isolateBottleneckView() {
  const bottleneckNodes = new Set([
    "Diagnostic Imaging Order",
    "Diagnostic Radiology (X-Ray)",
    "Missing Paperwork Flagged",
    "Return to Triage (Paperwork Resolution)",
    "Physician Re-consultation"
  ]);

  appState.nodesDataSet.forEach(node => {
    const keep = bottleneckNodes.has(node.id);
    appState.nodesDataSet.update({ id: node.id, opacity: keep ? 1.0 : 0.1 });
  });

  appState.edgesDataSet.forEach(edge => {
    const keep = edge.raw.is_loopback || (edge.from === "Diagnostic Imaging Order" && edge.to === "Diagnostic Radiology (X-Ray)");
    appState.edgesDataSet.update({
      id: edge.id,
      color: { color: keep ? "#f43f5e" : "rgba(255,255,255,0.05)" },
      width: keep ? 4.5 : 1
    });
  });
}

function isolateHappyPathView() {
  const happyPath = new Set(appState.data.ideal_pathway);
  highlightVariantPath(appState.data.ideal_pathway);
}

function showNodeModal(node) {
  const modal = document.getElementById("nodeDetailModal");
  document.getElementById("modalNodeTitle").innerHTML = `<i class="fa-solid fa-circle-nodes"></i> ${node.label}`;
  
  document.getElementById("modalNodeBody").innerHTML = `
    <div style="display: flex; flex-direction: column; gap: 0.75rem;">
      <p><strong>Department:</strong> ${node.department}</p>
<p><strong>Total Executions:</strong> ${node.execution_count.toLocaleString("en-US")} patient events</p>
      <p><strong>Average Activity Cost:</strong> $${node.avg_cost_usd.toFixed(2)} USD</p>
      <p><strong>Operational Classification:</strong> ${node.is_bottleneck ? '<span style="color:#f43f5e; font-weight:700;">Critical Process Bottleneck (Rework Loop)</span>' : '<span style="color:#10b981; font-weight:700;">Standard Clinical Stage</span>'}</p>
      ${node.is_bottleneck ? '<div style="background: rgba(244,63,94,0.1); border: 1px solid rgba(244,63,94,0.3); border-radius: 8px; padding: 0.75rem; color: #fecdd3;">Root Cause: Failure to sign radiation consent intake Form 4B prior to patient transfer to radiology suite.</div>' : ''}
    </div>
  `;
  modal.classList.add("open");
}

function showEdgeModal(edge) {
  const modal = document.getElementById("nodeDetailModal");
  document.getElementById("modalNodeTitle").innerHTML = `<i class="fa-solid fa-arrow-right-arrow-left"></i> Transition Edge`;
  
  document.getElementById("modalNodeBody").innerHTML = `
    <div style="display: flex; flex-direction: column; gap: 0.75rem;">
      <p><strong>Origin:</strong> ${edge.source}</p>
      <p><strong>Destination:</strong> ${edge.target}</p>
      <p><strong>Patient Volume:</strong> ${edge.frequency.toLocaleString("en-US")} occurrences</p>
      <p><strong>Average Transition Time:</strong> ${edge.avg_duration_minutes} minutes</p>
      <p><strong>Flow Archetype:</strong> ${edge.is_loopback ? '<span style="color:#f43f5e; font-weight:700;">Deviant Loop-Back (Administrative Rework)</span>' : '<span style="color:#38bdf8; font-weight:700;">Linear Clinical Progression</span>'}</p>
    </div>
  `;
  modal.classList.add("open");
}
