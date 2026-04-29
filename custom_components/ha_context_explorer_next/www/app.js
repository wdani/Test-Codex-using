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
        <div style="padding:16px">
          <p><b>System summary, battery risk, noise hotspots, recommendations</b></p>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <pre id="summary">Loading summary...</pre>
            <pre id="recs">Loading recommendations...</pre>
          </div>
        </div>
      </ha-card>
    `;
  }

  async load() {
    try {
      const payload = await this._hass.callApi("GET", "api/ha_context_explorer_next/summary");
      this.querySelector("#summary").textContent = JSON.stringify({
        summary: payload.summary,
        battery: payload.battery,
        noise_top_5: (payload.noise?.top_noisy_entities || []).slice(0, 5)
      }, null, 2);
      this.querySelector("#recs").textContent = JSON.stringify(payload.recommendations, null, 2);
    } catch (err) {
      this.querySelector("#summary").textContent = `Error: ${err}`;
    }
  }
}

customElements.define("ha-context-explorer-next-panel", HaContextExplorerNextPanel);
