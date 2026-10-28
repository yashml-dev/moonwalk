
import streamlit as st

HTML = """
<div class="mw-gps" role="status" aria-live="polite">
  <span class="mw-gps-dot" aria-hidden="true"></span>
  <strong id="location-status">Requesting location permission&hellip;</strong>
  <span id="location-coordinates">Waiting for GPS</span>
</div>
"""

CSS = """
.mw-gps{display:flex;align-items:center;gap:.6rem;flex-wrap:wrap;font:700 11px/1.4 'Manrope','Helvetica Neue',Arial,sans-serif;
  letter-spacing:.14em;text-transform:uppercase;color:#171717;padding:.2rem 0}
.mw-gps-dot{width:10px;height:10px;border-radius:50%;background:#777}
.mw-gps.on .mw-gps-dot{background:#FF4D32}
#location-coordinates{color:#5C5C5C;font-weight:500;letter-spacing:.08em}
"""

JS = """
export default function(component) {
    const { parentElement, setStateValue } = component;
    const status = parentElement.querySelector("#location-status");
    const coords = parentElement.querySelector("#location-coordinates");
    const box = parentElement.querySelector(".mw-gps");

    if (!navigator.geolocation) {
        status.textContent = "GPS unavailable";
        coords.textContent = "This browser has no geolocation support.";
        setStateValue("error", {code: 0, message: "Geolocation is not supported by this browser."});
        return;
    }

    // Only push a new fix to Python when it is meaningfully better or different. Every push
    // reruns the Streamlit script, so this keeps an in-progress scan from being interrupted.
    let last = null;
    function worthSending(p) {
        if (!last) return true;
        const R = 6371000, toRad = d => d * Math.PI / 180;
        const dLat = toRad(p.latitude - last.latitude), dLon = toRad(p.longitude - last.longitude);
        const a = Math.sin(dLat/2)**2 + Math.cos(toRad(last.latitude)) * Math.cos(toRad(p.latitude)) * Math.sin(dLon/2)**2;
        const dist = 2 * R * Math.asin(Math.sqrt(a));
        return dist > 25 || p.accuracy < last.accuracy * 0.8;
    }

    const watchId = navigator.geolocation.watchPosition(
        function(position) {
            const location = {
                latitude: position.coords.latitude,
                longitude: position.coords.longitude,
                accuracy: position.coords.accuracy,
                timestamp: position.timestamp
            };

            box.classList.add("on");
            status.textContent = "GPS locked";
            coords.textContent = "Accuracy \u00b1" + Math.round(location.accuracy) + " m";
            if (worthSending(location)) {
                last = location;
                setStateValue("error", null);
                setStateValue("location", location);
            }
        },
        function(error) {
            box.classList.remove("on");
            status.textContent = error.code === 1 ? "Location permission denied" : "Location unavailable";
            coords.textContent = "";
            setStateValue("error", {code: error.code, message: error.message});
        },
        {
            enableHighAccuracy: true,
            maximumAge: 5000,
            timeout: 15000
        }
    );

    return () => navigator.geolocation.clearWatch(watchId);
}
"""

_location_component = st.components.v2.component(
    "pothole_location_tracker",
    html=HTML,
    css=CSS,
    js=JS,
)


def location_tracker():
    return _location_component(
        key="pothole_location",
        on_location_change=lambda: None,
        on_error_change=lambda: None,
    )
