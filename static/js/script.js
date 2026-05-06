/**
 * AMWAL Dashboard Logic - High-Fidelity Analytics
 */

const ChartRegistry = {};
let CurrentProperties = [];

const CATEGORY_COLORS = {
    'Luxury Villas': '#0066FF',
    'Standard Villas': '#F97316',
    'Larger Apartments': '#10B981',
    'Standard Flats': '#3B82F6'
};

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // 2. Navigation System
    const navLinks = document.querySelectorAll('.nav-link[data-target]');
    const viewSections = document.querySelectorAll('.view-section');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('data-target');

            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');

            viewSections.forEach(section => section.classList.remove('active'));
            const targetView = document.getElementById(targetId);
            if (targetView) targetView.classList.add('active');

            fetchViewData(targetId);
        });
    });

    // Back Button in Property Detail
    const btnBack = document.getElementById('btn-back');
    if (btnBack) {
        btnBack.addEventListener('click', () => {
            const portfolioTab = document.querySelector('.nav-link[data-target="view-portfolio"]');
            if (portfolioTab) portfolioTab.click();
        });
    }

    // 3. Filter System
    const filterButtons = document.querySelectorAll('.filter-btn');
    filterButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            filterButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const filterValue = btn.getAttribute('data-filter');
            applyFilter(filterValue);
        });
    });

    // 4. Initial Load
    fetchViewData('view-portfolio');

    // 5. AI Analyst Button Placeholder
    const aiBtn = document.querySelector('.ai-analyst-btn');
    if (aiBtn) {
        aiBtn.addEventListener('click', () => {
            alert("AI Portfolio Analyst: Analyzing 60 assets... Portfolio yield at 5.2%. No critical risks detected today.");
        });
    }

    // 6. Real-time Polling (60s)
    setInterval(() => {
        const activeLink = document.querySelector('.nav-link.active');
        if (activeLink) {
            fetchViewData(activeLink.getAttribute('data-target'));
        }
    }, 60000);
});

function applyFilter(filter) {
    console.log("Applying filter:", filter);
    let filtered = [...CurrentProperties];
    
    if (filter === 'Vacant') {
        filtered = filtered.filter(p => p.status === 'Vacant');
    } else if (filter !== 'All') {
        filtered = filtered.filter(p => p.category === filter);
    }
    
    console.log("Filtered count:", filtered.length);
    renderPropertyGrid(filtered, false); 
}

/**
 * Route View ID to API Endpoint
 */
async function fetchViewData(viewId) {
    let endpoint = '';
    switch (viewId) {
        case 'view-portfolio': endpoint = '/api/dashboard/portfolio-overview/'; break;
        case 'view-rental': endpoint = '/api/dashboard/rental-intelligence/'; break;
        case 'view-occupancy': endpoint = '/api/dashboard/occupancy/'; break;
        case 'view-financial': endpoint = '/api/dashboard/financial/'; break;
        case 'view-owner': endpoint = '/api/dashboard/portfolio-overview/'; break;
    }

    if (!endpoint) return;

    try {
        const res = await fetch(endpoint, { credentials: 'include' });
        if (res.ok) {
            const data = await res.json();
            renderView(viewId, data);
        } else {
            console.error(`API Error: ${res.status}`);
            showErrorUI(viewId);
        }
    } catch (err) {
        console.error(`Fetch Error: ${err}`);
        showErrorUI(viewId);
    }
}

function showErrorUI(viewId) {
    const kpiRowId = viewId.replace('view-', '') + '-kpis';
    const container = document.getElementById(kpiRowId);
    if (container) {
        container.innerHTML = '<div style="color: var(--danger); font-weight: 800; padding: 24px;">CRITICAL: Connection Lost. Retrying...</div>';
    }
}

/**
 * Render View specific components
 */
