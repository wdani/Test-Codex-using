const I18N = {
  en: {
    title: "HA Context Explorer Next",
    topNoisy: "Top noisy entities",
    recommendations: "Recommendations",
    recorderAdvice: "Recorder advice",
    copyYaml: "Copy YAML",
    copied: "Copied",
    entities: "Entities",
    unavailable: "Unavailable/Unknown",
    lowBattery: "Low battery",
    next: "Next",
    error: "Error",
    score: "score",
    domainFilter: "Domain filter",
    sortBy: "Sort",
    risk: "Risk",
    exportWorkbench: "Export workbench",
    exportLevel: "Export level",
    copyExport: "Copy export JSON",
    copyShort: "Copy LLM short",
    copyFirst: "Copy do_first",
    domainHealth: "Domain health matrix",
    keyHint: "Set HCX_MASK_KEY to enable export endpoints.",
  },
  de: {
    title: "HA Context Explorer Next",
    topNoisy: "Entitäten mit hoher Last",
    recommendations: "Empfehlungen",
    recorderAdvice: "Recorder-Hinweise",
    copyYaml: "YAML kopieren",
    copied: "Kopiert",
    entities: "Entitäten",
    unavailable: "Nicht verfügbar/Unbekannt",
    lowBattery: "Niedriger Batteriestand",
    next: "Nächster Schritt",
    error: "Fehler",
    score: "Score",
    domainFilter: "Domain-Filter",
    sortBy: "Sortierung",
    risk: "Risiko",
    exportWorkbench: "Export-Werkbank",
    exportLevel: "Export-Level",
    copyExport: "Export-JSON kopieren",
    copyShort: "LLM Kurzkontext kopieren",
    copyFirst: "do_first kopieren",
    domainHealth: "Domain-Gesundheitsmatrix",
    keyHint: "Setze HCX_MASK_KEY, um Export-Endpunkte zu aktivieren.",
  },
};

function t(lang, key) {
  const locale = I18N[lang] ? lang : "en";
  return I18N[locale][key] || I18N.en[key] || key;
}

