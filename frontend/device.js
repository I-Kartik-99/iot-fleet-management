const API_BASE_URL = "http://127.0.0.1:8000";

const params = new URLSearchParams(window.location.search);
const deviceId = params.get("id");

let charts = {};

function formatTime(timestamp) {
    if (!timestamp) return "Never";

    return new Date(timestamp).toLocaleString("en-IN", {
        dateStyle: "medium",
        timeStyle: "medium"
    });
}

function shortTime(timestamp) {
    if (!timestamp) return "";

    return new Date(timestamp).toLocaleTimeString("en-IN", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
    });
}

function statusClass(status) {
    return status === "ONLINE" ? "status-online" : "status-offline";
}

function renderChart(id, records, field, label, color, unit) {
    const canvas = document.getElementById(id);
    if (!canvas) return;

    const ordered = [...records].reverse();

    const labels = ordered.map(r => shortTime(r.timestamp));
    const values = ordered.map(r => Number(r[field] ?? 0));

    if (charts[id]) {
        charts[id].data.labels = labels;
        charts[id].data.datasets[0].data = values;
        charts[id].update("none");
        return;
    }

    charts[id] = new Chart(canvas, {
        type: "line",
        data: {
            labels,
            datasets: [{
                label,
                data: values,
                borderColor: color,
                backgroundColor: color + "18",
                borderWidth: 2,
                pointRadius: 2,
                pointHoverRadius: 4,
                fill: true,
                tension: 0.35
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: context => `${context.parsed.y} ${unit}`
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: "#647596",
                        maxTicksLimit: 6,
                        font: { size: 8 }
                    },
                    grid: { color: "rgba(100,120,160,.08)" }
                },
                y: {
                    ticks: {
                        color: "#647596",
                        font: { size: 8 }
                    },
                    grid: { color: "rgba(100,120,160,.08)" }
                }
            }
        }
    });
}

function renderReadings(record) {
    if (!record) return;

    const values = [
        {
            cls: "temp",
            label: "🌡 Temperature",
            value: record.temperature,
            unit: "°C",
            change: "Live reading"
        },
        {
            cls: "humidity",
            label: "💧 Humidity",
            value: record.humidity,
            unit: "%",
            change: "Live reading"
        },
        {
            cls: "voltage",
            label: "⚡ Voltage",
            value: record.voltage,
            unit: "V",
            change: "Live reading"
        },
        {
            cls: "pressure",
            label: "◉ Pressure",
            value: record.pressure,
            unit: "hPa",
            change: "Live reading"
        }
    ];

    document.getElementById("currentReadings").innerHTML = values.map(item => `
        <div class="reading-card ${item.cls}">
            <div class="reading-label">${item.label}</div>
            <div class="reading-value">
                ${item.value ?? "-"}
                <span class="reading-unit">${item.unit}</span>
            </div>
            <div class="reading-change">● ${item.change}</div>
        </div>
    `).join("");
}

function renderDevice(device, statusData) {
    const status = statusData.status || device.status || "OFFLINE";

    document.getElementById("deviceDetails").innerHTML = `
        <div class="device-hero">

            <div class="device-icon">♨</div>

            <div class="device-main">
                <h1>${device.name}</h1>
                <p class="device-id">${device.device_id}</p>

                <span class="status-badge ${statusClass(status)}">
                    ● ${status}
                </span>

                <p class="device-description">
                    Industrial temperature and environmental monitor
                </p>
            </div>

            <div class="last-seen-box">
                <span>LAST SEEN</span>
                <strong>${formatTime(statusData.last_seen || device.last_seen)}</strong>
                <small>Live updates every 2 seconds</small>
            </div>

        </div>

        <div class="device-meta">

            <div class="meta-item">
                <div class="meta-label">Device Type</div>
                <div class="meta-value">${device.device_type || "N/A"}</div>
            </div>

            <div class="meta-item">
                <div class="meta-label">Location</div>
                <div class="meta-value">${device.location || "N/A"}</div>
            </div>

            <div class="meta-item">
                <div class="meta-label">Firmware</div>
                <div class="meta-value">${device.firmware_version || "N/A"}</div>
            </div>

            <div class="meta-item">
                <div class="meta-label">Last Seen</div>
                <div class="meta-value">${formatTime(statusData.last_seen || device.last_seen)}</div>
            </div>

        </div>
    `;
}

async function loadDevice() {
    if (!deviceId) return;

    try {
        const [deviceResponse, statusResponse] = await Promise.all([
            fetch(`${API_BASE_URL}/devices/${deviceId}`),
            fetch(`${API_BASE_URL}/devices/${deviceId}/status`)
        ]);

        if (!deviceResponse.ok) {
            throw new Error("Device not found");
        }

        const device = await deviceResponse.json();
        const statusData = statusResponse.ok
            ? await statusResponse.json()
            : device;

        renderDevice(device, statusData);

    } catch (error) {
        document.getElementById("deviceDetails").innerHTML = `
            <div class="error-box">Unable to load device.</div>
        `;
    }
}

async function loadTelemetry() {
    if (!deviceId) return;

    try {
        const response = await fetch(
            `${API_BASE_URL}/devices/${deviceId}/telemetry?limit=30`
        );

        if (!response.ok) {
            throw new Error("Telemetry unavailable");
        }

        const records = await response.json();

        if (!records.length) {
            document.getElementById("currentReadings").innerHTML =
                `<div class="empty-box">No telemetry available.</div>`;

            document.getElementById("telemetryContainer").innerHTML =
                `<div class="empty-box">No telemetry available.</div>`;

            return;
        }

        const latest = records[0];

        renderReadings(latest);

        renderChart(
            "temperatureChart",
            records,
            "temperature",
            "Temperature",
            "#ff654d",
            "°C"
        );

        renderChart(
            "humidityChart",
            records,
            "humidity",
            "Humidity",
            "#299cff",
            "%"
        );

        renderChart(
            "voltageChart",
            records,
            "voltage",
            "Voltage",
            "#1de79a",
            "V"
        );

        renderChart(
            "pressureChart",
            records,
            "pressure",
            "Pressure",
            "#b15cff",
            "hPa"
        );

        const latestTen = records.slice(0, 10);

        document.getElementById("telemetryContainer").innerHTML = `
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Time</th>
                            <th>Temperature</th>
                            <th>Humidity</th>
                            <th>Voltage</th>
                            <th>Pressure</th>
                        </tr>
                    </thead>

                    <tbody>
                        ${latestTen.map((record, index) => `
                            <tr>
                                <td><span class="dot"></span></td>
                                <td>${formatTime(record.timestamp)}</td>
                                <td class="temp-text">${record.temperature ?? "-"} °C</td>
                                <td class="humidity-text">${record.humidity ?? "-"} %</td>
                                <td class="voltage-text">${record.voltage ?? "-"} V</td>
                                <td class="pressure-text">${record.pressure ?? "-"} hPa</td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            </div>
        `;

    } catch (error) {
        document.getElementById("telemetryContainer").innerHTML = `
            <div class="error-box">Unable to load telemetry.</div>
        `;
    }
}

async function refreshPage() {
    await Promise.all([
        loadDevice(),
        loadTelemetry()
    ]);
}

refreshPage();

setInterval(refreshPage, 2000);