function renderView(viewId, data) {
    renderKPIs(viewId, data.kpis);

    if (viewId === 'view-portfolio') {
        renderAlerts(data.alerts);
        renderPortfolioCharts(data.charts);
        renderPropertyGrid(data.properties);
    } else if (viewId === 'view-rental') {
        renderRentalCharts(data.charts);
        renderRentalTable(data.tables);
    } else if (viewId === 'view-occupancy') {
        renderOccupancyCharts(data.charts);
        renderOccupancyTable(data.tables);
    } else if (viewId === 'view-financial') {
        renderFinancialCharts(data.charts);
    } else if (viewId === 'view-owner') {
        renderOwnerProfile(data.kpis);
    }

    if (typeof lucide !== 'undefined') lucide.createIcons();
}

function renderOwnerProfile(kpis) {
    const container = document.getElementById('owner-kpis');
    if (!container || !kpis) return;
    
    container.innerHTML = kpis.map(kpi => `
        <div class="card" style="margin-bottom: 0;">
            <span class="kpi-label">${kpi.title}</span>
            <span class="kpi-value" style="font-size: 1.5rem;">${kpi.value}</span>
        </div>
    `).join('');
}

/**
 * KPI Generator
 */
function renderKPIs(viewId, kpis) {
    const kpiRowId = viewId.replace('view-', '') + '-kpis';
    const container = document.getElementById(kpiRowId);
    if (!container) return;

    container.innerHTML = kpis.map(kpi => `
        <div class="kpi-card">
            <span class="kpi-label">${kpi.title}</span>
            <div style="display:flex; align-items:baseline; gap:6px;">
                <span class="kpi-value">${kpi.value}</span>
                <span style="color: var(--text-muted); font-weight: 800; font-size: 1.2rem;">${kpi.indicator || ''}</span>
            </div>
            <span class="kpi-subtext">${kpi.subtext}</span>
        </div>
    `).join('');
}

/**
 * Property Grid Rendering - GRID LAYOUT (PHASE 1)
 */
