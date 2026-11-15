/**
 * PyroNexa 26 - Scientific Data Visualizations (Plotly.js)
 * Implements interactive charts for Overview, Burning Activity Calendar,
 * Historical Baselines, MODIS-VIIRS Comparison, and Anomaly Detection.
 */

const PyroCharts = {
  theme: {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: {
      color: '#cbd5e1',
      family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    },
    gridcolor: '#1e293b',
    zerolinecolor: '#334155'
  },

  _renderEmptyPlot: function(el, message) {
    if (!el) return;
    Plotly.react(el, [], {
      ...this.theme,
      margin: { t: 20, b: 20, l: 20, r: 20 },
      annotations: [{
        text: message || 'No active fire data matches current filters.',
        xref: 'paper',
        yref: 'paper',
        x: 0.5,
        y: 0.5,
        showarrow: false,
        font: { size: 13, color: '#94a3b8' }
      }]
    }, { responsive: true, displayModeBar: false });
  },

  resizeAllCharts: function() {
    const ids = [
      'chart-sensor-pie',
      'chart-daynight',
      'chart-calendar-heatmap',
      'chart-historical-timeline',
      'chart-seasonal-baseline',
      'chart-yearly-trends',
      'chart-rfai-comparison',
      'chart-frp-distribution',
      'chart-anomalies-timeline'
    ];
    ids.forEach(id => {
      const el = document.getElementById(id);
      if (el && el.data && window.Plotly) {
        try {
          Plotly.Plots.resize(el);
        } catch (e) {}
      }
    });
  },

  renderAllCharts: function(overview, calendar, historical, comparison, anomalies) {
    if (overview) this.renderOverviewCharts(overview);
    if (calendar) this.renderCalendarHeatmap(calendar);
    if (historical) this.renderHistoricalCharts(historical);
    if (comparison) this.renderComparisonCharts(comparison);
    if (anomalies) this.renderAnomalyCharts(anomalies);
  },

  renderOverviewCharts: function(data) {
    const sensorEl = document.getElementById('chart-sensor-pie');
    if (sensorEl && data.sensor_breakdown) {
      const modisCnt = data.sensor_breakdown.MODIS || 0;
      const viirsCnt = data.sensor_breakdown.VIIRS || 0;

      const pieData = [{
        values: [modisCnt, viirsCnt],
        labels: ['MODIS (1km)', 'VIIRS (375m)'],
        type: 'pie',
        hole: 0.6,
        marker: {
          colors: ['#3b82f6', '#f97316']
        },
        textinfo: 'label+percent',
        textfont: { color: '#ffffff', size: 12 },
        hoverinfo: 'label+value+percent'
      }];

      const layout = {
        ...this.theme,
        margin: { t: 10, b: 10, l: 10, r: 10 },
        height: 230,
        showlegend: false
      };

      Plotly.react(sensorEl, pieData, layout, { responsive: true, displayModeBar: false });
    }

    const dnEl = document.getElementById('chart-daynight');
    if (dnEl && data.daynight_breakdown) {
      const barData = [{
        x: ['Day Overpass (Solar Peak)', 'Night Overpass (Thermal Baseline)'],
        y: [data.daynight_breakdown.day || 0, data.daynight_breakdown.night || 0],
        type: 'bar',
        marker: {
          color: ['#eab308', '#6366f1']
        }
      }];

      const layout = {
        ...this.theme,
        margin: { t: 20, b: 35, l: 45, r: 15 },
        height: 230,
        xaxis: { gridcolor: this.theme.gridcolor },
        yaxis: { gridcolor: this.theme.gridcolor, title: 'Hotspots' }
      };

      Plotly.react(dnEl, barData, layout, { responsive: true, displayModeBar: false });
    }
  },

  renderCalendarHeatmap: function(data) {
    const calEl = document.getElementById('chart-calendar-heatmap');
    if (!calEl) return;
    if (!data || !data.matrix || data.matrix.length === 0) {
      this._renderEmptyPlot(calEl, 'No seasonal fire activity recorded for current filter criteria.');
      return;
    }

    const years = data.years.map(String);
    const months = data.month_names;

    // Build 2D z array: z[year_idx][month_idx]
    const z = [];
    const text = [];
    for (const row of data.matrix) {
      const zRow = [];
      const textRow = [];
      for (const m of row.months) {
        zRow.push(m.count);
        textRow.push(`Year: ${row.year}<br>Month: ${m.month_name}<br>Detections: ${m.count.toLocaleString()}<br>FRP: ${m.total_frp} MW`);
      }
      z.push(zRow);
      text.push(textRow);
    }

    const heatmapData = [{
      z: z,
      x: months,
      y: years,
      type: 'heatmap',
      colorscale: [
        [0.0, '#0f172a'],
        [0.15, '#1e293b'],
        [0.35, '#b45309'],
        [0.65, '#ea580c'],
        [1.0, '#dc2626']
      ],
      hoverinfo: 'text',
      text: text,
      colorbar: {
        title: 'Hotspots',
        titleside: 'top',
        tickcolor: '#94a3b8',
        tickfont: { color: '#94a3b8' }
      }
    }];

    const layout = {
      ...this.theme,
      margin: { t: 30, b: 40, l: 60, r: 20 },
      height: 380,
      xaxis: { title: 'Calendar Month', tickcolor: '#94a3b8' },
      yaxis: { title: 'Year', autorange: 'reversed' }
    };

    Plotly.react(calEl, heatmapData, layout, { responsive: true, displayModeBar: true });
  },

  renderHistoricalCharts: function(data) {
    // 1. Monthly Timeline
    const timelineEl = document.getElementById('chart-historical-timeline');
    if (timelineEl) {
      if (!data || !data.monthly_series || data.monthly_series.length === 0) {
        this._renderEmptyPlot(timelineEl, 'No historical monthly data matching current filter criteria.');
      } else {
        const ym = data.monthly_series.map(d => d.year_month);
        const modisCounts = data.monthly_series.map(d => d.modis_count);
        const viirsCounts = data.monthly_series.map(d => d.viirs_count);
        const totalCounts = data.monthly_series.map(d => d.total_count);

        const traces = [
          {
            x: ym,
            y: totalCounts,
            name: 'Total Active Fires',
            type: 'scatter',
            mode: 'lines+markers',
            line: { color: '#38bdf8', width: 2.5 }
          },
          {
            x: ym,
            y: viirsCounts,
            name: 'VIIRS (375m)',
            type: 'scatter',
            mode: 'lines',
            line: { color: '#f97316', width: 1.8, dash: 'dot' }
          },
          {
            x: ym,
            y: modisCounts,
            name: 'MODIS (1km)',
            type: 'scatter',
            mode: 'lines',
            line: { color: '#3b82f6', width: 1.8, dash: 'dash' }
          }
        ];

        const layout = {
          ...this.theme,
          margin: { t: 25, b: 45, l: 55, r: 20 },
          height: 350,
          legend: { orientation: 'h', y: 1.15, x: 0 },
          xaxis: { gridcolor: this.theme.gridcolor, title: 'Year-Month' },
          yaxis: { gridcolor: this.theme.gridcolor, title: 'Detections' }
        };

        Plotly.react(timelineEl, traces, layout, { responsive: true, displayModeBar: false });
      }
    }

    // 2. Seasonal Baseline Curve
    const seasonalEl = document.getElementById('chart-seasonal-baseline');
    if (seasonalEl && data.seasonal_baseline && data.seasonal_baseline.length > 0) {
      const mNames = data.seasonal_baseline.map(d => d.month_name);
      const medians = data.seasonal_baseline.map(d => d.median_count);
      const q25 = data.seasonal_baseline.map(d => d.q25_count);
      const q75 = data.seasonal_baseline.map(d => d.q75_count);

      const traces = [
        {
          x: mNames,
          y: q75,
          type: 'scatter',
          mode: 'lines',
          line: { color: 'transparent' },
          showlegend: false
        },
        {
          x: mNames,
          y: q25,
          type: 'scatter',
          mode: 'lines',
          fill: 'tonexty',
          fillcolor: 'rgba(56, 189, 248, 0.15)',
          line: { color: 'transparent' },
          name: 'Historical 25th-75th Percentile Band'
        },
        {
          x: mNames,
          y: medians,
          type: 'scatter',
          mode: 'lines+markers',
          line: { color: '#38bdf8', width: 3 },
          name: 'Historical Median Baseline'
        }
      ];

      const layout = {
        ...this.theme,
        margin: { t: 25, b: 40, l: 55, r: 20 },
        height: 320,
        legend: { orientation: 'h', y: 1.15, x: 0 },
        xaxis: { gridcolor: this.theme.gridcolor },
        yaxis: { gridcolor: this.theme.gridcolor, title: 'Seasonal Hotspots' }
      };

      Plotly.react(seasonalEl, traces, layout, { responsive: true, displayModeBar: false });
    }

    // 3. Yearly Trends Stacked Bar
    const yearlyEl = document.getElementById('chart-yearly-trends');
    if (yearlyEl && data.yearly_trends && data.yearly_trends.length > 0) {
      const yrs = data.yearly_trends.map(d => String(d.year));
      const modis = data.yearly_trends.map(d => d.modis_detections);
      const viirs = data.yearly_trends.map(d => d.viirs_detections);

      const traces = [
        {
          x: yrs,
          y: modis,
          name: 'MODIS',
          type: 'bar',
          marker: { color: '#3b82f6' }
        },
        {
          x: yrs,
          y: viirs,
          name: 'VIIRS',
          type: 'bar',
          marker: { color: '#f97316' }
        }
      ];

      const layout = {
        ...this.theme,
        barmode: 'stack',
        margin: { t: 25, b: 40, l: 55, r: 20 },
        height: 320,
        legend: { orientation: 'h', y: 1.15, x: 0 },
        xaxis: { gridcolor: this.theme.gridcolor },
        yaxis: { gridcolor: this.theme.gridcolor, title: 'Annual Hotspots' }
      };

      Plotly.react(yearlyEl, traces, layout, { responsive: true, displayModeBar: false });
    }
  },

  renderComparisonCharts: function(data) {
    // Populate comparison KPI cards
    const countRatioEl = document.getElementById('comp-count-ratio');
    if (countRatioEl) {
      countRatioEl.textContent = data.detection_ratio !== null ? `${data.detection_ratio.toFixed(2)}x` : 'N/A';
    }
    const areaRatioEl = document.getElementById('comp-area-ratio');
    if (areaRatioEl) {
      areaRatioEl.textContent = data.area_ratio !== null ? `${data.area_ratio.toFixed(2)}x` : 'N/A';
    }
    const clustersCountEl = document.getElementById('comp-clusters-count');
    if (clustersCountEl) {
      const uCl = (data.coincident_summary && data.coincident_summary.unique_clusters) || 0;
      clustersCountEl.textContent = uCl.toLocaleString();
    }
    const clusterRatioEl = document.getElementById('comp-cluster-ratio');
    if (clusterRatioEl) {
      const vPerM = data.coincident_summary && data.coincident_summary.viirs_per_modis_cluster_ratio;
      clusterRatioEl.textContent = vPerM !== null && vPerM !== undefined ? `${vPerM.toFixed(2)}x` : 'N/A';
    }

    // 1. RFAI Harmonized Comparison Lines
    const rfaiEl = document.getElementById('chart-rfai-comparison');
    if (rfaiEl && data.rfai_analysis && data.rfai_analysis.monthly_rfai) {
      const rf = data.rfai_analysis.monthly_rfai;
      const ym = rf.map(d => d.year_month);
      const modisRfai = rf.map(d => d.rfai_modis);
      const viirsRfai = rf.map(d => d.rfai_viirs);
      const harmRfai = rf.map(d => d.rfai_harmonized);

      const traces = [
        {
          x: ym,
          y: modisRfai,
          name: 'MODIS RFAI (Relative Index)',
          type: 'scatter',
          mode: 'lines',
          line: { color: '#3b82f6', width: 2 }
        },
        {
          x: ym,
          y: viirsRfai,
          name: 'VIIRS RFAI (Relative Index)',
          type: 'scatter',
          mode: 'lines',
          line: { color: '#f97316', width: 2 }
        },
        {
          x: ym,
          y: harmRfai,
          name: 'Harmonized Composite Index',
          type: 'scatter',
          mode: 'lines+markers',
          line: { color: '#38bdf8', width: 2.5, dash: 'dot' }
        }
      ];

      const layout = {
        ...this.theme,
        margin: { t: 25, b: 45, l: 55, r: 20 },
        height: 340,
        legend: { orientation: 'h', y: 1.15, x: 0 },
        xaxis: { gridcolor: this.theme.gridcolor, title: 'Year-Month' },
        yaxis: { gridcolor: this.theme.gridcolor, title: 'Dimensionless Index (1.0 = Baseline Median)' }
      };

      Plotly.react(rfaiEl, traces, layout, { responsive: true, displayModeBar: false });
    }

    // 2. FRP Quantile Comparison
    const frpEl = document.getElementById('chart-frp-distribution');
    if (frpEl && data.frp_quantiles) {
      const q = data.frp_quantiles;
      const categories = ['Median (50%)', '75th Percentile', '95th Percentile (Extreme)'];
      const modisVals = [
        q.MODIS ? q.MODIS.median : 0,
        q.MODIS ? q.MODIS.q75 : 0,
        q.MODIS ? q.MODIS.q95 : 0
      ];
      const viirsVals = [
        q.VIIRS ? q.VIIRS.median : 0,
        q.VIIRS ? q.VIIRS.q75 : 0,
        q.VIIRS ? q.VIIRS.q95 : 0
      ];

      const traces = [
        {
          x: categories,
          y: modisVals,
          name: 'MODIS FRP (1km Pixel)',
          type: 'bar',
          marker: { color: '#3b82f6' }
        },
        {
          x: categories,
          y: viirsVals,
          name: 'VIIRS FRP (375m Pixel)',
          type: 'bar',
          marker: { color: '#f97316' }
        }
      ];

      const layout = {
        ...this.theme,
        barmode: 'group',
        margin: { t: 25, b: 40, l: 55, r: 20 },
        height: 320,
        legend: { orientation: 'h', y: 1.15, x: 0 },
        xaxis: { gridcolor: this.theme.gridcolor },
        yaxis: { gridcolor: this.theme.gridcolor, title: 'FRP (Megawatts)' }
      };

      Plotly.react(frpEl, traces, layout, { responsive: true, displayModeBar: false });
    }
  },

  renderAnomalyCharts: function(data) {
    const el = document.getElementById('chart-anomalies-timeline');
    if (!el || !data || !data.monthly_anomalies || data.monthly_anomalies.length === 0) return;

    const ym = data.monthly_anomalies.map(d => d.year_month);
    const zScores = data.monthly_anomalies.map(d => d.z_score);
    const colors = data.monthly_anomalies.map(d => d.severity_color);
    const hoverTexts = data.monthly_anomalies.map(d => 
      `${d.year_month}<br>Z-Score: ${d.z_score}<br>Modified Z (MAD): ${d.z_mad}<br>Severity: ${d.severity_label}<br>Count: ${d.count} (${d.pct_of_baseline}% of seasonal median)`
    );

    const barTrace = {
      x: ym,
      y: zScores,
      type: 'bar',
      marker: { color: colors },
      hoverinfo: 'text',
      text: hoverTexts
    };

    // Reference threshold lines
    const layout = {
      ...this.theme,
      margin: { t: 30, b: 45, l: 55, r: 20 },
      height: 350,
      xaxis: { gridcolor: this.theme.gridcolor, title: 'Year-Month' },
      yaxis: { gridcolor: this.theme.gridcolor, title: 'Standardized Z-Score (Divergence)' },
      shapes: [
        {
          type: 'line',
          x0: ym[0],
          x1: ym[ym.length - 1],
          y0: 2.0,
          y1: 2.0,
          line: { color: '#ea580c', width: 1.5, dash: 'dash' }
        },
        {
          type: 'line',
          x0: ym[0],
          x1: ym[ym.length - 1],
          y0: 3.0,
          y1: 3.0,
          line: { color: '#dc2626', width: 1.5, dash: 'dash' }
        }
      ],
      annotations: [
        {
          x: ym[Math.floor(ym.length / 2)],
          y: 3.1,
          text: 'Extreme Fire Activity Threshold (Z >= 3.0)',
          showarrow: false,
          font: { color: '#f87171', size: 10 }
        }
      ]
    };

    Plotly.react(el, [barTrace], layout, { responsive: true, displayModeBar: false });
  }
};

window.PyroCharts = PyroCharts;
