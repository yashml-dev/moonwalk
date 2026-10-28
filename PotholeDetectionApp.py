# MOONWALK — street-editorial field reporting: YOLO detection + browser location + complaint PDF.
# (File name kept as PotholeDetectionApp.py so existing run commands and packaging keep working.)
from __future__ import annotations

import base64
import gc
import json
import os
import tempfile
from datetime import datetime
from html import escape
from pathlib import Path

import cv2
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
from ultralytics import YOLO

import moonwalk_ui as ui
from authority_lookup import suggest_authority, contractor_status, alternate_channels
from detection_pipeline import IMAGE_EXTS, VIDEO_EXTS, scan_image, scan_video
from location_component import location_tracker
from report_generator import generate_report

st.set_page_config(page_title="MOONWALK — Urban infrastructure / field reporting",  layout="wide")
ui.inject_theme()

# Native mobile camera picker (opens the device camera only after a user tap).
native_camera = components.declare_component(
    "moonwalk_native_camera",
    path=str(Path(__file__).resolve().parent / "native_camera_component"),
)

DEFAULT_START = (18.5204, 73.8567)  # Pune centre; only a starting point for manual entry


# ----------------------------------------------------------------------------- helpers
@st.cache_resource
def load_model():
    model_path = Path(__file__).resolve().parent / "best.pt"
    if not model_path.exists():
        raise FileNotFoundError(f"Model weights not found: {model_path}. Place best.pt beside this app.")
    return YOLO(str(model_path))


def _geolocator():
    from geopy.geocoders import Nominatim
    contact = os.environ.get("MOONWALK_CONTACT", "")
    agent = "moonwalk-field-reporting/1.0" + (f" ({contact})" if contact else "")
    return Nominatim(user_agent=agent, timeout=8)


@st.cache_data(ttl=86400, show_spinner=False)
def reverse_geocode(lat: float, lon: float):
    """Cached Nominatim lookup. Only called for the coordinates selected for the report."""
    place = _geolocator().reverse((lat, lon), exactly_one=True, language="en", zoom=18)
    return place.address if place else None


@st.cache_data(ttl=86400, show_spinner=False)
def forward_geocode(query: str):
    place = _geolocator().geocode(query, exactly_one=True, language="en")
    return (place.latitude, place.longitude, place.address) if place else None


