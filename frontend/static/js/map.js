/**
 * PyroNexa 26 - Interactive Leaflet Fire Map Controller
 * Renders satellite active fire detections with sensor-specific color encoding,
 * FRP radius scaling, rich NASA telemetry popups, base layer toggles (OSM, Carto Dark, Esri),
 * AOI bounding box overlays, and tile error fallback handling.
 */

const PyroMap = {
  map: null,
  baseLayers: {},
  modisLayer: null,
  viirsLayer: null,
  highFrpLayer: null,
  aoiPolygonLayer: null,
  scaleByFRP: true,
  currentFires: [],
  currentBbox: null,

  init: function() {
    const mapEl = document.getElementById('map-container');
    if (!mapEl || this.map) return;

    // Initialize Leaflet map with standard OpenStreetMap as primary base layer
    this.map = L.map('map-container', {
      center: [37.2, -119.5],
      zoom: 6,
      minZoom: 2,
      maxZoom: 18,
      zoomControl: true
    });

    // 1. OpenStreetMap Standard (100% Free, reliable worldwide, no API key required)
    const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors | NASA FIRMS Active Fire',
      maxZoom: 19
    });

    // 2. CartoDB Dark Matter
    const cartoDarkLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> | NASA FIRMS',
      subdomains: 'abcd',
      maxZoom: 19
    });

    // 3. Esri World Imagery (Satellite)
    const esriSatellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      attribution: 'Tiles &copy; Esri, Earthstar Geographics | NASA FIRMS',
      maxZoom: 18
    });

    // Attach tile error listeners to all base layers
    [osmLayer, cartoDarkLayer, esriSatellite].forEach(layer => {
      layer.on('tileerror', (error) => {
        console.warn('Map tile loading issue detected:', error);
        const fallbackBanner = document.getElementById('map-tile-fallback-banner');
        if (fallbackBanner) fallbackBanner.style.display = 'block';
      });
    });

    // Default active base layer: OpenStreetMap Standard
    osmLayer.addTo(this.map);

    this.baseLayers = {
      'OpenStreetMap (Standard)': osmLayer,
      'Dark Matter (Aerospace)': cartoDarkLayer,
      'Satellite Imagery (Esri)': esriSatellite
    };

    // Overlay Layer Groups
    this.modisLayer = L.layerGroup().addTo(this.map);
    this.viirsLayer = L.layerGroup().addTo(this.map);
    this.highFrpLayer = L.layerGroup();
    this.coincidentLayer = L.layerGroup();
    this.aoiPolygonLayer = L.layerGroup().addTo(this.map);

    const overlays = {
      '<span class="badge-modis px-2 py-0.5 rounded">MODIS (Terra/Aqua 1km)</span>': this.modisLayer,
      '<span class="badge-viirs px-2 py-0.5 rounded">VIIRS (NOAA-20/21 375m)</span>': this.viirsLayer,
      '<span class="badge bg-danger bg-opacity-25 text-danger px-2 py-0.5 rounded">Intense Fires (FRP &ge; 50 MW)</span>': this.highFrpLayer,
      '<span class="badge bg-info bg-opacity-25 text-info px-2 py-0.5 rounded">&#10003; Coincident Clusters (&le;60min)</span>': this.coincidentLayer,
      '<span class="text-info small px-1">Selected AOI Boundary</span>': this.aoiPolygonLayer
    };

    L.control.layers(this.baseLayers, overlays, { position: 'topright', collapsed: false }).addTo(this.map);

    // Map mousemove inspector
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

    // FRP toggle listener
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

  updateFires: function(fires, bbox) {
    this.currentFires = fires || [];
    this.currentBbox = bbox || null;
    if (!this.map) {
      this.init();
    }
    this.renderAoiPolygon();
    this.renderFires();
    this.fitBounds();
    this.updateStats();
  },

  renderAoiPolygon: function() {
    if (!this.aoiPolygonLayer) return;
    this.aoiPolygonLayer.clearLayers();

    if (this.currentBbox && this.currentBbox.length === 4) {
      const [minLon, minLat, maxLon, maxLat] = this.currentBbox;
      const bounds = [[minLat, minLon], [maxLat, maxLon]];
      const rect = L.rectangle(bounds, {
        color: '#38bdf8',
        weight: 1.5,
        dashArray: '5, 5',
        fillOpacity: 0.04
      });
      rect.bindTooltip('Area of Interest Boundary', { sticky: true });
      this.aoiPolygonLayer.addLayer(rect);
    }
  },

  renderFires: function() {
    if (!this.modisLayer || !this.viirsLayer || !this.highFrpLayer) return;

    this.modisLayer.clearLayers();
    this.viirsLayer.clearLayers();
    this.highFrpLayer.clearLayers();
    if (this.coincidentLayer) this.coincidentLayer.clearLayers();

    const emptyOverlay = document.getElementById('map-empty-overlay');
    if (emptyOverlay) {
      if (this.currentFires.length === 0) {
        emptyOverlay.style.display = 'flex';
      } else {
        emptyOverlay.style.display = 'none';
      }
    }

    this.currentFires.forEach(pt => {
      const isModis = pt.instrument === 'MODIS';
      const color = isModis ? '#2563eb' : '#ea580c';
      const fillColor = isModis ? '#60a5fa' : '#fb923c';

      // Marker radius: either fixed or scaled by Fire Radiative Power
      let radius = 4;
      if (this.scaleByFRP && pt.frp) {
        radius = Math.min(18, Math.max(3.5, Math.sqrt(pt.frp) * 0.85));
      }

      const marker = L.circleMarker([pt.latitude, pt.longitude], {
        radius: radius,
        color: color,
        weight: 1.5,
        fillColor: fillColor,
        fillOpacity: 0.8
      });

      // Rich popup with full telemetry
      const popupContent = `
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 0.82rem; min-width: 220px; color: #0f172a;">
          <div style="font-weight: 700; font-size: 0.92rem; margin-bottom: 4px; display: flex; justify-content: space-between; align-items: center;">
            <span>${pt.instrument} &bull; ${pt.satellite}</span>
            <span style="font-size: 0.72rem; padding: 2px 6px; border-radius: 4px; font-weight: 600; background: ${isModis ? '#dbeafe; color: #1d4ed8;' : '#ffedd5; color: #c2410c;'}">
              ${isModis ? '1 km nadir' : '375 m nadir'}
            </span>
          </div>
          <hr style="margin: 4px 0 8px 0; border: none; border-top: 1px solid #cbd5e1;">
          <div style="margin-bottom: 3px;"><strong>Acquisition:</strong> ${pt.acq_date} @ ${pt.acq_time} UTC</div>
          <div style="margin-bottom: 3px;"><strong>Coordinates:</strong> ${pt.latitude.toFixed(4)}°, ${pt.longitude.toFixed(4)}°</div>
          <div style="margin-bottom: 3px;"><strong>Confidence:</strong> <span style="text-transform: capitalize; font-weight: 600;">${pt.confidence_cat}</span> (${pt.confidence_pct}%)</div>
          <div style="margin-bottom: 3px;"><strong>FRP:</strong> <span style="font-weight: 700; color: #dc2626;">${pt.frp.toFixed(1)} MW</span></div>
          <div style="margin-bottom: 3px;"><strong>Footprint Area:</strong> ${pt.footprint_area_km2.toFixed(3)} km²</div>
          <div style="margin-bottom: 3px;"><strong>Brightness Temp:</strong> ${pt.brightness.toFixed(1)} K</div>
          ${pt.is_coincident ? `
          <div style="margin-top: 4px; padding: 3px 6px; border-radius: 4px; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.4); font-size: 0.72rem; color: #0284c7;">
            <strong>&#10003; Simultaneous Multi-Sensor Cluster:</strong> ${pt.cluster_id}
          </div>
          ` : ''}
          <div style="font-size: 0.72rem; color: #64748b; margin-top: 4px; border-top: 1px dashed #e2e8f0; padding-top: 4px;">
            Grid Cell: ${pt.grid_cell_id} | Overpass: ${pt.daynight === 'D' ? 'Day (Solar Peak)' : 'Night'}
          </div>
        </div>
      `;
      marker.bindPopup(popupContent);

      if (isModis) {
        this.modisLayer.addLayer(marker);
      } else {
        this.viirsLayer.addLayer(marker);
      }

      if (pt.frp >= 50.0) {
        this.highFrpLayer.addLayer(marker);
      }

      if (pt.is_coincident && this.coincidentLayer) {
        const ring = L.circleMarker([pt.latitude, pt.longitude], {
          radius: radius + 4,
          color: '#38bdf8',
          weight: 2,
          fillOpacity: 0.0,
          dashArray: '3, 3'
        });
        ring.bindTooltip(`Simultaneous Cluster: ${pt.cluster_id}`, { sticky: true });
        this.coincidentLayer.addLayer(ring);
      }
    });
  },

  fitBounds: function() {
    if (!this.map) return;

    if (this.currentFires.length > 0) {
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
        ], { padding: [35, 35], maxZoom: 12 });
        return;
      }
    }

    if (this.currentBbox && this.currentBbox.length === 4) {
      const [minLon, minLat, maxLon, maxLat] = this.currentBbox;
      this.map.fitBounds([[minLat, minLon], [maxLat, maxLon]], { padding: [20, 20] });
    }
  },

  updateStats: function() {
    const countEl = document.getElementById('map-point-count');
    if (countEl) {
      countEl.textContent = `${this.currentFires.length.toLocaleString()} active fire hotspots plotted`;
    }
  }
};

window.PyroMap = PyroMap;
