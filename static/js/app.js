let activeDevice = 'pi4';
let currentMetric = 'temp';
let isStreaming = true;
let chartInstance = null;
let pollInterval = null;

// Telemetry buffer for Chart.js
const chartDataBuffer = {
    labels: [],
    datasets: {
        pi4: [],
        pi5: [],
        pi6: [],
        pi7: []
    }
};

const maxDataPoints = 20;

// Device labels mapping
const deviceNames = {
    pi4: 'Pi-4 (Living Room Hub)',
    pi5: 'Pi-5 (Structural & Vibration)',
    pi6: 'Pi-6 (Hallway Entry Node)',
    pi7: 'Pi-7 (Kitchen Safety & Gas)'
};

// Initialize Chart.js
function initChart() {
    const ctx = document.getElementById('liveTelemetryChart').getContext('2d');
    
    // Create gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 350);
    gradient.addColorStop(0, 'rgba(0, 242, 254, 0.35)');
    gradient.addColorStop(1, 'rgba(0, 242, 254, 0.0)');

    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Temperature (°C)',
                data: [],
                borderColor: '#00f2fe',
                backgroundColor: gradient,
                borderWidth: 2.5,
                fill: true,
                tension: 0.35,
                pointRadius: 4,
                pointBackgroundColor: '#00f2fe',
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 400
            },
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        color: '#94a3b8',
                        font: { family: 'Plus Jakarta Sans', size: 12 }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    titleColor: '#00f2fe',
                    bodyColor: '#f8fafc'
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#64748b', font: { family: 'JetBrains Mono', size: 11 } }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#64748b', font: { family: 'JetBrains Mono', size: 11 } }
                }
            }
        }
    });
}

// Select active device to focus
function selectDevice(devId) {
    activeDevice = devId;
    document.querySelectorAll('.node-card').forEach(c => c.classList.remove('active'));
    const targetCard = document.getElementById(`node-card-${devId}`);
    if (targetCard) targetCard.classList.add('active');

    const ind = document.getElementById('active-device-indicator');
    if (ind) ind.textContent = `Viewing: ${deviceNames[devId]}`;
    
    updateChartTheme();
}

// Switch metric shown in chart
function setChartMetric(metric) {
    currentMetric = metric;
    document.querySelectorAll('.btn-chip').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    updateChartTheme();
}

function updateChartTheme() {
    if (!chartInstance) return;
    
    let label = 'Temperature (°C)';
    let color = '#00f2fe';

    if (currentMetric === 'humidity') {
        label = 'Humidity (%)';
        color = '#8b5cf6';
    } else if (currentMetric === 'anomaly') {
        label = 'Anomaly Probability Score';
        color = '#ef4444';
    }

    chartInstance.data.datasets[0].label = `${deviceNames[activeDevice]} - ${label}`;
    chartInstance.data.datasets[0].borderColor = color;
    chartInstance.data.datasets[0].pointBackgroundColor = color;
    chartInstance.update();
}

// Fetch live telemetry stream
async function fetchTelemetry() {
    if (!isStreaming) return;

    try {
        const res = await fetch('/api/telemetry/live');
        const data = await res.json();
        if (!data.success) return;

        const timeLabel = new Date().toLocaleTimeString();
        const devData = data.data;

        // Update Pi-4
        if (devData.pi4) {
            document.getElementById('val-pi4-temp').textContent = `${devData.pi4.temperature_C} °C`;
            document.getElementById('val-pi4-humidity').textContent = `${devData.pi4.humidity} %`;
            document.getElementById('val-pi4-pir').textContent = devData.pi4.pir_motion ? 'Active' : 'Idle';
            updateNodeRisk('pi4', devData.pi4);
        }

        // Update Pi-5
        if (devData.pi5) {
            document.getElementById('val-pi5-temp').textContent = `${devData.pi5.temperature_C} °C`;
            document.getElementById('val-pi5-accel').textContent = `${devData.pi5.accel_z_m_s2} m/s²`;
            updateNodeRisk('pi5', devData.pi5);
        }

        // Update Pi-6
        if (devData.pi6) {
            document.getElementById('val-pi6-temp').textContent = `${devData.pi6.temperature_C} °C`;
            document.getElementById('val-pi6-humidity').textContent = `${devData.pi6.humidity} %`;
            document.getElementById('val-pi6-pir').textContent = devData.pi6.pir_motion ? 'Active' : 'Idle';
            updateNodeRisk('pi6', devData.pi6);
        }

        // Update Pi-7
        if (devData.pi7) {
            document.getElementById('val-pi7-temp').textContent = `${devData.pi7.temperature_C} °C`;
            document.getElementById('val-pi7-mq').textContent = `${devData.pi7.mq_raw}`;
            updateNodeRisk('pi7', devData.pi7);
        }

        // Update Center Gauges
        const activeReading = devData[activeDevice];
        if (activeReading) {
            document.getElementById('selected-gauge-temp').textContent = `${activeReading.temperature_C} °C`;
            document.getElementById('selected-gauge-humidity').textContent = `${activeReading.humidity} %`;
            const riskEl = document.getElementById('selected-gauge-score');
            if (activeReading.anomaly_flag) {
                riskEl.textContent = `${activeReading.anomaly_score} (${activeReading.anomaly_type})`;
                riskEl.className = 'g-val text-danger';
            } else {
                riskEl.textContent = `${activeReading.anomaly_score} (Normal)`;
                riskEl.className = 'g-val text-cyan';
            }
        }

        // Update Chart
        let plotVal = activeReading.temperature_C;
        if (currentMetric === 'humidity') plotVal = activeReading.humidity;
        if (currentMetric === 'anomaly') plotVal = activeReading.anomaly_score;

        chartInstance.data.labels.push(timeLabel);
        chartInstance.data.datasets[0].data.push(plotVal);

        if (chartInstance.data.labels.length > maxDataPoints) {
            chartInstance.data.labels.shift();
            chartInstance.data.datasets[0].data.shift();
        }
        chartInstance.update();

        // Refresh Alerts
        fetchAlerts();

    } catch (err) {
        console.error('Telemetry fetch failed:', err);
    }
}