def data_uri(img_bytes: bytes, max_side: int = 1200) -> str:
    arr = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
    if arr is None:
        return ""
    h, w = arr.shape[:2]
    if max(h, w) > max_side:
        s = max_side / max(h, w)
        arr = cv2.resize(arr, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", arr, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode() if ok else ""


def pct_list(confs, n=5) -> str:
    return " · ".join(f"{c * 100:.0f}%" for c in confs[:n])


def search_location():
    q = (st.session_state.get("m_query") or "").strip()
    if not q:
        st.session_state["m_msg"] = ("warn", "Type an address or landmark first.")
        return
    try:
        hit = forward_geocode(q)
    except Exception:
        st.session_state["m_msg"] = ("warn", "Search is unavailable right now. Enter coordinates instead.")
        return
    if not hit:
        st.session_state["m_msg"] = ("warn", "Nothing found for that search. Try a nearby landmark or enter coordinates.")
        return
    st.session_state["m_lat"], st.session_state["m_lon"] = round(hit[0], 6), round(hit[1], 6)
    st.session_state["m_msg"] = ("ok", f"Pin moved to: {hit[2]}")


def seed_manual_from_gps():
    loc = st.session_state.get("_gps")
    if loc and st.session_state.get("manual"):
        st.session_state["m_lat"], st.session_state["m_lon"] = round(loc[0], 6), round(loc[1], 6)


# ----------------------------------------------------------------------------- shell
ui.masthead()
ui.hero(datetime.now().strftime("%d.%m.%y"))

try:
    model = load_model()
except Exception as exc:
    ui.note("err", "Model not loaded", f"MOONWALK could not load its detection model. {escape(str(exc))}")
    st.stop()

# ----------------------------------------------------------------------------- 01 evidence
ui.section("scan", "01", "Evidence", "Drop the<br><em>damage</em>.")
col_l, col_r = st.columns([4, 8], gap="large")
with col_l:
    ui.html("""
    <ol class="mw-steps">
      <li><b>01</b><span>Add a photo or short clip of the road.</span></li>
      <li><b>02</b><span>Scan it. The model runs on this server, nothing is faked.</span></li>
      <li><b>03</b><span>Check the pin, then prepare your report.</span></li>
    </ol>
    <div class="mw-types" aria-label="Accepted file types"><span>JPG</span><span>PNG</span><span>MP4</span><span>MOV</span><span>AVI</span></div>
    """)
    with st.expander("Scan sensitivity"):
        conf_thresh = st.slider("Confidence threshold", 0.10, 1.00, 0.25, 0.05,
                                help="Lower values find more candidates but also more false alarms.")
        st.caption("Lower finds more, including false alarms. Higher is stricter.")

with col_r:
    input_method = st.radio(
        "Input method",
        ["📁 Browse files", "📷 Take a photo"],
        horizontal=True,
        key="image_input_method",
        label_visibility="collapsed",
    )

    uploaded = None
    camera_capture = None

    if input_method == "📷 Take a photo":
        camera_capture = native_camera(
            label="Open phone camera",
            key="native_camera_capture",
            default=None,
        )
        if camera_capture and camera_capture.get("data"):
            try:
                raw = base64.b64decode(camera_capture["data"])
                upload_name = camera_capture.get("name") or "camera_capture.jpg"
            except Exception:
                raw = b""
                upload_name = "camera_capture.jpg"
        else:
            raw = b""
            upload_name = ""
    else:
        uploaded = st.file_uploader(
            "Road image or video",
            type=["jpg", "jpeg", "png", "mp4", "mov", "avi"],
            key="evidence",
            label_visibility="collapsed",
        )
        if uploaded is not None:
            raw = uploaded.getvalue()
            upload_name = getattr(uploaded, "name", None) or "uploaded_evidence"
        else:
            raw = b""
            upload_name = ""

    preview_ph = st.empty()
    progress_ph = st.empty()
    file_key = None
    valid_upload = False
    ext = Path(upload_name).suffix.lower() if upload_name else ""

    if upload_name:
        file_key = (upload_name, len(raw), round(float(conf_thresh), 2))

        if not raw:
            ui.note(
                "err",
                "Empty file",
                "This file has no data. Capture or choose another file.",
                preview_ph,
            )
        elif ext in IMAGE_EXTS:
            if cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR) is None:
                ui.note(
                    "err",
                    "Can't read this image",
                    "The file looks damaged or isn't a real image. Try a JPG or PNG.",
                    preview_ph,
                )
            else:
                valid_upload = True
                with preview_ph.container():
                    st.image(raw, width="stretch")
        elif ext in VIDEO_EXTS:
            valid_upload = True
            with preview_ph.container():
                st.video(raw)
                st.caption(
                    "Video scans every frame (maximum 120 seconds). "
                    "CPU-only scans can take a while; a short, clear clip works best."
                )
        else:
            ui.note(
                "err",
                "Unsupported file",
                "Use JPG, PNG, MP4, MOV or AVI.",
                preview_ph,
            )

    go = st.button(
        "Scan the damage",
        type="primary",
        disabled=not valid_upload,
        key="go_scan",
    )

    if go and valid_upload:
        st.session_state.pop("report", None)
        st.session_state.pop("scan", None)
        try:
            with tempfile.TemporaryDirectory(prefix="moonwalk_") as tmp:
                in_path = os.path.join(tmp, Path(upload_name).name)
                with open(in_path, "wb") as fh:
                    fh.write(raw)

                if ext in IMAGE_EXTS:
                    preview_ph.markdown(
                        ui.scan_overlay(data_uri(raw), "Scanning · model running"),
                        unsafe_allow_html=True,
                    )
                    res = scan_image(model, in_path, float(conf_thresh))
                else:
                    cap = cv2.VideoCapture(in_path)
                    ok, first = cap.read()
                    cap.release()
                    if ok:
                        okj, jb = cv2.imencode(".jpg", first)
                        if okj:
                            preview_ph.markdown(
                                ui.scan_overlay(data_uri(jb.tobytes()), "Scanning · frame by frame"),
                                unsafe_allow_html=True,
                            )
                    last_pct = {"v": -1}

                    def on_progress(done, total):
                        pct = int(100 * done / max(total, 1))
                        if pct != last_pct["v"]:
                            last_pct["v"] = pct
                            progress_ph.markdown(
                                ui.progress_bar(done, total),
                                unsafe_allow_html=True,
                            )

                    res = scan_video(
                        model,
                        in_path,
                        os.path.join(tmp, "moonwalk_detected.mp4"),
                        float(conf_thresh),
                        on_progress,
                    )

            st.session_state["scan"] = {
                "res": res,
                "key": file_key,
                "name": upload_name,
            }
        except Exception as exc:
            preview_ph.empty()
            progress_ph.empty()
            ui.note(
                "err",
                "Scan failed",
                f"MOONWALK couldn't process this file. Try another one. "
                f"<br><small>{escape(str(exc))}</small>",
            )
        finally:
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass
            gc.collect()

        if "scan" in st.session_state:
            st.rerun()

