/* Müll-Erinnerung Lovelace card. */
class MuellErinnerungCard extends HTMLElement {
  setConfig(config) {
    if (!config || !config.entity) throw new Error("Bitte entity angeben, z. B. binary_sensor.muellerinnerung_aktiv");
    this._config = config;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._config || !this.isConnected) return;
    this.render();
  }

  connectedCallback() { if (this._hass) this.render(); }

  render() {
    const hass = this._hass;
    const active = hass.states[this._config.entity];
    const sensorId = this._config.sensor || "sensor.muellerinnerung_naechste_abholung";
    const sensor = hass.states[sensorId];
    const due = sensor?.attributes?.muellarten || [];
    const visible = this._config.show_when_inactive || active?.state === "on";
    if (!visible && !this._config.show_when_inactive) { this.innerHTML = ""; return; }
    this.innerHTML = `
      <ha-card>
        <div class="wrap" style="${visible ? "" : "display:none"}">
          <div class="heading"><ha-icon icon="mdi:trash-can"></ha-icon><span>Müllabholung morgen</span></div>
          <p>Folgende Müllarten müssen für die morgige Abholung rausgestellt werden:</p>
          <strong class="items">${this.escape(due.length ? due.join(", ") : (sensor?.state || "Keine"))}</strong>
          <div class="buttons">
            <button id="snooze"><ha-icon icon="mdi:clock-outline"></ha-icon> Später</button>
            <button id="done"><ha-icon icon="mdi:check-circle"></ha-icon> Erledigt</button>
          </div>
        </div>
        <style>
          .wrap{padding:16px}.heading{display:flex;gap:12px;align-items:center;font-size:1.2em;font-weight:600}
          p{line-height:1.5}.items{display:block;margin:10px 0 16px}
          .buttons{display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap}
          ha-icon{vertical-align:middle;--mdc-icon-size:18px}
          button{display:inline-flex;gap:6px;align-items:center;padding:8px 14px;border:none;border-radius:18px;cursor:pointer;font:inherit;background:var(--secondary-background-color);color:var(--primary-text-color)}
          button#done{background:var(--primary-color);color:var(--text-primary-color)}
        </style>
      </ha-card>`;
    this.querySelector("#snooze")?.addEventListener("click", () => this.callButton("button.muellerinnerung_spaeter"));
    this.querySelector("#done")?.addEventListener("click", () => this.callButton("button.muellerinnerung_erledigt"));
  }

  callButton(entity_id) {
    if (!this._hass.states[entity_id]) {
      const suffix = entity_id.endsWith("spaeter") ? "spaeter" : "erledigt";
      const found = Object.keys(this._hass.states).find(id => id.startsWith("button.muellerinnerung") && id.endsWith(suffix));
      if (found) entity_id = found;
    }
    this._hass.callService("button", "press", {entity_id});
  }

  escape(value) {
    return String(value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  }

  getCardSize() { return 2; }
}
customElements.define("muell-erinnerung-card", MuellErinnerungCard);
window.customCards = window.customCards || [];
window.customCards.push({type:"muell-erinnerung-card", name:"Müll-Erinnerung", description:"Erinnerung mit Später- und Erledigt-Buttons."});
MuellErinnerungCard.getStubConfig = () => ({entity: "binary_sensor.muellerinnerung_aktiv", sensor: "sensor.muellerinnerung_naechste_abholung", show_when_inactive: true});
