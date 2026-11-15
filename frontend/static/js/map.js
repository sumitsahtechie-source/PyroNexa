/**
 * PyroNexa 26 - Interactive Leaflet Fire Map Controller
 * Renders satellite active fire detections with sensor-specific color encoding,
 * FRP radius scaling, rich telemetry popups, and spatial layer controls.
 */

const PyroMap = {
  map: null,
  modisLayer: null,
  viirsLayer: null,
  scaleByFRP: true,
  currentFires: [],

  init: function() {
    const mapEl = document.getElementById('map-container');
    if (!mapEl || this.map) return;

    // Default center (California)
    this.map = L.map('map-container', {
      center: [37.2, -119.5],
      zoom: 6,
      minZoom: 2,
      maxZoom: 18,
      zoomControl: true
    });

    // Dark Matter basemap tiles (CartoDB)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | NASA FIRMS',
      subdomains: 'abcd',
      maxZoom: 19
    }).addTo(this.map);

    // Layer groups
    this.modisLayer = L.layerGroup().addTo(this.map);
    this.viirsLayer = L.layerGroup().addTo(this.map);

    // Add layer control
    const overlays = {
      '<span class="badge-modis px-2 py-0.5 rounded">MODIS (Terra/Aqua 1km)</span>': this.modisLayer,
      '<span class="badge-viirs px-2 py-0.5 rounded">VIIRS (NOAA-20/21 375m)</span>': this.viirsLayer
    };
    L.control.layers(null, overlays, { position: 'topright', collapsed: false }).addTo(this.map);

    // Map move listener to update coordinates in inspector
    this.map.on('mousemove', (e) => {
      const coordEl = document.getElementById('map-coord-inspector');
      if (coordEl) {
        coordEl.textContent = `Lat: ${e.latlng.lat.toFixed(4)}°, Lon: ${e.latlng.lng.toFixed(4)}°`;
      }
    });

    this.map.on('zoomend', () => {
      const zoomEl = document.getElementById('map-zoom-inspector');
      if (zoomEl) {
        zoomEl.textContent = `Zoom: ${this.map.getZoom()}`;
      }
    });

    // FRP toggle
    const frpToggle = document.getElementById('map-toggle-frp-scale');
    if (frpToggle) {
      frpToggle.addEventListener('change', (e) => {
        this.scaleByFRP = e.target.checked;
        this.renderFires();
      });
    }

    // Fit bounds button
    const fitBtn = document.getElementById('map-btn-fit');
    if (fitBtn) {
      fitBtn.addEventListener('click', () => {
        this.fitBounds();
      });
    }
  },

  updateFires: function(fires) {
    this.currentFires = fires || [];
    if (!this.map) {
      this.init();
    }
    this.renderFires();
    this.fitBounds();
    this.updateStats();
  },

  renderFires: function() {
    if (!this.modisLayer || !this.viirsLayer) return;

    this.modisLayer.clearLayers();
    this.viirsLayer.clearLayers();

    this.currentFires.forEach(pt => {
      const isModis = pt.instrument === 'MODIS';
      const color = isModis ? '#3b82f6' : '#f97316';
      const fillColor = isModis ? '#60a5fa' : '#fb923c';

      // Radius calculation: either fixed or scaled by FRP
      let radius = 4;
      if (this.scaleByFRP && pt.frp) {
        radius = Math.min(16, Math.max(3, Math.sqrt(pt.frp) * 0.8));
      }

      const marker = L.circleMarker([pt.latitude, pt.longitude], {
        radius: radius,
        color: color,
        weight: 1.5,
        fillColor: fillColor,
        fillOpacity: 0.75
      });

      // Rich popup with NASA telemetry
      const popupContent = `
        <div style="font-family: inherit; font-size: 0.82rem; min-width: 210px; color: #1e293b;">
          <div style="font-weight: 700; font-size: 0.9rem; margin-bottom: 4px; display: flex; justify-content: space-between; align-items: center;">
            <span>${pt.instrument} &bull; ${pt.satellite}</span>
            <span style="font-size: 0.7rem; padding: 2px 6px; border-radius: 4px; background: ${isModis ? '#dbeafe; color: #1d4ed8' : '#ffedd5; color: #c2410c'};">
              ${pt.instrument === 'MODIS' ? '1 km' : '375 m'}
            </span>
          </div>
          <hr style="margin: 4px 0 8px 0; border-top: 1px solid #cbd5e1;">
          <div style="margin-bottom: 3px;"><strong>Acquisition:</strong> ${pt.acq_date} @ ${pt.acq_time} UTC</div>
          <div style="margin-bottom: 3px;"><strong>Coordinates:</strong> ${pt.latitude.toFixed(4)}°, ${pt.longitude.toFixed(4)}°</div>
          <div style="margin-bottom: 3px;"><strong>Confidence:</strong> <span style="text-transform: capitalize; font-weight: 600;">${pt.confidence_cat}</span> (${pt.confidence_pct}%)</div>
          <div style="margin-bottom: 3px;"><strong>FRP:</strong> <span style="font-weight: 700; color: #dc2626;">${pt.frp.toFixed(1)} MW</span></div>
          <div style="margin-bottom: 3px;"><strong>Footprint Area:</strong> ${pt.footprint_area_km2.toFixed(3)} km²</div>
          <div style="margin-bottom: 3px;"><strong>Brightness Temp:</strong> ${pt.brightness.toFixed(1)} K</div>
          <div style="font-size: 0.72rem; color: #64748b; margin-top: 4px;">Cell: ${pt.grid_cell_id} | Day/Night: ${pt.daynight}</div>
        </div>
      `;
      marker.bindPopup(popupContent);

      if (isModis) {
        this.modisLayer.addLayer(marker);
      } else {
        this.viirsLayer.addLayer(marker);
      }
    });
  },

  fitBounds: function() {
    if (!this.map || this.currentFires.length === 0) return;

    const lats = this.currentFires.map(p => p.latitude);
    const lons = this.currentFires.map(p => p.longitude);
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLon = Math.min(...lons);
    const maxLon = Math.max(...lons);

    if (minLat !== maxLat && minLon !== maxLon) {
      this.map.fitBounds([
        [minLat, minLon],
        [maxLat, maxLon]
      ], { padding: [30, 30], maxZoom: 12 });
    } else {
      this.map.setView([minLat, minLon], 8);
    }
  },

  updateStats: function() {
    const countEl = document.getElementById('map-point-count');
    if (countEl) {
      countEl.textContent = `${this.currentFires.length.toLocaleString()} hotspots plotted`;
    }
  }
};

window.PyroMap = PyroMap;