scan = st.session_state.get("scan")
if scan and scan["key"] != file_key:
    scan = None  # a different file / sensitivity is selected; the old result no longer applies

# ----------------------------------------------------------------------------- 01.1 result
if scan:
    res = scan["res"]
    count = res.count
    ui.section("result", "01.1", "Result",
               "Candidates<br><em>spotted</em>." if count else "Nothing<br>spotted.")
    r_img, r_txt = st.columns([7, 5], gap="large")
    with r_img:
        ui.html(f'<div class="mw-frame mw-reveal"><img src="data:image/jpeg;base64,{base64.b64encode(res.annotated_jpg).decode()}" '
                f'alt="Photo with {count} detected pothole candidate{"s" if count != 1 else ""} outlined"></div>')
        ui.html('<div class="mw-meta" style="margin-top:.5rem">Fig. 02 / '
                + ("Evidence frame · most potholes in a single frame" if res.kind == "video" else "Annotated detection") + '</div>')
    with r_txt:
        ui.html(f'<div class="mw-count {"" if count else "zero"}" aria-hidden="true">{count:02d}</div>'
                f'<div class="mw-label">Pothole candidate{"s" if count != 1 else ""}'
                f'{" · most in one frame" if res.kind == "video" else ""}</div>')
        rows = []
        if res.confidences:
            rows.append(("Model confidence", pct_list(res.confidences), False))
        if res.kind == "video":
            rows.append(("Frames scanned", f"{res.frames}", False))
        rows.append(("Sensitivity", f"{scan['key'][2]:.2f} threshold", False))
        ui.facts(rows)
        if count:
            ui.note("", "How to read this",
                    "Outlined boxes mark where the model thinks a pothole is. It can be wrong, so look before you file."
                    + (" Video counts are per frame, not unique potholes across the clip." if res.kind == "video" else ""))
        else:
            ui.note("warn", "No potholes found at this sensitivity",
                    "Try a clearer, closer photo, or lower the threshold under <b style='display:inline;font-size:inherit;letter-spacing:0;text-transform:none'>Scan sensitivity</b> and scan again.")
        if res.kind == "image":
            st.download_button("Download annotated image", res.annotated_jpg, "moonwalk_detected.jpg", "image/jpeg", key="dl_img")
        else:
            st.download_button("Download evidence frame", res.annotated_jpg, "moonwalk_evidence_frame.jpg", "image/jpeg", key="dl_frame")
    if res.kind == "video":
        if res.video_playable:
            st.video(res.video_bytes)
        else:
            ui.note("", "Video preview unavailable", "This machine can't re-encode video for the browser. Download the annotated file to watch it.")
        st.download_button("Download annotated video", res.video_bytes, "moonwalk_detected.mp4", "video/mp4", key="dl_vid")

# ----------------------------------------------------------------------------- 02 location
ui.section("location", "02", "Location", "Pin it where<br>it <em>is</em>.")
loc_l, loc_r = st.columns([5, 7], gap="large")

