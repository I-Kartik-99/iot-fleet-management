const API_BASE_URL = "http://127.0.0.1:8000";

const params = new URLSearchParams(window.location.search);
const deviceId = params.get("id");


function formatTime(timestamp) {

    if (!timestamp) {
        return "Never";
    }

    const date = new Date(timestamp);

    return date.toLocaleString("en-IN", {
        dateStyle: "medium",
        timeStyle: "medium"
    });
}


function statusClass(status) {

    return status === "ONLINE"
        ? "status-online"
        : "status-offline";
}


async function loadDevice() {

    if (!deviceId) {
        return;
    }

    try {

        /*
         * Get device information
         */
        const deviceResponse = await fetch(
            `${API_BASE_URL}/devices/${deviceId}`
        );

        if (!deviceResponse.ok) {
            throw new Error("Device not found");
        }

        const device = await deviceResponse.json();


        /*
         * Get LIVE status
         */
        const statusResponse = await fetch(
            `${API_BASE_URL}/devices/${deviceId}/status`
        );

        let statusData = device;

        if (statusResponse.ok) {
            statusData = await statusResponse.json();
        }


        document.getElementById("deviceDetails").innerHTML = `

            <div class="device-title">

                <div>
                    <h1>${device.name}</h1>

                    <p class="device-id">
                        ${device.device_id}
                    </p>
                </div>

                <span class="status-badge ${statusClass(statusData.status)}">
                    ${statusData.status}
                </span>

            </div>


            <div class="device-info-grid">

                <div class="info-box">
                    <span>Device Type</span>
                    <strong>${device.device_type}</strong>
                </div>

                <div class="info-box">
                    <span>Location</span>
                    <strong>${device.location ?? "N/A"}</strong>
                </div>

                <div class="info-box">
                    <span>Firmware</span>
                    <strong>${device.firmware_version ?? "N/A"}</strong>
                </div>

                <div class="info-box">
                    <span>Last Seen</span>
                    <strong>
                        ${formatTime(statusData.last_seen)}
                    </strong>
                </div>

            </div>
        `;

    } catch (error) {

        document.getElementById("deviceDetails").innerHTML = `
            <div class="error-box">
                Unable to load device
            </div>
        `;
    }
}


async function loadTelemetry() {

    if (!deviceId) {
        return;
    }

    try {

        const response = await fetch(
            `${API_BASE_URL}/devices/${deviceId}/telemetry?limit=10`
        );

        if (!response.ok) {
            throw new Error("Telemetry unavailable");
        }

        const records = await response.json();


        if (records.length === 0) {

            document.getElementById("telemetryContainer").innerHTML = `
                <div class="empty-box">
                    No telemetry available.
                </div>
            `;

            return;
        }


        document.getElementById("telemetryContainer").innerHTML = `

            <div class="table-wrapper">

                <table>

                    <thead>

                        <tr>
                            <th>Time</th>
                            <th>Temperature</th>
                            <th>Humidity</th>
                            <th>Voltage</th>
                            <th>Pressure</th>
                        </tr>

                    </thead>

                    <tbody>

                        ${records.map(record => `

                            <tr>

                                <td>
                                    ${formatTime(record.timestamp)}
                                </td>

                                <td>
                                    <strong>
                                        ${record.temperature ?? "-"} °C
                                    </strong>
                                </td>

                                <td>
                                    ${record.humidity ?? "-"} %
                                </td>

                                <td>
                                    ${record.voltage ?? "-"} V
                                </td>

                                <td>
                                    ${record.pressure ?? "-"} hPa
                                </td>

                            </tr>

                        `).join("")}

                    </tbody>

                </table>

            </div>
        `;

    } catch (error) {

        document.getElementById("telemetryContainer").innerHTML = `
            <div class="error-box">
                Unable to load telemetry
            </div>
        `;
    }
}


/*
 * Initial load
 */
loadDevice();
loadTelemetry();


/*
 * Live update every 2 seconds
 */
setInterval(() => {

    loadDevice();
    loadTelemetry();

}, 2000);