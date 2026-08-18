const API_URL = "http://127.0.0.1:8000";

const REFRESH_INTERVAL = 3000;


/* =========================================
   API
========================================= */

async function getDevices() {

    const response = await fetch(
        `${API_URL}/devices`
    );

    if (!response.ok) {
        throw new Error("Failed to fetch devices");
    }

    return await response.json();
}


async function getTelemetry(deviceId) {

    try {

        const response = await fetch(
            `${API_URL}/devices/${encodeURIComponent(deviceId)}/telemetry?limit=1`
        );

        if (!response.ok) {
            return [];
        }

        return await response.json();

    } catch (error) {

        console.error(
            `Telemetry error for ${deviceId}:`,
            error
        );

        return [];
    }
}


async function getStatus(deviceId) {

    try {

        const response = await fetch(
            `${API_URL}/devices/${encodeURIComponent(deviceId)}/status`
        );

        if (!response.ok) {
            return null;
        }

        return await response.json();

    } catch (error) {

        console.error(
            `Status error for ${deviceId}:`,
            error
        );

        return null;
    }
}


/* =========================================
   HELPERS
========================================= */

function formatValue(value, unit = "") {

    if (
        value === null ||
        value === undefined ||
        Number.isNaN(Number(value))
    ) {
        return "--";
    }

    return `${Number(value).toFixed(2)} ${unit}`;
}


function formatLastSeen(value) {

    if (!value) {
        return "Never";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return "Unknown";
    }

    return date.toLocaleString(
        "en-IN",
        {
            day: "2-digit",
            month: "short",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit"
        }
    );
}


/* =========================================
   DEVICE CARD
========================================= */

function createDeviceCard(
    device,
    telemetry,
    statusData
) {

    const latest =
        telemetry.length > 0
            ? telemetry[0]
            : null;


    const status =
        statusData?.status || "OFFLINE";


    const statusClass =
        status === "ONLINE"
            ? "status-online"
            : "status-offline";


    const lastSeen =
        statusData?.last_seen
            ? formatLastSeen(statusData.last_seen)
            : "Never";


    return `

        <div
            class="device-card"
            onclick="openDevice('${device.device_id}')"
        >

            <div class="device-header">

                <div>

                    <div class="device-name">
                        ${escapeHtml(device.name)}
                    </div>

                    <div class="device-info">
                        ${escapeHtml(device.device_id)}
                    </div>

                </div>


                <div class="status ${statusClass}">
                    ${status}
                </div>

            </div>


            <div class="telemetry">

                <div class="metric">

                    <span class="metric-label">
                        Temperature
                    </span>

                    <span class="metric-value">
                        ${
                            latest
                                ? formatValue(
                                    latest.temperature,
                                    "°C"
                                )
                                : "--"
                        }
                    </span>

                </div>


                <div class="metric">

                    <span class="metric-label">
                        Humidity
                    </span>

                    <span class="metric-value">
                        ${
                            latest
                                ? formatValue(
                                    latest.humidity,
                                    "%"
                                )
                                : "--"
                        }
                    </span>

                </div>


                <div class="metric">

                    <span class="metric-label">
                        Voltage
                    </span>

                    <span class="metric-value">
                        ${
                            latest
                                ? formatValue(
                                    latest.voltage,
                                    "V"
                                )
                                : "--"
                        }
                    </span>

                </div>


                <div class="metric">

                    <span class="metric-label">
                        Pressure
                    </span>

                    <span class="metric-value">
                        ${
                            latest
                                ? formatValue(
                                    latest.pressure,
                                    "hPa"
                                )
                                : "--"
                        }
                    </span>

                </div>

            </div>


            <div class="device-footer">

                <div class="device-type">
                    Type:
                    <strong>
                        ${escapeHtml(device.device_type)}
                    </strong>
                </div>

                <div class="last-seen">

                    Last seen<br>

                    <strong>
                        ${lastSeen}
                    </strong>

                </div>

            </div>

        </div>

    `;
}


/* =========================================
   LOAD DASHBOARD
========================================= */

async function loadDashboard() {

    const container =
        document.getElementById(
            "device-container"
        );


    try {

        const devices =
            await getDevices();


        /*
         * Get status + telemetry for all devices
         * in parallel instead of one-by-one.
         */

        const deviceData =
            await Promise.all(

                devices.map(
                    async (device) => {

                        const [
                            statusData,
                            telemetry
                        ] = await Promise.all([
                            getStatus(
                                device.device_id
                            ),
                            getTelemetry(
                                device.device_id
                            )
                        ]);


                        return {
                            device,
                            statusData,
                            telemetry
                        };
                    }
                )
            );


        let online = 0;
        let offline = 0;


        deviceData.forEach(
            ({ statusData }) => {

                if (
                    statusData?.status ===
                    "ONLINE"
                ) {

                    online++;

                } else {

                    offline++;
                }
            }
        );


        /*
         * Update summary
         */

        document.getElementById(
            "total-devices"
        ).textContent = devices.length;


        document.getElementById(
            "online-devices"
        ).textContent = online;


        document.getElementById(
            "offline-devices"
        ).textContent = offline;


        document.getElementById(
            "device-count"
        ).textContent =
            `${devices.length} ${
                devices.length === 1
                    ? "device"
                    : "devices"
            }`;


        /*
         * Empty state
         */

        if (devices.length === 0) {

            container.innerHTML = `
                <div class="empty-box">
                    No devices registered yet.
                </div>
            `;

            return;
        }


        /*
         * Render all cards at once
         */

        container.innerHTML =
            deviceData
                .map(
                    ({
                        device,
                        statusData,
                        telemetry
                    }) =>
                        createDeviceCard(
                            device,
                            telemetry,
                            statusData
                        )
                )
                .join("");


    } catch (error) {

        console.error(
            "Dashboard error:",
            error
        );


        container.innerHTML = `
            <div class="error-box">
                Unable to connect to FastAPI.
                <br>
                <small>
                    Make sure the backend is running.
                </small>
            </div>
        `;


        document.getElementById(
            "total-devices"
        ).textContent = "0";


        document.getElementById(
            "online-devices"
        ).textContent = "0";


        document.getElementById(
            "offline-devices"
        ).textContent = "0";

    }
}


/* =========================================
   OPEN DEVICE
========================================= */

function openDevice(deviceId) {

    window.location.href =
        `device.html?id=${encodeURIComponent(deviceId)}`;
}


/* =========================================
   BASIC HTML ESCAPE
========================================= */

function escapeHtml(value) {

    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


/* =========================================
   INITIAL LOAD
========================================= */

loadDashboard();


/* =========================================
   LIVE REFRESH
========================================= */

setInterval(
    loadDashboard,
    REFRESH_INTERVAL
);