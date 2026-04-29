class HaContextExplorerNextPanel extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    if (!this._loaded) {
      this._loaded = true;
      this.render();
      this.load();
    }
  }

  render() {
    this.innerHTML = `
      <ha-card header="HA Context Explorer Next">
        <div style="padding:16px;display:grid;gap:12px;">
          <div id="kpis" style="display:flex;gap:8px;flex-wrap:wrap;"></div>
          <div>
            <h3>Top noisy entities</h3>
            <ul id="noise"></ul>
          </div>
          <div>
            <h3>Recommendations</h3>
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
      <small><b>Next:</b> ${rec.next_action || "-"}</small>
    </div>`;
  }

  async load() {
    try {
      const payload = await this._hass.callApi("GET", "api/ha_context_explorer_next/summary");
      const entitiesTotal = payload.summary?.entities_total ?? 0;
      const unavailable = payload.summary?.entities_unavailable_or_unknown ?? 0;
      const batteryLow = payload.battery?.battery_entities_low ?? 0;
      const topNoise = (payload.noise?.top_noisy_entities || []).slice(0, 5);

      this.querySelector("#kpis").innerHTML = [
        this._kpi("Entities", entitiesTotal),
        this._kpi("Unavailable/Unknown", unavailable),
        this._kpi("Low battery", batteryLow),
      ].join("");

      this.querySelector("#noise").innerHTML = topNoise
        .map((item) => `<li>${item.entity_id} — score ${item.noise_score}</li>`)
        .join("");

      this.querySelector("#recs").innerHTML = (payload.recommendations || [])
        .map((rec) => this._rec(rec))
        .join("");
    } catch (err) {
      this.innerHTML = `<ha-card><div style="padding:16px">Error: ${err}</div></ha-card>`;
    }
  }
}

customElements.define("ha-context-explorer-next-panel", HaContextExplorerNextPanel);