class HaContextExplorerNextPanel extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    this._lang = (hass.language || "en").slice(0, 2);
    if (!this._loaded) {
      this._loaded = true;
      this._sort = "score_desc";
      this._domain = "all";
      this._exportLevel = "short";
      this.render();
      this.load();
    }
  }

  render() {
    this.innerHTML = `
      <style>
        .grid { display:grid; gap:12px; }
        .kpis { display:flex; gap:8px; flex-wrap:wrap; }
        .kpi { padding:8px 10px; border:1px solid var(--divider-color); border-radius:10px; min-width:120px; }
        .card { padding:12px; border:1px solid var(--divider-color); border-radius:10px; background:var(--card-background-color, transparent); }
        .controls { display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
        table { width:100%; border-collapse:collapse; }
        th, td { border-bottom:1px solid var(--divider-color); padding:6px; text-align:left; }
        .risk { padding:2px 8px; border-radius:999px; font-size:12px; font-weight:600; }
        .risk-safe { background:#2e7d3233; color:#2e7d32; }
        .risk-review { background:#f9a82533; color:#8d6e00; }
        .risk-aggressive { background:#c6282833; color:#b71c1c; }
        .hint { font-size:12px; color:var(--secondary-text-color); }
        @media (max-width: 700px) { .kpi { min-width:unset; width:100%; } }
      </style>
      <ha-card header="${t(this._lang, "title")}">
        <div class="grid" style="padding:16px;">
          <div id="kpis" class="kpis"></div>
          <div class="card">
            <h3>${t(this._lang, "topNoisy")}</h3>
            <ul id="noise"></ul>
          </div>
          <div class="card">
            <h3>${t(this._lang, "recorderAdvice")}</h3>
            <div class="controls">
              <label>${t(this._lang, "domainFilter")}: <select id="domainSelect"></select></label>
              <label>${t(this._lang, "sortBy")}: <select id="sortSelect">
                <option value="score_desc">Score ↓</option>
                <option value="score_asc">Score ↑</option>
                <option value="risk">${t(this._lang, "risk")}</option>
              </select></label>
              <button id="copyYamlBtn" type="button">${t(this._lang, "copyYaml")}</button>
              <small id="copyState"></small>
            </div>
            <table id="recorderTable"></table>
            <pre id="recorder"></pre>
          </div>
          <div class="card">
            <h3>${t(this._lang, "domainHealth")}</h3>
            <table id="domainHealthTable"></table>
          </div>
          <div class="card">
            <h3>${t(this._lang, "exportWorkbench")}</h3>
            <div class="controls">
              <label>${t(this._lang, "exportLevel")}: <select id="exportLevelSelect"><option value="short">short</option><option value="deep">deep</option></select></label>
              <button id="copyExportBtn" type="button">${t(this._lang, "copyExport")}</button>
              <button id="copyShortBtn" type="button">${t(this._lang, "copyShort")}</button>
              <button id="copyFirstBtn" type="button">${t(this._lang, "copyFirst")}</button>
              <small id="exportCopyState"></small>
            </div>
            <div class="hint" id="exportHint"></div>
            <pre id="exportPreview"></pre>
          </div>
          <div>
            <h3>${t(this._lang, "recommendations")}</h3>
            <div id="recs" class="grid"></div>
          </div>
        </div>
      </ha-card>
    `;
  }

  _riskBadge(risk) {
    return `<span class="risk risk-${risk}">${risk}</span>`;
  }

  _kpi(label, value) {
    return `<div class="kpi"><b>${value}</b><br><small>${label}</small></div>`;
  }

  _rec(rec) {
    return `<div class="card"><b>[${rec.severity.toUpperCase()}] ${rec.title}</b><div>${rec.detail}</div><small>category=${rec.category || "general"}, confidence=${rec.confidence ?? "-"}</small><br><small><b>${t(this._lang, "next")}:</b> ${rec.next_action || "-"}</small></div>`;
  }

  _sortRows(rows) {
    if (this._sort === "score_asc") return rows.sort((a, b) => a.noise_score - b.noise_score);
    if (this._sort === "risk") {
      const order = { aggressive: 0, review: 1, safe: 2 };
      return rows.sort((a, b) => (order[a.risk_level] ?? 9) - (order[b.risk_level] ?? 9));
    }
    return rows.sort((a, b) => b.noise_score - a.noise_score);
  }

  _renderRecorderTable(advice) {
    let rows = [...(advice.entity_suggestions || [])];
    if (this._domain !== "all") rows = rows.filter((r) => r.domain === this._domain);
    rows = this._sortRows(rows);

    this.querySelector("#recorderTable").innerHTML = `
      <thead><tr><th>Entity</th><th>Domain</th><th>${t(this._lang, "score")}</th><th>${t(this._lang, "risk")}</th></tr></thead>
      <tbody>${rows
        .map((r) => `<tr><td>${r.entity_id}</td><td>${r.domain}</td><td>${r.noise_score}</td><td>${this._riskBadge(r.risk_level)}</td></tr>`)
        .join("")}</tbody>`;
  }



  _formatError(err) {
    if (!err) return "unknown error";
    const status = err?.status_code || err?.status || err?.code;
    const msg = err?.body?.message || err?.message || String(err);
    if (status === 412 || msg.includes("HCX_MASK_KEY")) {
      return `${msg} (${t(this._lang, "keyHint")})`;
    }
    return msg;
  }

  async _loadExport() {
    const level = this._exportLevel;
    const path = `ha_context_explorer_next/export/ai_context/${level}`;
    try {
      const payload = await this._hass.callApi("GET", path);
      this._exportPayload = payload;
      const firstCount = payload?.action_queue?.do_first?.length || 0;
      this.querySelector("#exportHint").textContent = `level=${level}, do_first=${firstCount}`;
      this.querySelector("#exportPreview").textContent = JSON.stringify(payload, null, 2);
    } catch (err) {
      this._exportPayload = null;
      this.querySelector("#exportHint").textContent = `${t(this._lang, "error")}: ${this._formatError(err)}`;
      this.querySelector("#exportPreview").textContent = "{}";
    }
  }

  async load() {
    try {
      const payload = await this._hass.callApi("GET", "ha_context_explorer_next/summary");
      const entitiesTotal = payload.summary?.entities_total ?? 0;
      const unavailable = payload.summary?.entities_unavailable_or_unknown ?? 0;
      const batteryLow = payload.battery?.battery_entities_low ?? 0;
      const topNoise = (payload.noise?.top_noisy_entities || []).slice(0, 5);

      this.querySelector("#kpis").innerHTML = [
        this._kpi(t(this._lang, "entities"), entitiesTotal),
        this._kpi(t(this._lang, "unavailable"), unavailable),
        this._kpi(t(this._lang, "lowBattery"), batteryLow),
      ].join("");

      this.querySelector("#noise").innerHTML = topNoise
        .map((item) => `<li>${item.entity_id} — ${t(this._lang, "score")} ${item.noise_score}</li>`)
        .join("");


      const domainHealthRows = (payload.domain_health || [])
        .map((d) => `<tr><td>${d.domain}</td><td>${d.entities}</td><td>${d.noise_score}</td><td>${d.noise_density}</td><td>${this._riskBadge(d.risk)}</td></tr>`)
        .join("");
      this.querySelector("#domainHealthTable").innerHTML = `<thead><tr><th>Domain</th><th>Entities</th><th>Score</th><th>Density</th><th>Risk</th></tr></thead><tbody>${domainHealthRows}</tbody>`;

      const recorderAdvice = payload.recorder_advice || {};
      this.querySelector("#recorder").textContent = JSON.stringify(recorderAdvice.yaml_preview || {}, null, 2);

      const domains = ["all", ...new Set((recorderAdvice.entity_suggestions || []).map((r) => r.domain))];
      this.querySelector("#domainSelect").innerHTML = domains
        .map((d) => `<option value="${d}">${d}</option>`)
        .join("");

      this.querySelector("#domainSelect").onchange = (e) => {
        this._domain = e.target.value;
        this._renderRecorderTable(recorderAdvice);
      };

      this.querySelector("#sortSelect").onchange = (e) => {
        this._sort = e.target.value;
        this._renderRecorderTable(recorderAdvice);
      };

      this.querySelector("#copyYamlBtn").onclick = async () => {
        try {
          await navigator.clipboard.writeText(this.querySelector("#recorder").textContent || "");
          this.querySelector("#copyState").textContent = t(this._lang, "copied");
        } catch (e) {
          this.querySelector("#copyState").textContent = `${t(this._lang, "error")}: ${e}`;
        }
      };

      this.querySelector("#exportLevelSelect").onchange = async (e) => {
        this._exportLevel = e.target.value;
        await this._loadExport();
      };

      const copyText = async (text) => {
        try {
          await navigator.clipboard.writeText(text);
          this.querySelector("#exportCopyState").textContent = t(this._lang, "copied");
        } catch (e) {
          this.querySelector("#exportCopyState").textContent = `${t(this._lang, "error")}: ${this._formatError(e)}`;
        }
      };

      this.querySelector("#copyExportBtn").onclick = async () => copyText(JSON.stringify(this._exportPayload || {}, null, 2));
      this.querySelector("#copyShortBtn").onclick = async () => copyText(JSON.stringify(this._exportPayload?.llm_context_short || {}, null, 2));
      this.querySelector("#copyFirstBtn").onclick = async () => copyText(JSON.stringify(this._exportPayload?.action_queue?.do_first || [], null, 2));

      this._renderRecorderTable(recorderAdvice);
      await this._loadExport();

      this.querySelector("#recs").innerHTML = (payload.recommendations || []).map((rec) => this._rec(rec)).join("");
    } catch (err) {
      this.innerHTML = `<ha-card><div style="padding:16px">${t(this._lang, "error")}: ${this._formatError(err)}</div></ha-card>`;
    }
  }
}

customElements.define("ha-context-explorer-next-panel", HaContextExplorerNextPanel);
