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
      this.render();
      this.load();
    }
  }

  render() {
    this.innerHTML = `
      <ha-card header="${t(this._lang, "title")}">
        <div style="padding:16px;display:grid;gap:12px;">
          <div id="kpis" style="display:flex;gap:8px;flex-wrap:wrap;"></div>
          <div>
            <h3>${t(this._lang, "topNoisy")}</h3>
            <ul id="noise"></ul>
          </div>
          <div>
            <h3>${t(this._lang, "recorderAdvice")}</h3>
            <button id="copyYamlBtn" type="button">${t(this._lang, "copyYaml")}</button>
            <div id="copyState" style="font-size:12px;color:var(--secondary-text-color);"></div>
            <table id="recorderTable" style="width:100%;border-collapse:collapse;"></table>
            <pre id="recorder"></pre>
          </div>
          <div>
            <h3>${t(this._lang, "recommendations")}</h3>
            <div id="recs" style="display:grid;gap:8px;"></div>
          </div>
        </div>
      </ha-card>
    `;
  }

  _kpi(label, value) {
    return `<div style="padding:8px 10px;border:1px solid var(--divider-color);border-radius:10px;"><b>${value}</b><br><small>${label}</small></div>`;
  }

  _rec(rec) {
    return `<div style="padding:10px;border:1px solid var(--divider-color);border-radius:10px;">
      <b>[${rec.severity.toUpperCase()}] ${rec.title}</b>
      <div>${rec.detail}</div>
      <small><b>${t(this._lang, "next")}:</b> ${rec.next_action || "-"}</small>
    </div>`;
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

      const recorderAdvice = payload.recorder_advice || {};
      this.querySelector("#recorder").textContent = JSON.stringify(recorderAdvice.yaml_preview || {}, null, 2);

      const rows = (recorderAdvice.entity_suggestions || []).slice(0, 8)
        .map((r) => `<tr><td>${r.entity_id}</td><td>${r.noise_score}</td><td>${r.risk_level}</td></tr>`)
        .join("");
      this.querySelector("#recorderTable").innerHTML = `<thead><tr><th>Entity</th><th>Score</th><th>Risk</th></tr></thead><tbody>${rows}</tbody>`;

      this.querySelector("#copyYamlBtn").onclick = async () => {
        try {
          await navigator.clipboard.writeText(this.querySelector("#recorder").textContent || "");
          this.querySelector("#copyState").textContent = t(this._lang, "copied");
        } catch (e) {
          this.querySelector("#copyState").textContent = `${t(this._lang, "error")}: ${e}`;
        }
      };

      this.querySelector("#recs").innerHTML = (payload.recommendations || [])
        .map((rec) => this._rec(rec))
        .join("");
    } catch (err) {
      this.innerHTML = `<ha-card><div style="padding:16px">${t(this._lang, "error")}: ${err}</div></ha-card>`;
    }
  }
}

customElements.define("ha-context-explorer-next-panel", HaContextExplorerNextPanel);