loc_state = location_tracker()
location = getattr(loc_state, "location", None)
loc_error = getattr(loc_state, "error", None)

gps_lat = gps_lon = gps_acc = None
if isinstance(location, dict) and "latitude" in location and "longitude" in location:
    try:
        gps_lat, gps_lon = float(location["latitude"]), float(location["longitude"])
        gps_acc = float(location.get("accuracy", 0))
        st.session_state["_gps"] = (gps_lat, gps_lon)
    except (TypeError, ValueError):
        gps_lat = gps_lon = gps_acc = None

with loc_l:
    if gps_lat is None:
        if isinstance(loc_error, dict) and loc_error.get("code") == 1:
            ui.note("warn", "Location permission denied",
                    "Allow location for this site in your browser settings, or search an address / enter coordinates below.")
        elif isinstance(loc_error, dict):
            ui.note("warn", "GPS unavailable",
                    "Your device couldn't provide a location. Search an address or enter coordinates below.")
        else:
            ui.note("", "Waiting for GPS",
                    "Allow location when your browser asks. It needs HTTPS or localhost and can take a few seconds.")
    manual = False
    if gps_lat is not None:
        manual = st.checkbox("The pothole isn't where I'm standing. Adjust the pin.", key="manual", on_change=seed_manual_from_gps)
    else:
        manual = True

    report_lat = report_lon = report_acc = None
    if manual:
        st.session_state.setdefault("m_lat", DEFAULT_START[0] if gps_lat is None else round(gps_lat, 6))
        st.session_state.setdefault("m_lon", DEFAULT_START[1] if gps_lon is None else round(gps_lon, 6))
        st.text_input("Search an address or landmark", key="m_query", placeholder="e.g. FC Road, Pune")
        st.button("Find on map", key="find", on_click=search_location)
        msg = st.session_state.get("m_msg")
        if msg:
            ui.note("warn" if msg[0] == "warn" else "", "Search", escape(msg[1]))
        c1, c2 = st.columns(2)
        report_lat = c1.number_input("Latitude", key="m_lat", format="%.6f", min_value=-90.0, max_value=90.0, step=0.0001)
        report_lon = c2.number_input("Longitude", key="m_lon", format="%.6f", min_value=-180.0, max_value=180.0, step=0.0001)
        if gps_lat is None:
            st.caption("Starting point is central Pune. Search or edit the coordinates to move the pin.")
    else:
        report_lat, report_lon, report_acc = gps_lat, gps_lon, gps_acc

    address = None
    if report_lat is not None and report_lon is not None:
        try:
            address = reverse_geocode(round(float(report_lat), 5), round(float(report_lon), 5))
        except Exception:
            address = None

    if report_lat is not None:
        ui.facts([
            ("Address", escape(address) if address else "Not resolved. The report will use coordinates only.", True),
            ("Latitude", f"{report_lat:.6f}", False),
            ("Longitude", f"{report_lon:.6f}", False),
            ("GPS accuracy", f"±{report_acc:.0f} m" if report_acc is not None else "Not applicable (set manually)", False),
            ("Source", "Adjusted by you" if manual else "Browser device location", False),
        ])
        ui.note("warn", "Verify the pin",
                "GPS shows where your device is, which may not be exactly where the pothole is. Check the map and move the pin if needed.")
        st.link_button("Open in OpenStreetMap",
                       f"https://www.openstreetmap.org/?mlat={report_lat}&mlon={report_lon}#map=18/{report_lat}/{report_lon}")

with loc_r:
    if report_lat is not None and report_lon is not None:
        d = 0.0035
        src = (f"https://www.openstreetmap.org/export/embed.html?bbox={report_lon - d},{report_lat - d},"
               f"{report_lon + d},{report_lat + d}&layer=mapnik&marker={report_lat},{report_lon}")
        components.iframe(src, height=420)
        ui.html(f'<div class="mw-meta" style="margin-top:.4rem">Fig. 03 / Map · {report_lat:.5f}, {report_lon:.5f}</div>')
    else:
        ui.note("", "No pin yet", "The map appears as soon as GPS locks or you enter a location.")

