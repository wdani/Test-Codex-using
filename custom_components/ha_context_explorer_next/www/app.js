const I18N = {
  en: {
    title: "HA Context Explorer Next",
    topNoisy: "Top noisy entities",
    recommendations: "Recommendations",
    recorderAdvice: "Recorder advice",
    recorderVolume: "Recorder/logbook volume",
    copyYaml: "Copy YAML",
    copied: "Copied",
    entities: "Entities",
    unavailable: "Unavailable/Unknown",
    lowBattery: "Low battery",
    criticalBattery: "Critical battery",
    watchBattery: "Watch battery",
    unknownBattery: "Unknown battery",
    batteryHealth: "Battery health",
    maintenanceQueue: "Maintenance queue",
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
    copyUiContext: "Copy UI context",
    domainHealth: "Domain health matrix",
    keyHint: "A privacy key is created automatically; HCX_MASK_KEY only overrides it for development.",
    backupKey: "Download key backup",
    rotateKey: "Rotate key",
    keySource: "Key source",
    keyFingerprint: "Key fingerprint",
    keyBackupReady: "Key backup ready",
    keyRotated: "Key rotated",
    rotateKeyConfirm: "Rotate privacy key? New exports will use different masked aliases than older exports.",
    privacyStatus: "Privacy/export status",
    exportsReady: "Exports enabled",
    exportsLocked: "Exports locked",
    privacyCoverage: "Privacy coverage",
    sensitiveKeys: "Sensitive keys",
    textPatterns: "Text patterns",
    entitiesWithSignals: "Entities with signals",
    diagnostics: "Diagnostics",
    loadDiagnostics: "Load diagnostics",
    copyDiagnostics: "Copy diagnostics JSON",
    diagnosticsReady: "Diagnostics ready",
    estimatedEvents: "Estimated events/day",
    estimatedBytes: "Estimated bytes/day",
    hotspots: "Hotspots",
    panelLoadFailed: "Panel could not load",
  },
  de: {
    title: "HA Context Explorer Next",
    topNoisy: "Entitäten mit hoher Last",
    recommendations: "Empfehlungen",
    recorderAdvice: "Recorder-Hinweise",
    recorderVolume: "Recorder/Logbook-Volumen",
    copyYaml: "YAML kopieren",
    copied: "Kopiert",
    entities: "Entitäten",
    unavailable: "Nicht verfügbar/Unbekannt",
    lowBattery: "Niedriger Batteriestand",
    criticalBattery: "Kritischer Batteriestand",
    watchBattery: "Batterie beobachten",
    unknownBattery: "Unklare Batterie",
    batteryHealth: "Batterie-Gesundheit",
    maintenanceQueue: "Wartungsliste",
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
    copyUiContext: "UI-Kontext kopieren",
    domainHealth: "Domain-Gesundheitsmatrix",
    keyHint: "Ein Datenschutz-Schluessel wird automatisch erstellt; HCX_MASK_KEY ist nur ein Entwickler-Override.",
    backupKey: "Key-Backup laden",
    rotateKey: "Key rotieren",
    keySource: "Key-Quelle",
    keyFingerprint: "Key-Fingerprint",
    keyBackupReady: "Key-Backup bereit",
    keyRotated: "Key rotiert",
    rotateKeyConfirm: "Privacy-Key rotieren? Neue Exporte nutzen andere maskierte Aliase als alte Exporte.",
    privacyStatus: "Datenschutz/Export-Status",
    exportsReady: "Exporte aktiv",
    exportsLocked: "Exporte gesperrt",
    privacyCoverage: "Datenschutz-Abdeckung",
    sensitiveKeys: "Sensitive Keys",
    textPatterns: "Textmuster",
    entitiesWithSignals: "Entitaeten mit Signalen",
    diagnostics: "Diagnose",
    loadDiagnostics: "Diagnose laden",
    copyDiagnostics: "Diagnose-JSON kopieren",
    diagnosticsReady: "Diagnose bereit",
    estimatedEvents: "Geschaetzte Events/Tag",
    estimatedBytes: "Geschaetzte Bytes/Tag",
    hotspots: "Hotspots",
    panelLoadFailed: "Panel konnte nicht geladen werden",
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
      this.load().catch((err) => this._showFatalError(err));
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
        .risk-critical { background:#b71c1c33; color:#b71c1c; }
        .risk-low { background:#e6510033; color:#bf360c; }
        .risk-watch { background:#f9a82533; color:#8d6e00; }
        .risk-unknown { background:#61616133; color:#424242; }
        .hint { font-size:12px; color:var(--secondary-text-color); }
        pre { white-space:pre-wrap; overflow:auto; max-height:420px; }
        @media (max-width: 700px) { .kpi { min-width:unset; width:100%; } }
      </style>
      <ha-card header="${t(this._lang, "title")}">
        <div class="grid" style="padding:16px;">
          <div id="kpis" class="kpis"></div>
          <div class="card">
            <h3>${t(this._lang, "batteryHealth")}</h3>
            <div class="hint" id="batterySummary"></div>
            <table id="batteryTable"></table>
          </div>
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
            <h3>${t(this._lang, "recorderVolume")}</h3>
            <div class="hint" id="recorderVolumeSummary"></div>
            <table id="recorderVolumeTable"></table>
          </div>
          <div class="card">
            <h3>${t(this._lang, "domainHealth")}</h3>
            <table id="domainHealthTable"></table>
          </div>
          <div class="card">
            <h3>${t(this._lang, "privacyStatus")}</h3>
            <div class="controls">
              <button id="downloadKeyBtn" type="button">${t(this._lang, "backupKey")}</button>
              <button id="rotateKeyBtn" type="button">${t(this._lang, "rotateKey")}</button>
              <small id="privacyKeyState"></small>
            </div>
            <div class="hint" id="privacyStatus"></div>
            <div id="privacyCoverage"></div>
          </div>
          <div class="card">
            <h3>${t(this._lang, "exportWorkbench")}</h3>
            <div class="controls">
              <label>${t(this._lang, "exportLevel")}: <select id="exportLevelSelect"><option value="short">short</option><option value="deep">deep</option></select></label>
              <button id="copyExportBtn" type="button">${t(this._lang, "copyExport")}</button>
              <button id="copyShortBtn" type="button">${t(this._lang, "copyShort")}</button>
              <button id="copyFirstBtn" type="button">${t(this._lang, "copyFirst")}</button>
              <button id="copyUiContextBtn" type="button">${t(this._lang, "copyUiContext")}</button>
              <small id="exportCopyState"></small>
            </div>
            <div class="hint" id="exportHint"></div>
            <pre id="exportPreview"></pre>
          </div>
          <div class="card">
            <h3>${t(this._lang, "diagnostics")}</h3>
            <div class="controls">
              <button id="loadDiagnosticsBtn" type="button">${t(this._lang, "loadDiagnostics")}</button>
              <button id="copyDiagnosticsBtn" type="button">${t(this._lang, "copyDiagnostics")}</button>
              <small id="diagnosticsState"></small>
            </div>
            <pre id="diagnosticsPreview"></pre>
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

  _formatBytes(value) {
    const bytes = Number(value || 0);
    if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MiB`;
    if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KiB`;
    return `${bytes} B`;
  }

  _escape(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    })[char]);
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



  _stringifySafe(value) {
    if (value === undefined) return "";
    if (value === null) return "null";
    if (typeof value === "string") return value;
    if (typeof value === "number" || typeof value === "boolean") return String(value);
    try {
      const json = JSON.stringify(value);
      return json && json !== "{}" ? json : String(value);
    } catch (_err) {
      return String(value);
    }
  }

  _formatError(err) {
    try {
      if (!err) return "unknown error";
      const status = err?.status_code || err?.status || err?.code;
      const statusText = err?.statusText || err?.status_text || "";
      const body = err?.body || err?.response || err;
      const msg = body?.message || body?.error || err?.message || statusText || body;
      let msgText = this._stringifySafe(msg);
      if (!msgText || msgText === "[object Object]") {
        msgText = status ? `HTTP ${status}` : "unknown error";
      }
      if (status === 412 || msgText.includes("HCX_MASK_KEY") || msgText.includes("Privacy mask key")) {
        return `${msgText} (${t(this._lang, "keyHint")})`;
      }
      return msgText;
    } catch (_err) {
      return "unknown error";
    }
  }

  _setText(selector, text) {
    const element = this.querySelector(selector);
    if (element) element.textContent = text;
  }

  _showFatalError(err) {
    const message = this._formatError(err);
    globalThis.console?.warn?.(`HA Context Explorer Next panel load failed: ${message}`);
    this.innerHTML = `
      <ha-card header="${t(this._lang, "title")}">
        <div style="padding:16px">
          <b>${t(this._lang, "panelLoadFailed")}</b>
          <div class="hint">${this._escape(message)}</div>
        </div>
      </ha-card>
    `;
  }

  _downloadJson(filename, payload) {
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  async _writeClipboard(text) {
    const value = text ?? "";
    const clipboard = globalThis.navigator?.clipboard;
    if (clipboard?.writeText) {
      await clipboard.writeText(value);
      return;
    }

    const textarea = document.createElement("textarea");
    textarea.value = value;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";
    textarea.style.top = "0";
    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();
    textarea.setSelectionRange(0, value.length);

    try {
      if (!document.execCommand("copy")) {
        throw new Error("Clipboard copy is not available in this browser context");
      }
    } finally {
      textarea.remove();
    }
  }

  _setExportCopyDisabled(disabled) {
    ["#copyExportBtn", "#copyShortBtn", "#copyFirstBtn"].forEach((selector) => {
      const button = this.querySelector(selector);
      if (button) button.disabled = disabled;
    });
  }

  _renderRecorderVolume(volume) {
    const totals = volume?.totals || {};
    const rows = (volume?.top_entities || []).slice(0, 8);
    this.querySelector("#recorderVolumeSummary").textContent =
      `${t(this._lang, "estimatedEvents")}: ${totals.estimated_daily_events || 0}, ` +
      `${t(this._lang, "estimatedBytes")}: ${this._formatBytes(totals.estimated_daily_state_bytes || 0)}, ` +
      `${t(this._lang, "hotspots")}: ${totals.high_impact_entities || 0}`;

    this.querySelector("#recorderVolumeTable").innerHTML = `
      <thead><tr><th>Entity</th><th>Domain</th><th>${t(this._lang, "estimatedEvents")}</th><th>${t(this._lang, "estimatedBytes")}</th><th>${t(this._lang, "risk")}</th></tr></thead>
      <tbody>${rows
        .map((r) => `<tr><td>${this._escape(r.entity_id)}</td><td>${this._escape(r.domain)}</td><td>${this._escape(r.estimated_daily_events)}</td><td>${this._escape(this._formatBytes(r.estimated_daily_state_bytes))}</td><td>${this._riskBadge(r.risk_level)}</td></tr>`)
        .join("")}</tbody>`;
  }

  _renderBatteryHealth(battery) {
    const risks = (battery?.top_battery_risks || []).slice(0, 8);
    this.querySelector("#batterySummary").textContent =
      `${t(this._lang, "criticalBattery")}: ${battery?.battery_entities_critical || 0}, ` +
      `${t(this._lang, "lowBattery")}: ${battery?.battery_entities_low || 0}, ` +
      `${t(this._lang, "watchBattery")}: ${battery?.battery_entities_watch || 0}, ` +
      `${t(this._lang, "unknownBattery")}: ${battery?.battery_entities_unknown || 0}`;

    this.querySelector("#batteryTable").innerHTML = `
      <thead><tr><th>Entity</th><th>Device</th><th>%</th><th>${t(this._lang, "risk")}</th><th>${t(this._lang, "next")}</th></tr></thead>
      <tbody>${risks
        .map((r) => `<tr><td>${this._escape(r.entity_id)}</td><td>${this._escape(r.device_key)}</td><td>${this._escape(r.percent ?? "-")}</td><td>${this._riskBadge(r.risk_level)}</td><td>${this._escape(r.recommended_action)}</td></tr>`)
        .join("")}</tbody>`;
  }

  _setDiagnosticsCopyDisabled(disabled) {
    const button = this.querySelector("#copyDiagnosticsBtn");
    if (button) button.disabled = disabled;
  }

  _renderPrivacyCoverage(coverage) {
    const keyHits = (coverage?.sensitive_key_hits || [])
      .slice(0, 6)
      .map((item) => `${this._escape(item.key)} (${item.count})`)
      .join(", ") || "-";
    const patternHits = Object.entries(coverage?.text_pattern_hits || {})
      .map(([key, count]) => `${this._escape(key)} (${count})`)
      .join(", ") || "-";

    this.querySelector("#privacyCoverage").innerHTML = `
      <div><b>${this._escape(coverage?.entities_with_sensitive_signals ?? 0)}</b> / ${this._escape(coverage?.entities_scanned ?? 0)} ${t(this._lang, "entitiesWithSignals")}</div>
      <div class="hint">${t(this._lang, "sensitiveKeys")}: ${keyHits}</div>
      <div class="hint">${t(this._lang, "textPatterns")}: ${patternHits}</div>
    `;
  }

  _renderPrivacyStatus(privacy) {
    const source = privacy?.key_source || "-";
    const fingerprint = privacy?.key_fingerprint || "-";
    this.querySelector("#privacyStatus").textContent =
      `${privacy.exports_enabled ? t(this._lang, "exportsReady") : t(this._lang, "exportsLocked")} - ` +
      `${t(this._lang, "keySource")}: ${source}, ${t(this._lang, "keyFingerprint")}: ${fingerprint}`;

    const rotateButton = this.querySelector("#rotateKeyBtn");
    if (rotateButton) rotateButton.disabled = !privacy.rotation_available;
  }

  async _downloadKeyBackup() {
    try {
      const payload = await this._hass.callApi("GET", "ha_context_explorer_next/privacy/key/backup");
      const fingerprint = payload?.key_fingerprint || "privacy-key";
      this._downloadJson(`ha-context-explorer-mask-key-${fingerprint}.json`, payload);
      this.querySelector("#privacyKeyState").textContent = t(this._lang, "keyBackupReady");
    } catch (err) {
      this.querySelector("#privacyKeyState").textContent = `${t(this._lang, "error")}: ${this._formatError(err)}`;
    }
  }

  async _rotateKey() {
    if (!globalThis.confirm(t(this._lang, "rotateKeyConfirm"))) return;
    try {
      await this._hass.callApi("POST", "ha_context_explorer_next/privacy/key/rotate");
      this.querySelector("#privacyKeyState").textContent = t(this._lang, "keyRotated");
      await this.load();
    } catch (err) {
      this.querySelector("#privacyKeyState").textContent = `${t(this._lang, "error")}: ${this._formatError(err)}`;
    }
  }

  async _loadExport() {
    const level = this._exportLevel;
    const path = `ha_context_explorer_next/export/ai_context/${level}`;
    this._setExportCopyDisabled(true);
    try {
      const payload = await this._hass.callApi("GET", path);
      this._exportPayload = payload;
      const firstCount = payload?.action_queue?.do_first?.length || 0;
      this.querySelector("#exportHint").textContent = `level=${level}, do_first=${firstCount}`;
      this.querySelector("#exportPreview").textContent = JSON.stringify(payload, null, 2);
      this._setExportCopyDisabled(false);
    } catch (err) {
      this._exportPayload = null;
      this._setText("#exportHint", `${t(this._lang, "error")}: ${this._formatError(err)}`);
      this._setText("#exportPreview", "{}");
      this._setExportCopyDisabled(true);
    }
  }

  async _copyUiContext(copyText) {
    const button = this.querySelector("#copyUiContextBtn");
    if (button) button.disabled = true;
    try {
      const payload = await this._hass.callApi("GET", "ha_context_explorer_next/export/ui_context");
      await copyText(JSON.stringify(payload, null, 2));
    } catch (err) {
      this._setText("#exportCopyState", `${t(this._lang, "error")}: ${this._formatError(err)}`);
    } finally {
      if (button) button.disabled = false;
    }
  }

  async _loadDiagnostics() {
    this._setDiagnosticsCopyDisabled(true);
    try {
      const payload = await this._hass.callApi("GET", "ha_context_explorer_next/diagnostics");
      this._diagnosticsPayload = payload;
      this.querySelector("#diagnosticsState").textContent = t(this._lang, "diagnosticsReady");
      this.querySelector("#diagnosticsPreview").textContent = JSON.stringify(payload, null, 2);
      this._setDiagnosticsCopyDisabled(false);
    } catch (err) {
      this._diagnosticsPayload = null;
      this._setText("#diagnosticsState", `${t(this._lang, "error")}: ${this._formatError(err)}`);
      this._setText("#diagnosticsPreview", "{}");
    }
  }

  async load() {
    try {
      const payload = await this._hass.callApi("GET", "ha_context_explorer_next/summary");
      const entitiesTotal = payload.summary?.entities_total ?? 0;
      const unavailable = payload.summary?.entities_unavailable_or_unknown ?? 0;
      const batteryLow = payload.battery?.battery_entities_low ?? 0;
      const batteryCritical = payload.battery?.battery_entities_critical ?? 0;
      const topNoise = (payload.noise?.top_noisy_entities || []).slice(0, 5);

      this.querySelector("#kpis").innerHTML = [
        this._kpi(t(this._lang, "entities"), entitiesTotal),
        this._kpi(t(this._lang, "unavailable"), unavailable),
        this._kpi(t(this._lang, "criticalBattery"), batteryCritical),
        this._kpi(t(this._lang, "lowBattery"), batteryLow),
      ].join("");

      this.querySelector("#noise").innerHTML = topNoise
        .map((item) => `<li>${item.entity_id} — ${t(this._lang, "score")} ${item.noise_score}</li>`)
        .join("");


      const domainHealthRows = (payload.domain_health || [])
        .map((d) => `<tr><td>${d.domain}</td><td>${d.entities}</td><td>${d.noise_score}</td><td>${d.noise_density}</td><td>${this._riskBadge(d.risk)}</td></tr>`)
        .join("");
      this.querySelector("#domainHealthTable").innerHTML = `<thead><tr><th>Domain</th><th>Entities</th><th>Score</th><th>Density</th><th>Risk</th></tr></thead><tbody>${domainHealthRows}</tbody>`;

      const privacy = payload.privacy || {};
      this._renderPrivacyStatus(privacy);
      this._renderPrivacyCoverage(privacy.coverage || {});

      const recorderAdvice = payload.recorder_advice || {};
      this.querySelector("#recorder").textContent = JSON.stringify(recorderAdvice.yaml_preview || {}, null, 2);
      this._renderBatteryHealth(payload.battery || {});
      this._renderRecorderVolume(payload.recorder_volume || {});

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
          await this._writeClipboard(this.querySelector("#recorder").textContent || "");
          this.querySelector("#copyState").textContent = t(this._lang, "copied");
        } catch (e) {
          this.querySelector("#copyState").textContent = `${t(this._lang, "error")}: ${e}`;
        }
      };
      this.querySelector("#downloadKeyBtn").onclick = async () => this._downloadKeyBackup();
      this.querySelector("#rotateKeyBtn").onclick = async () => this._rotateKey();

      this.querySelector("#exportLevelSelect").onchange = async (e) => {
        this._exportLevel = e.target.value;
        await this._loadExport();
      };

      const copyText = async (text) => {
        try {
          await this._writeClipboard(text);
          this.querySelector("#exportCopyState").textContent = t(this._lang, "copied");
        } catch (e) {
          this.querySelector("#exportCopyState").textContent = `${t(this._lang, "error")}: ${this._formatError(e)}`;
        }
      };

      this.querySelector("#copyExportBtn").onclick = async () => copyText(JSON.stringify(this._exportPayload, null, 2));
      this.querySelector("#copyShortBtn").onclick = async () => copyText(JSON.stringify(this._exportPayload?.llm_context_short || {}, null, 2));
      this.querySelector("#copyFirstBtn").onclick = async () => copyText(JSON.stringify(this._exportPayload?.action_queue?.do_first || [], null, 2));
      this.querySelector("#copyUiContextBtn").onclick = async () => this._copyUiContext(copyText);
      this.querySelector("#loadDiagnosticsBtn").onclick = async () => this._loadDiagnostics();
      this.querySelector("#copyDiagnosticsBtn").onclick = async () => copyText(JSON.stringify(this._diagnosticsPayload || {}, null, 2));
      this._setDiagnosticsCopyDisabled(!this._diagnosticsPayload);

      this._renderRecorderTable(recorderAdvice);
      await this._loadExport();

      this.querySelector("#recs").innerHTML = (payload.recommendations || []).map((rec) => this._rec(rec)).join("");
    } catch (err) {
      this._showFatalError(err);
    }
  }
}

customElements.define("ha-context-explorer-next-panel", HaContextExplorerNextPanel);