function updateNodeRisk(devId, reading) {
    const riskEl = document.getElementById(`risk-${devId}`);
    if (!riskEl) return;

    if (reading.anomaly_flag) {
        riskEl.textContent = `${reading.anomaly_score} (ANOMALY)`;
        riskEl.className = 'risk-badge risk-high';
    } else {
        riskEl.textContent = `${reading.anomaly_score} (Normal)`;
        riskEl.className = 'risk-badge risk-low';
    }
}

// Fetch Alerts Feed
async function fetchAlerts() {
    try {
        const res = await fetch('/api/alerts');
        const data = await res.json();
        if (!data.success) return;

        const container = document.getElementById('alerts-container');
        const counter = document.getElementById('alert-counter');

        if (data.alerts.length === 0) {
            counter.textContent = '0 Detected';
            container.innerHTML = `
                <div class="empty-alerts">
                    <i data-lucide="shield-check"></i>
                    <p>No active anomalies detected across edge nodes.</p>
                    <span>Systems operating under standard parameters.</span>
                </div>
            `;
            lucide.createIcons();
            return;
        }

        counter.textContent = `${data.alerts.length} Detected`;
        container.innerHTML = data.alerts.map(a => `
            <div class="alert-item">
                <div class="alert-item-header">
                    <span class="alert-item-title">${a.device} • ${a.severity}</span>
                    <span class="alert-item-time">${a.time}</span>
                </div>
                <div class="alert-item-desc">${a.type} (Score: ${a.score})</div>
            </div>
        `).join('');

    } catch (err) {
        console.error('Alerts fetch failed:', err);
    }
}

// Fault injection triggers
async function triggerFault(faultType) {
    try {
        await fetch('/api/inject-anomaly', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: faultType, device: activeDevice })
        });
    } catch (err) {
        console.error(err);
    }
}

async function clearFault() {
    try {
        await fetch('/api/clear-anomaly', { method: 'POST' });
    } catch (err) {
        console.error(err);
    }
}

// Modal controls
const modal = document.getElementById('fault-modal');
document.getElementById('btn-inject-modal').addEventListener('click', () => {
    modal.classList.add('open');
});

function closeModal() {
    modal.classList.remove('open');
}

async function submitModalFault() {
    const node = document.getElementById('modal-target-node').value;
    const type = document.getElementById('modal-fault-type').value;

    try {
        await fetch('/api/inject-anomaly', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: type, device: node })
        });
        closeModal();
    } catch (err) {
        console.error(err);
    }
}

// Pause/Resume button
document.getElementById('btn-pause-stream').addEventListener('click', function() {
    isStreaming = !isStreaming;
    const statusText = document.getElementById('system-status-text');
    if (isStreaming) {
        this.innerHTML = '<i data-lucide="pause"></i> Pause Stream';
        statusText.textContent = 'LIVE STREAMING';
    } else {
        this.innerHTML = '<i data-lucide="play"></i> Resume Stream';
        statusText.textContent = 'STREAM PAUSED';
    }
    lucide.createIcons();
});

// Start loop
window.addEventListener('DOMContentLoaded', () => {
    initChart();
    fetchTelemetry();
    pollInterval = setInterval(fetchTelemetry, 1500);
});