# ----------------------------------------------------------------------------- 03 file a report
ui.section("file", "03", "Next step / File a report", "You file it.<br>We <em>prep</em> it.")
if not (scan and scan["res"].count > 0):
    ui.html('<div class="mw-lede">Scan a road photo or clip first. If potholes are found, your report options appear here.</div>')
else:
    res = scan["res"]
    authority = suggest_authority(address, report_lat, report_lon)
    contractor = contractor_status(address)
    f_l, f_r = st.columns([6, 6], gap="large")
    with f_l:
        ui.facts([("Likely authority", escape(authority["authority"]), True), ("Why", escape(authority["note"]), False)])
        ui.note("warn", "Road ownership not confirmed",
                "This is a keyword guess from the address, not a legal finding. Roads can belong to PMC, PCMC, state PWD, highways or cantonment bodies. Confirm the owner before you file.")
        st.link_button("Open official authority site ↗", authority["url"], type="primary")
        if authority.get("reporting_url"):
            st.link_button(f"{authority['reporting_label']} ↗", authority["reporting_url"], key="reporting_channel")
        ui.html('<div class="mw-meta" style="margin-top:.4rem">The app link opens an official app listing, not a web complaint form. Confirm road ownership and follow the authority\'s own filing steps.</div>')
    with f_r:
        alts = alternate_channels(authority["url"])
        if alts:
            ui.html('<div class="mw-meta">Alternate official channels</div>')
            for name, url in alts:
                st.link_button(f"{name} ↗", url, key=f"alt_{name}")
        ui.facts([("Contractor", escape(contractor["status"]), False), ("Note", escape(contractor["note"]), False)])
        st.link_button("Check Maharashtra e-Tenders ↗", contractor["url"], key="tenders")

    if not address:
        ui.note("", "Address not resolved", "The report will include coordinates only.")
    if report_lat is None:
        ui.note("warn", "No location set", "The report will say location is not available. Set the pin above first for a stronger report.")

    sig = (scan["key"], None if report_lat is None else round(report_lat, 6), None if report_lon is None else round(report_lon, 6), address)
    if st.button("Generate report", type="primary", key="gen_report"):
        now = datetime.now().astimezone()
        rid = "MW-" + now.strftime("%Y%m%d-%H%M%S")
        pdf = generate_report(
            res.annotated_jpg, latitude=report_lat, longitude=report_lon, accuracy=report_acc, address=address,
            authority=authority["authority"], complaint_url=authority["url"],
            reporting_url=authority.get("reporting_url"), detected_count=res.count,
            timestamp=now.strftime("%Y-%m-%d %H:%M:%S %Z"), manual_location=bool(manual),
            report_id=rid, confidences=res.confidences, source_kind=res.kind)
        st.session_state["report"] = {"pdf": pdf, "sig": sig, "id": rid, "stamp": now.strftime("%d %b %Y · %H:%M"),
                                      "authority": authority, "address": address, "lat": report_lat, "lon": report_lon,
                                      "acc": report_acc, "manual": bool(manual)}
    ui.html('<div class="mw-meta" style="margin-top:.4rem">Nothing is sent anywhere. You decide where and when to file.</div>')

    # ------------------------------------------------------------------------- 04 report ready
    report = st.session_state.get("report")
    if report and report["sig"] != sig:
        ui.note("warn", "Report out of date", "The location or evidence changed after your report was made. Generate it again.")
        report = None
    if report:
        ui.section("report", "04", "Report ready", "Receipts<br><em>ready</em>.")
        a = report["authority"]
        place = (report["address"] or "").split(",")[0].strip() or (
            f"{report['lat']:.4f}, {report['lon']:.4f}" if report["lat"] is not None else "Location not set")
        coords = (f"{report['lat']:.6f}, {report['lon']:.6f}" if report["lat"] is not None else "Not available")
        det = f"{res.count} candidate{'s' if res.count != 1 else ''}" + (" (most in one frame)" if res.kind == "video" else "")
        if res.confidences:
            det += f" · {pct_list(res.confidences, 3)}"
        img_b64 = base64.b64encode(res.annotated_jpg).decode()
        ui.html(f"""
        <article class="mw-report" aria-label="MOONWALK field report">
          <div class="mw-report-top">
            <div><span class="mw-word" style="font-size:1.2rem">MOONWALK<i aria-hidden="true"></i></span>
                 <div class="mw-meta">Field report / No. {escape(report['id'])}</div></div>
            <div class="mw-meta">{escape(report['stamp'])}</div>
          </div>
          <div class="mw-h3" role="heading" aria-level="3">Pothole damage<br>at {escape(place)}</div>
          <div class="mw-report-grid">
            <div class="mw-frame mw-reveal"><img src="data:image/jpeg;base64,{img_b64}" alt="Annotated evidence photo"></div>
            <dl class="mw-facts">
              <div><dt>Address</dt><dd>{escape(report['address']) if report['address'] else 'Not resolved'}</dd></div>
              <div><dt>Coordinates</dt><dd>{coords}</dd></div>
              <div><dt>Detection</dt><dd>{escape(det)}</dd></div>
              <div><dt>Likely authority</dt><dd>{escape(a['authority'])}</dd></div>
              <div><dt>Official portal</dt><dd><a href="{escape(a['url'])}" target="_blank" rel="noopener noreferrer">{escape(a['url'])}</a></dd></div>
              <div><dt>Status</dt><dd><span class="mw-stamp">Prepared · not submitted</span></dd></div>
            </dl>
          </div>
        </article>
        """)
        d1, d2, _ = st.columns([3, 3, 4])
        with d1:
            st.download_button("Download report", report["pdf"], "moonwalk_field_report.pdf", "application/pdf",
                               type="primary", key="dl_pdf")
        with d2:
            st.link_button("Open official authority site ↗", a["url"], key="report_portal")
        if a.get("reporting_url"):
            st.link_button(f"Open {a['reporting_label']} ↗", a["reporting_url"], key="reporting_channel_ready")
        report_data = {
            "brand": "MOONWALK",
            "report_id": report["id"],
            "created_at_local": report["stamp"],
            "status": "prepared_not_submitted",
            "evidence_file": scan.get("name"),
            "evidence_type": res.kind,
            "detected_candidates": res.count,
            "count_semantics": "maximum detections in one frame; not unique potholes across the clip" if res.kind == "video" else "detections in the uploaded image",
            "model_confidences": res.confidences,
            "confidence_threshold": scan["key"][2],
            "location": {
                "latitude": report["lat"],
                "longitude": report["lon"],
                "accuracy_m": report["acc"],
                "address": report["address"],
                "manually_adjusted": report["manual"],
                "openstreetmap_url": (f"https://www.openstreetmap.org/?mlat={report['lat']}&mlon={report['lon']}#map=18/{report['lat']}/{report['lon']}" if report["lat"] is not None and report["lon"] is not None else None),
            },
            "authority_guidance": {
                "suggestion": a["authority"],
                "official_site": a["url"],
                "reporting_channel": a.get("reporting_url"),
                "note": a["note"],
                "ownership_verified": False,
            },
            "submission": {"submitted": False, "note": "MOONWALK prepares evidence only; the user must submit through an official channel."},
        }
        st.download_button("Download report data (JSON)", json.dumps(report_data, indent=2, ensure_ascii=False),
                           f"{report['id'].lower()}_data.json", "application/json", key="dl_json")

# ----------------------------------------------------------------------------- privacy + footer
ui.section("privacy", "05", "Privacy & limits", "Your data,<br>your <em>call</em>.")
ui.html("""
<ul class="mw-steps" style="max-width:70ch;margin-left:0">
  <li><b>—</b><span>Browser location is requested only with your permission and used in this session to prepare your report.</span></li>
  <li><b>—</b><span>Looking up an address sends coordinates to OpenStreetMap&rsquo;s Nominatim service. Don&rsquo;t submit sensitive images.</span></li>
  <li><b>—</b><span>GPS shows the device location, which may differ from the pothole. Confirm or adjust the pin before reporting.</span></li>
  <li><b>—</b><span>MOONWALK never files or sends a complaint automatically.</span></li>
</ul>
""")
ui.footer()
