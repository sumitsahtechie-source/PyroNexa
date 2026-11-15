/**
 * PyroNexa 26 - Analytics & Data Explorer Controller
 * Handles table sorting, live search filtering, pagination,
 * and statistical anomaly tables.
 */

const PyroExplorer = {
  allFires: [],
  filteredFires: [],
  currentPage: 1,
  pageSize: 25,
  sortCol: 'acq_date',
  sortAsc: false,

  updateData: function(fires, pagination) {
    this.allFires = fires || [];
    this.applyFilterAndSort();
    this.renderAnomalyTable();
  },

  applyFilterAndSort: function() {
    const term = (PyroNexa.state.searchTerm || '').toLowerCase();
    
    // Filter
    if (!term) {
      this.filteredFires = [...this.allFires];
    } else {
      this.filteredFires = this.allFires.filter(f => {
        return (
          f.acq_date.includes(term) ||
          f.satellite.toLowerCase().includes(term) ||
          f.instrument.toLowerCase().includes(term) ||
          f.confidence_cat.toLowerCase().includes(term) ||
          f.latitude.toString().includes(term) ||
          f.longitude.toString().includes(term) ||
          f.grid_cell_id.toLowerCase().includes(term)
        );
      });
    }

    // Sort
    this.filteredFires.sort((a, b) => {
      let va = a[this.sortCol];
      let vb = b[this.sortCol];

      if (typeof va === 'string') {
        va = va.toLowerCase();
        vb = vb.toLowerCase();
      }

      if (va < vb) return this.sortAsc ? -1 : 1;
      if (va > vb) return this.sortAsc ? 1 : -1;
      return 0;
    });

    this.renderTable();
  },

  setSort: function(colName) {
    if (this.sortCol === colName) {
      this.sortAsc = !this.sortAsc;
    } else {
      this.sortCol = colName;
      this.sortAsc = false;
    }
    this.applyFilterAndSort();
  },

  renderTable: function() {
    const tbody = document.getElementById('table-fires-body');
    const countEl = document.getElementById('table-records-count');
    const paginationEl = document.getElementById('table-pagination-controls');
    if (!tbody) return;

    if (countEl) {
      countEl.textContent = `Showing ${this.filteredFires.length.toLocaleString()} matching records (of ${this.allFires.length.toLocaleString()} loaded)`;
    }

    const total = this.filteredFires.length;
    const totalPages = Math.max(1, Math.ceil(total / this.pageSize));
    if (this.currentPage > totalPages) this.currentPage = 1;

    const startIdx = (this.currentPage - 1) * this.pageSize;
    const pageData = this.filteredFires.slice(startIdx, startIdx + this.pageSize);

    if (pageData.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="10" class="text-center py-4 text-muted">
            <em>No fire observations match current filter criteria.</em>
          </td>
        </tr>
      `;
      if (paginationEl) paginationEl.innerHTML = '';
      return;
    }

    tbody.innerHTML = pageData.map((pt, idx) => {
      const isModis = pt.instrument === 'MODIS';
      const badgeClass = isModis ? 'badge-modis' : 'badge-viirs';
      const confBadge = pt.confidence_cat === 'high' 
        ? 'badge-normal' 
        : (pt.confidence_cat === 'nominal' ? 'badge-elevated' : 'badge bg-secondary bg-opacity-25 text-muted');

      return `
        <tr onclick="PyroExplorer.showDetails(${startIdx + idx})" style="cursor: pointer;" title="Click to view full hotspot details">
          <td><span class="badge ${badgeClass}">${pt.instrument}</span></td>
          <td><strong>${pt.satellite}</strong></td>
          <td><code>${pt.acq_date}</code></td>
          <td>${pt.acq_time} UTC</td>
          <td>${pt.latitude.toFixed(4)}°</td>
          <td>${pt.longitude.toFixed(4)}°</td>
          <td><span class="badge ${confBadge}">${pt.confidence_cat}</span> <small class="text-muted">(${pt.confidence_pct}%)</small></td>
          <td><strong class="text-danger">${pt.frp.toFixed(1)}</strong></td>
          <td>${pt.footprint_area_km2.toFixed(3)}</td>
          <td><small class="text-dim">${pt.grid_cell_id}</small></td>
        </tr>
      `;
    }).join('');

    // Pagination controls
    if (paginationEl) {
      paginationEl.innerHTML = `
        <div class="d-flex align-items-center justify-content-between w-100">
          <span class="text-muted small">Page ${this.currentPage} of ${totalPages}</span>
          <div class="btn-group">
            <button class="btn btn-sm btn-pyro-outline" ${this.currentPage <= 1 ? 'disabled' : ''} onclick="PyroExplorer.changePage(${this.currentPage - 1})">&laquo; Prev</button>
            <button class="btn btn-sm btn-pyro-outline" ${this.currentPage >= totalPages ? 'disabled' : ''} onclick="PyroExplorer.changePage(${this.currentPage + 1})">Next &raquo;</button>
          </div>
        </div>
      `;
    }
  },

  changePage: function(newPage) {
    this.currentPage = newPage;
    this.renderTable();
  },

  showDetails: function(index) {
    const pt = this.filteredFires[index];
    if (!pt) return;
    const body = document.getElementById('record-details-modal-body');
    if (!body) return;
    const isModis = pt.instrument === 'MODIS';
    body.innerHTML = `
      <div class="row g-3">
        <div class="col-6">
          <div class="text-dim small">Sensor &bull; Satellite</div>
          <div class="fw-bold text-white fs-6">${pt.instrument} &bull; ${pt.satellite}</div>
          <div class="small text-info">${isModis ? '1,000 m nominal nadir' : '375 m I-band nadir'}</div>
        </div>
        <div class="col-6">
          <div class="text-dim small">Acquisition Timestamp</div>
          <div class="fw-bold text-white fs-6">${pt.acq_date} @ ${pt.acq_time} UTC</div>
          <div class="small text-muted">${pt.daynight === 'D' ? 'Daytime (Solar Peak)' : 'Nighttime'}</div>
        </div>
        <div class="col-6">
          <div class="text-dim small">Geographic Coordinates</div>
          <div class="fw-bold text-white">${pt.latitude.toFixed(5)}°, ${pt.longitude.toFixed(5)}°</div>
          <div class="small text-dim">Cell: ${pt.grid_cell_id}</div>
        </div>
        <div class="col-6">
          <div class="text-dim small">Harmonized Confidence</div>
          <div class="fw-bold text-warning text-capitalize">${pt.confidence_cat} (${pt.confidence_pct}%)</div>
          <div class="small text-dim">Raw FIRMS Value: '${pt.confidence_raw}'</div>
        </div>
        <div class="col-6">
          <div class="text-dim small">Fire Radiative Power (FRP)</div>
          <div class="fw-bold text-danger fs-5">${pt.frp.toFixed(1)} MW</div>
        </div>
        <div class="col-6">
          <div class="text-dim small">Ground Footprint Area</div>
          <div class="fw-bold text-white fs-5">${pt.footprint_area_km2.toFixed(3)} km²</div>
          <div class="small text-dim">Scan: ${pt.scan || '1.0'} km &times; Track: ${pt.track || '1.0'} km</div>
        </div>
        <div class="col-12 border-top border-secondary border-opacity-25 pt-2">
          <div class="text-dim small">Thermal Brightness: <strong class="text-white">${pt.brightness.toFixed(1)} K</strong></div>
        </div>
      </div>
    `;
    const modalEl = document.getElementById('recordDetailsModal');
    if (modalEl && window.bootstrap) {
      const modal = new bootstrap.Modal(modalEl);
      modal.show();
    }
  },

  renderAnomalyTable: function() {
    const data = PyroNexa.state.anomalyData;
    const tbody = document.getElementById('anomaly-table-body');
    if (!tbody || !data || !data.monthly_anomalies) return;

    tbody.innerHTML = data.monthly_anomalies.map(a => `
      <tr>
        <td><strong>${a.year_month}</strong></td>
        <td>${a.count.toLocaleString()}</td>
        <td>${a.baseline_median.toLocaleString()}</td>
        <td><strong>${a.z_score}</strong></td>
        <td>${a.z_mad}</td>
        <td>${a.pct_of_baseline}%</td>
        <td><span class="badge badge-${a.severity}">${a.severity_label}</span></td>
      </tr>
    `).join('');
  }
};

window.PyroExplorer = PyroExplorer;