function renderPropertyGrid(properties, updateGlobal = true) {
    if (updateGlobal) CurrentProperties = properties;
    
    const container = document.getElementById('property-grid');
    if (!container) return;

    container.innerHTML = properties.map(p => {
        const statusClass = p.status.toLowerCase() === 'occupied' ? 'status-occupied' : 'status-vacant';
        const categoryMap = {
            'Luxury Villas': 'luxury',
            'Standard Villas': 'standard',
            'Larger Apartments': 'apartment',
            'Standard Flats': 'flat'
        };
        const categoryClass = categoryMap[p.category] || 'standard';
        
        // Highlight Rent Leakage if gap > 5% of market potential
        const isLeaking = p.rent_gap > (p.market_rent * 0.05);

        return `
            <div class="card property-card" onclick="openPropertyDetail(${p.id})" style="cursor:pointer;">
                <div class="img-container" style="background-image: url('${p.image}')"></div>
                
                <div class="prop-details-row" style="margin-top: 16px;">
                    <span class="status-pill ${statusClass}">${p.status}</span>
                    <span class="status-pill tag-${categoryClass}">${p.category}</span>
                </div>

                <div class="prop-details-row">
                    <h4 style="margin:0; font-weight: 800; font-size: 1.2rem;">${p.unit_ref}</h4>
                    <span style="font-weight: 700; color: var(--text-muted); font-size: 0.85rem;">${p.location}</span>
                </div>

                <div style="font-size: 0.9rem; color: var(--text-muted); font-weight: 600; margin-bottom: 12px;">
                    ${p.type} | ${p.bedrooms}BR | ${p.floor_area.toLocaleString()} sqft
                </div>

                <div style="border-top: 1px solid var(--border); padding-top: 12px; display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span class="kpi-label" style="margin:0; font-size: 0.7rem;">Monthly Rent</span>
                        <div class="prop-value-highlight">AED ${p.rent.toLocaleString()}</div>
                    </div>
                    ${isLeaking ? `
                        <div style="text-align: right;">
                            <span class="kpi-label" style="margin:0; font-size: 0.7rem; color: var(--danger);">Leakage</span>
                            <div class="prop-leakage">AED ${p.rent_gap.toLocaleString()}</div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Detail View Navigation
 */
/**
 * Detail View Navigation (PHASE 3)
 */
async function openPropertyDetail(id) {
    try {
        const res = await fetch(`/api/property/${id}/`, { credentials: 'include' });
        const p = await res.json();
        
        if (p.error) return;

        // UI Switch
        document.querySelectorAll('.view-section').forEach(s => s.classList.remove('active'));
        document.getElementById('view-property-detail').classList.add('active');

        // Populate Detail
        document.getElementById('detail-main-img').style.backgroundImage = `url('${p.images[0] || "https://via.placeholder.com/800x400"}')`;
        
        // Gallery thumbs
        const thumbStrip = document.getElementById('detail-thumb-strip');
        thumbStrip.innerHTML = p.images.map(img => `
            <div class="thumb-img" style="background-image: url('${img}')" onclick="document.getElementById('detail-main-img').style.backgroundImage='url(\\'${img}\\')'"></div>
        `).join('');

        document.getElementById('detail-ref').textContent = p.unit_ref;
        document.getElementById('detail-name').textContent = p.unit_ref + " – " + p.type;
        document.getElementById('detail-loc').textContent = p.location + ", Dubai, UAE";
        document.getElementById('detail-type').textContent = p.type;
        document.getElementById('detail-area').textContent = p.floor_area.toLocaleString() + " sqft";

        // Rent Analysis
        document.getElementById('detail-rent-annual').textContent = "AED " + p.rent.annual.toLocaleString();
        document.getElementById('detail-market-annual').textContent = "AED " + p.rent.market.toLocaleString();
        document.getElementById('detail-rent-gap').textContent = "AED " + p.rent.gap.toLocaleString();

        // Lease/Tenant
        const leaseCard = document.getElementById('detail-lease-card');
        if (p.lease) {
            leaseCard.style.display = 'block';
            document.getElementById('detail-tenant-name').textContent = p.lease.tenant.name;
            document.getElementById('detail-tenant-email').textContent = p.lease.tenant.email;
            document.getElementById('detail-lease-end').textContent = p.lease.end_date;
            document.getElementById('detail-lease-rent').textContent = "AED " + p.lease.monthly_rent.toLocaleString();
        } else {
            leaseCard.style.display = 'none';
        }

        if (typeof lucide !== 'undefined') lucide.createIcons();

    } catch (err) {
        console.error("Error opening detail:", err);
    }
}

/**
 * Alert Generator
 */
function renderAlerts(alerts) {
    const container = document.getElementById('alerts-panel');
    if (!container || !alerts) return;

    container.innerHTML = alerts.map(alert => {
        const severityClass = alert.severity.toLowerCase();
        const icon = alert.severity === 'Critical' ? 'alert-octagon' : 'alert-circle';
        
        return `
            <div class="alert-item ${severityClass}">
                <i data-lucide="${icon}"></i>
                <div class="alert-content">
                    <div class="alert-tag">${alert.type} | ${alert.severity}</div>
                    <div class="alert-msg">${alert.message}</div>
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Chart.js Integration
 */
function safeRender(canvasId, config) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    if (ChartRegistry[canvasId]) ChartRegistry[canvasId].destroy();
    ChartRegistry[canvasId] = new Chart(ctx, config);
}

function renderPortfolioCharts(charts) {
    safeRender('chart-composition', {
        type: 'doughnut',
        data: {
            labels: charts.composition.labels,
            datasets: [{
                data: charts.composition.datasets[0].data,
                backgroundColor: charts.composition.labels.map(label => CATEGORY_COLORS[label] || '#E0E5F2'),
                borderWidth: 0,
                spacing: 4
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false, cutout: '75%',
            plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, font: { weight: 'bold' } } } }
        }
    });

    safeRender('chart-trend', {
        type: 'line',
        data: {
            labels: charts.trend.labels,
            datasets: [{
                label: 'Portfolio Occupancy',
                data: charts.trend.datasets[0].data,
                borderColor: '#0066FF',
                backgroundColor: 'rgba(0, 102, 255, 0.05)',
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointBackgroundColor: '#fff',
                borderWidth: 3
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: false, grid: { color: '#E0E5F2'}, border: { display: false } },
                x: { grid: { display: false } }
            }
        }
    });

    // Occupancy Bars: Categorized
    // REMOVED HARDCODED DATA - This should ideally come from backend, but for now we enforce colors
    safeRender('chart-occupancy-bars', {
        type: 'bar',
        data: {
            labels: ['Luxury Villas', 'Standard Villas', 'Larger Apartments', 'Standard Flats'],
            datasets: [
                { 
                    label: 'Occupied', 
                    data: [
                        charts.composition.labels.indexOf('Luxury Villas') > -1 ? charts.composition.datasets[0].data[charts.composition.labels.indexOf('Luxury Villas')] : 0,
                        charts.composition.labels.indexOf('Standard Villas') > -1 ? charts.composition.datasets[0].data[charts.composition.labels.indexOf('Standard Villas')] : 0,
                        charts.composition.labels.indexOf('Larger Apartments') > -1 ? charts.composition.datasets[0].data[charts.composition.labels.indexOf('Larger Apartments')] : 0,
                        charts.composition.labels.indexOf('Standard Flats') > -1 ? charts.composition.datasets[0].data[charts.composition.labels.indexOf('Standard Flats')] : 0
                    ], 
                    backgroundColor: ['#0066FF', '#F97316', '#10B981', '#3B82F6'], 
                    borderRadius: 6 
                },
                { 
                    label: 'Vacant', 
                    data: [0, 0, 0, 0], // Fallback if data not available
                    backgroundColor: '#E0E5F2', 
                    borderRadius: 6 
                }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { stacked: true, grid: { color: '#E0E5F2'}, border: { display: false } },
                x: { stacked: true, grid: { display: false } }
            }
        }
    });
}

function renderRentalCharts(charts) {
    safeRender('chart-rental-comparison', {
        type: 'bar',
        data: {
            labels: charts.labels,
            datasets: [
                { label: 'Current Rent', data: charts.datasets[0].data, backgroundColor: '#3B82F6', borderRadius: 4 },
                { label: 'Market Rent', data: charts.datasets[1].data, backgroundColor: '#F97316', borderRadius: 4 }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { position: 'top' } },
            scales: {
                y: { grid: { color: '#E0E5F2'} },
                x: { grid: { display: false } }
            }
        }
    });
}

function renderOccupancyCharts(charts) {
    safeRender('chart-occupancy-bars', {
        type: 'doughnut',
        data: {
            labels: charts.labels,
            datasets: [{
                data: charts.datasets[0].data,
                backgroundColor: ['#10B981', '#EF4444', '#3B82F6'],
                borderWidth: 0,
                spacing: 8
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false, cutout: '70%',
            plugins: { legend: { position: 'bottom' } }
        }
    });
}

/**
 * ApexCharts Waterfall
 */
/**
 * ApexCharts & Chart.js Multi-Integration (PHASE 4)
 */
function renderFinancialCharts(charts) {
    // 1. Waterfall
    const waterfallContainer = document.querySelector('#chart-waterfall');
    if (waterfallContainer) {
        waterfallContainer.innerHTML = '';
        
        const data = charts.waterfall.datasets[0].data;
        const potential = data[0];
        const loss = data[1];
        const leakage = data[2];
        const fees = data[3];
        const net = data[4];

        const seriesData = [
            { x: 'Market Potential', y: [0, potential] },
            { x: 'Vacancy Loss', y: [potential, potential + loss] }, // loss is negative
            { x: 'Rent Leakage', y: [potential + loss, potential + loss + leakage] },
            { x: 'Fees', y: [potential + loss + leakage, potential + loss + leakage + fees] },
            { x: 'Net Income', y: [0, net] }
        ];

        const waterfallOptions = {
            series: [{ name: 'Revenue', data: seriesData }],
            chart: { type: 'bar', height: 350, fontFamily: 'Inter', toolbar: { show: false } },
            plotOptions: {
                bar: {
                    horizontal: false,
                    columnWidth: '60%',
                }
            },
            dataLabels: {
                enabled: true,
                formatter: (val, opt) => {
                    const range = opt.w.config.series[0].data[opt.dataPointIndex].y;
                    const diff = Math.abs(range[1] - range[0]);
                    return 'AED ' + (diff/1000).toFixed(0) + 'K';
                },
                style: { colors: ['#fff'] }
            },
            colors: [
                ({ value, dataPointIndex }) => {
                    if (dataPointIndex === 0) return '#10B981';
                    if (dataPointIndex === 4) return '#0066FF';
                    return '#EF4444';
                }
            ],
            xaxis: { type: 'category' },
            yaxis: { labels: { formatter: (val) => (val/1000).toFixed(0) + 'K' } }
        };
        new ApexCharts(waterfallContainer, waterfallOptions).render();
    }

    // 2. Income Trend (Line + Area)
    safeRender('chart-income-trend', {
        type: 'line',
        data: {
            labels: charts.trend.labels,
            datasets: [{
                label: 'Monthly Net Income',
                data: charts.trend.datasets[0].data,
                borderColor: '#0066FF',
                backgroundColor: 'rgba(0, 102, 255, 0.1)',
                fill: true,
                tension: 0.4,
                borderWidth: 3,
                pointRadius: 4
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { grid: { color: '#E0E5F2'}, border: { display: false } },
                x: { grid: { display: false } }
            }
        }
    });

    // 3. Scenario Analysis (Apex Bar)
    const scenarioContainer = document.querySelector('#chart-scenarios');
    if (scenarioContainer) {
        scenarioContainer.innerHTML = '';
        const scenarioOptions = {
            series: [
                { name: 'LTV Range', data: charts.scenarios.datasets[0].data },
                { name: 'Yield Range', data: charts.scenarios.datasets[1].data }
            ],
            chart: { type: 'bar', height: 350, toolbar: { show: false } },
            plotOptions: { bar: { horizontal: false, columnWidth: '55%', borderRadius: 6 } },
            dataLabels: { enabled: false },
            colors: ['#3B82F6', '#10B981'],
            xaxis: { categories: charts.scenarios.labels },
            yaxis: { title: { text: 'Percentage (%)' } },
            fill: { opacity: 1 }
        };
        new ApexCharts(scenarioContainer, scenarioOptions).render();
    }
}

/**
 * Table Renderers
 */
function renderRentalTable(rows) {
    const container = document.getElementById('rental-table-container');
    if (!container) return;

    container.innerHTML = `
        <table class="data-table">
            <thead>
                <tr>
                    <th>Unit Ref</th>
                    <th>Property Type</th>
                    <th>CurrentRent (Annual)</th>
                    <th>Market Rent (Annual)</th>
                    <th>Annual Gap</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                ${rows.map(row => `
                    <tr>
                        <td>${row.unit_ref}</td>
                        <td>${row.type}</td>
                        <td>AED ${row.current.toLocaleString()}</td>
                        <td>AED ${row.market.toLocaleString()}</td>
                        <td style="color: var(--danger)">AED ${row.gap.toLocaleString()}</td>
                        <td><span class="status-pill status-${row.status.toLowerCase().replace(' ', '-')}">${row.status}</span></td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

function renderOccupancyTable(rows) {
    const container = document.getElementById('occupancy-table-container');
    if (!container) return;

    container.innerHTML = `
        <table class="data-table">
            <thead>
                <tr>
                    <th>Unit Ref</th>
                    <th>Days Vacant</th>
                    <th>Monthly Rent</th>
                    <th>Est. Vacancy Loss (YTD)</th>
                    <th>Vacancy Reason</th>
                </tr>
            </thead>
            <tbody>
                ${rows.map(row => `
                    <tr>
                        <td>${row.unit_ref}</td>
                        <td>${row.days_vacant} Days</td>
                        <td>AED ${row.monthly_rent.toLocaleString()}</td>
                        <td style="color: var(--danger)">AED ${row.vacancy_loss.toLocaleString()}</td>
                        <td>${row.reason || 'Not Specified'}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}
