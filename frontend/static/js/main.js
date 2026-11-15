/**
 * PyroNexa 26 - Main Application Controller
 * Handles navigation, state management, filter events, and asynchronous API calls.
 */

const PyroNexa = {
  state: {
    region: 'california',
    bbox: [-125.0, 32.0, -114.0, 42.5],
    sensor: 'ALL',
    confidence: 'all',
    startDate: '',
    endDate: '',
    activeSection: 'overview',
    currentPage: 1,
    perPage: 50,
    searchTerm: '',
    rawFires: [],
    overviewData: null,
    calendarData: null,
    historicalData: null,
    comparisonData: null,
    anomalyData: null,
    firmsStatus: null
  },

  init: function() {
    this.bindEvents();
    this.checkApiStatus();
    this.refreshAllData();
  },

  bindEvents: function() {
    // Navigation tab switching
    document.querySelectorAll('.nav-link-custom').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const targetSection = link.getAttribute('data-section');
        this.switchSection(targetSection);
      });
    });

    // Preset Region change
    const regionSelect = document.getElementById('filter-region');
    if (regionSelect) {
      regionSelect.addEventListener('change', (e) => {
        const val = e.target.value;
        this.state.region = val;
        this.state.currentPage = 1;
        this.refreshAllData();
      });
    }

    // Sensor change
    const sensorSelect = document.getElementById('filter-sensor');
    if (sensorSelect) {
      sensorSelect.addEventListener('change', (e) => {
        this.state.sensor = e.target.value;
        this.state.currentPage = 1;
        this.refreshAllData();
      });
    }

    // Confidence change
    const confSelect = document.getElementById('filter-confidence');
    if (confSelect) {
      confSelect.addEventListener('change', (e) => {
        this.state.confidence = e.target.value;
        this.state.currentPage = 1;
        this.refreshAllData();
      });
    }

    // Date inputs
    const startInput = document.getElementById('filter-start-date');
    const endInput = document.getElementById('filter-end-date');
    if (startInput) {
      startInput.addEventListener('change', (e) => {
        this.state.startDate = e.target.value;
      });
    }
    if (endInput) {
      endInput.addEventListener('change', (e) => {
        this.state.endDate = e.target.value;
      });
    }

    // Apply Filter Button
    const applyBtn = document.getElementById('btn-apply-filters');
    if (applyBtn) {
      applyBtn.addEventListener('click', () => {
        this.state.currentPage = 1;
        this.refreshAllData();
      });
    }

    // Reset Filter Button
    const resetBtn = document.getElementById('btn-reset-filters');
    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        this.resetFilters();
      });
    }

    // CSV Export Button
    const exportBtn = document.getElementById('btn-export-csv');
    if (exportBtn) {
      exportBtn.addEventListener('click', () => {
        this.triggerCsvExport();
      });
    }

    // Table search input
    const searchInput = document.getElementById('table-search-input');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.state.searchTerm = e.target.value.toLowerCase().trim();
        PyroExplorer.renderTable();
      });
    }
  },

  switchSection: function(sectionId) {
    this.state.activeSection = sectionId;

    // Update nav links
    document.querySelectorAll('.nav-link-custom').forEach(link => {
      if (link.getAttribute('data-section') === sectionId) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    });

    // Update section visibility
    document.querySelectorAll('.dashboard-section').forEach(sec => {
      if (sec.id === `section-${sectionId}`) {
        sec.classList.add('active-section');
      } else {
        sec.classList.remove('active-section');
      }
    });

    // Trigger map invalidation if opening map section
    if (sectionId === 'map') {
      setTimeout(() => {
        if (window.PyroMap && window.PyroMap.map) {
          window.PyroMap.map.invalidateSize();
        }
      }, 150);
    }
  },

  buildQueryParams: function() {
    const p = new URLSearchParams();
    if (this.state.region) p.set('region', this.state.region);
    if (this.state.sensor) p.set('sensor', this.state.sensor);
    if (this.state.confidence) p.set('confidence', this.state.confidence);
    if (this.state.startDate) p.set('start_date', this.state.startDate);
    if (this.state.endDate) p.set('end_date', this.state.endDate);
    p.set('page', this.state.currentPage);
    p.set('per_page', this.state.perPage);
    return p.toString();
  },

  checkApiStatus: function() {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => {
        this.state.firmsStatus = data.nasa_firms;
        this.updateApiStatusUI(data.nasa_firms);
      })
      .catch(err => {
        console.error('Error checking API status:', err);
      });
  },

  updateApiStatusUI: function(status) {
    const pill = document.getElementById('api-status-pill');
    const label = document.getElementById('api-status-label');
    const modalText = document.getElementById('modal-status-text');

    if (modalText) {
      if (status.operational && status.configured) {
        modalText.innerHTML = `<span class="text-success fw-bold">&check; Connected to NASA FIRMS Live API</span><br><span class="text-muted small">${status.message}</span>`;
      } else {
        modalText.innerHTML = `<span class="text-warning fw-bold">&#9888; Simulation Mode (Sample Data)</span><br><span class="text-muted small">${status.message}</span>`;
      }
    }

    if (!pill || !label) return;

    if (status.operational && status.configured) {
      pill.className = 'status-pill live-mode';
      label.textContent = 'NASA FIRMS LIVE API';
      pill.title = 'Connected to NASA FIRMS production endpoints';
    } else {
      pill.className = 'status-pill sample-mode';
      label.textContent = 'SIMULATION MODE (Sample Data)';
      pill.title = status.message || 'Operating on verified NASA scientific sample datasets';
    }
  },

  showLoading: function(show) {
    const overlay = document.getElementById('global-loading');
    if (overlay) {
      if (show) overlay.classList.add('active');
      else overlay.classList.remove('active');
    }
  },

  refreshAllData: function() {
    this.showLoading(true);
    const query = this.buildQueryParams();

    // Parallel fetch of main endpoints
    Promise.all([
      fetch(`/api/analytics/overview?${query}`).then(r => r.json()),
      fetch(`/api/fires?${query}`).then(r => r.json()),
      fetch(`/api/analytics/calendar?${query}`).then(r => r.json()),
      fetch(`/api/analytics/historical?${query}`).then(r => r.json()),
      fetch(`/api/analytics/comparison?${query}`).then(r => r.json()),
      fetch(`/api/analytics/anomalies?${query}`).then(r => r.json())
    ])
    .then(([overview, fires, calendar, historical, comparison, anomalies]) => {
      this.state.overviewData = overview.data;
      this.state.rawFires = fires.data || [];
      this.state.calendarData = calendar.data;
      this.state.historicalData = historical.data;
      this.state.comparisonData = comparison.data;
      this.state.anomalyData = anomalies.data;

      // Update UI components
      this.renderOverview();
      if (window.PyroMap) window.PyroMap.updateFires(this.state.rawFires);
      if (window.PyroCharts) {
        window.PyroCharts.renderAllCharts(
          this.state.overviewData,
          this.state.calendarData,
          this.state.historicalData,
          this.state.comparisonData,
          this.state.anomalyData
        );
      }
      if (window.PyroExplorer) {
        window.PyroExplorer.updateData(this.state.rawFires, fires.pagination);
      }
    })
    .catch(err => {
      console.error('Error refreshing dashboard data:', err);
      alert('Failed to load satellite fire data. Check console for details.');
    })
    .finally(() => {
      this.showLoading(false);
    });
  },

  renderOverview: function() {
    const data = this.state.overviewData;
    if (!data) return;

    // Update KPI numbers
    document.getElementById('kpi-total-detections').textContent = (data.total_detections || 0).toLocaleString();
    document.getElementById('kpi-modis-detections').textContent = (data.modis_detections || 0).toLocaleString();
    document.getElementById('kpi-viirs-detections').textContent = (data.viirs_detections || 0).toLocaleString();
    document.getElementById('kpi-total-frp').textContent = `${(data.total_frp_mw || 0).toLocaleString()} MW`;
    document.getElementById('kpi-total-area').textContent = `${(data.total_footprint_km2 || 0).toLocaleString()} km²`;
    
    // VIIRS to MODIS ratio pill
    const ratioEl = document.getElementById('kpi-viirs-ratio');
    if (ratioEl) {
      if (data.viirs_to_modis_ratio !== null) {
        ratioEl.textContent = `${data.viirs_to_modis_ratio}x`;
      } else {
        ratioEl.textContent = 'N/A';
      }
    }

    // Satellite breakdown list
    const satList = document.getElementById('overview-satellites-list');
    if (satList && data.satellite_breakdown) {
      satList.innerHTML = Object.entries(data.satellite_breakdown)
        .map(([sat, count]) => `
          <div class="d-flex justify-content-between align-items-center py-1 border-bottom border-secondary border-opacity-25">
            <span class="text-light small">${sat}</span>
            <span class="badge bg-dark border border-secondary">${count.toLocaleString()}</span>
          </div>
        `).join('');
    }

    // Confidence breakdown list
    const confList = document.getElementById('overview-confidence-list');
    if (confList && data.confidence_breakdown) {
      const cb = data.confidence_breakdown;
      confList.innerHTML = `
        <div class="d-flex justify-content-between py-1 border-bottom border-secondary border-opacity-25">
          <span class="text-success small">High Confidence (&ge;80% / 'h')</span>
          <span class="badge bg-success bg-opacity-25 text-success">${(cb.high || 0).toLocaleString()}</span>
        </div>
        <div class="d-flex justify-content-between py-1 border-bottom border-secondary border-opacity-25">
          <span class="text-warning small">Nominal Confidence (30-79% / 'n')</span>
          <span class="badge bg-warning bg-opacity-25 text-warning">${(cb.nominal || 0).toLocaleString()}</span>
        </div>
        <div class="d-flex justify-content-between py-1">
          <span class="text-muted small">Low Confidence (&lt;30% / 'l')</span>
          <span class="badge bg-secondary bg-opacity-25 text-muted">${(cb.low || 0).toLocaleString()}</span>
        </div>
      `;
    }

    // Date bounds
    const dateSpanEl = document.getElementById('overview-date-span');
    if (dateSpanEl && data.date_span) {
      dateSpanEl.textContent = `${data.date_span.min_date || 'N/A'} to ${data.date_span.max_date || 'N/A'} (${data.date_span.total_days} days)`;
    }
  },

  resetFilters: function() {
    this.state.region = 'california';
    this.state.sensor = 'ALL';
    this.state.confidence = 'all';
    this.state.startDate = '';
    this.state.endDate = '';
    this.state.currentPage = 1;

    document.getElementById('filter-region').value = 'california';
    document.getElementById('filter-sensor').value = 'ALL';
    document.getElementById('filter-confidence').value = 'all';
    document.getElementById('filter-start-date').value = '';
    document.getElementById('filter-end-date').value = '';

    this.refreshAllData();
  },

  triggerCsvExport: function() {
    const query = this.buildQueryParams();
    window.location.href = `/api/export/csv?${query}`;
  }
};

document.addEventListener('DOMContentLoaded', () => {
  PyroNexa.init();
});
