const API_URL = "http://127.0.0.1:8000";


async function getDevices() {

    const response = await fetch(`${API_URL}/devices`);

    if (!response.ok) {
        throw new Error("Failed to fetch devices");
    }

    return await response.json();
}


async function getTelemetry(deviceId) {

    const response = await fetch(
        `${API_URL}/devices/${deviceId}/telemetry?limit=1`
    );

    if (!response.ok) {
        return [];
    }

    return await response.json();
}


async function getStatus(deviceId) {

    const response = await fetch(
        `${API_URL}/devices/${deviceId}/status`
    );

    if (!response.ok) {
        return null;
    }

    return await response.json();
}


function formatValue(value, unit = "") {

    if (value === null || value === undefined) {
        return "--";
    }

    return `${Number(value).toFixed(2)} ${unit}`;
}


function createDeviceCard(device, telemetry, statusData) {

    const latest = telemetry.length > 0
        ? telemetry[0]
        : null;

    const status = statusData
        ? statusData.status
        : "OFFLINE";

    const statusClass = status === "ONLINE"
        ? "status-online"
        : "status-offline";

    const lastSeen = statusData && statusData.last_seen
        ? new Date(statusData.last_seen).toLocaleString()
        : "Never";

    return `

        <div
            class="device-card"
            onclick="openDevice('${device.device_id}')"
        >

            <div class="device-header">

                <div class="device-name">
                    ${device.name}
                </div>

                <div class="status ${statusClass}">
                    ${status}
                </div>

            </div>

            <div class="device-info">
                ${device.device_id}
            </div>

            <div class="telemetry">

                <div class="metric">
                    <span class="metric-label">
                        Temperature
                    </span>

                    <span class="metric-value">
                        ${latest
                            ? formatValue(latest.temperature, "°C")
                            : "--"}
                    </span>
                </div>


                <div class="metric">
                    <span class="metric-label">
                        Humidity
                    </span>

                    <span class="metric-value">
                        ${latest
                            ? formatValue(latest.humidity, "%")
                            : "--"}
                    </span>
                </div>


                <div class="metric">
                    <span class="metric-label">
                        Voltage
                    </span>

                    <span class="metric-value">
                        ${latest
                            ? formatValue(latest.voltage, "V")
                            : "--"}
                    </span>
                </div>


                <div class="metric">
                    <span class="metric-label">
                        Pressure
                    </span>

                    <span class="metric-value">
                        ${latest
                            ? formatValue(latest.pressure, "hPa")
                            : "--"}
                    </span>
                </div>

            </div>

            <div class="device-info">
                Type: ${device.device_type}
            </div>

            <div class="device-info last-seen">
                Last seen: ${lastSeen}
            </div>

        </div>
    `;
}


async function loadDashboard() {

    try {

        const devices = await getDevices();

        let online = 0;
        let offline = 0;

        const container =
            document.getElementById("device-container");

        container.innerHTML = "";

        for (const device of devices) {

            const statusData =
                await getStatus(device.device_id);

            if (statusData?.status === "ONLINE") {
                online++;
            } else {
                offline++;
            }

            const telemetry =
                await getTelemetry(device.device_id);

            container.innerHTML +=
                createDeviceCard(
                    device,
                    telemetry,
                    statusData
                );
        }


        document.getElementById("total-devices")
            .textContent = devices.length;

        document.getElementById("online-devices")
            .textContent = online;

        document.getElementById("offline-devices")
            .textContent = offline;


        if (devices.length === 0) {

            container.innerHTML =
                "<p>No devices registered.</p>";
        }

    } catch (error) {

        console.error(error);

        document.getElementById("device-container")
            .innerHTML =
            "<p>Unable to connect to FastAPI.</p>";
    }
}

function openDevice(deviceId) {

    window.location.href =
        `device.html?id=${encodeURIComponent(deviceId)}`;
}

// Initial load
loadDashboard();


// Refresh every 3 seconds
setInterval(loadDashboard, 3000);