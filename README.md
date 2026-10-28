# MOONWALK

**Urban infrastructure / field reporting.** Bad roads. Good receipts.

MOONWALK is a street-editorial Streamlit app that extends the existing YOLO pothole detector with browser location, reverse geocoding, cautious road-authority guidance, and a downloadable complaint-ready PDF.

## Features

- Keeps the supplied `best.pt` model and existing image/video detection workflow.
- Browser geolocation using the existing Streamlit v2 custom component; shows latitude, longitude, accuracy, and time.
- Optional manual coordinates for cases where the device is not standing beside the pothole.
- Cached OpenStreetMap Nominatim reverse geocoding, with graceful failure handling.
- Map preview and a link to open the selected coordinates in OpenStreetMap.
- Authority guidance links for PMC/PCMC; suggestions are explicitly tentative because road ownership can vary by road.
- Official Google Play listing links for PMC Road Mitra / PCMC Pothole Management where an address keyword match suggests the relevant municipality. These links open app listings, not complaint forms; the user must complete submission in the official channel.
- Contractor lookup does **not** invent names. It directs users to official Maharashtra e-Tenders when no verified road-specific record is bundled.
- Redesigned street-editorial interface (MOONWALK) with scanning state, real video progress, and a report-ready screen.
- Video scans pick the frame with the most detections as report evidence.
- PDF report (MOONWALK-branded) with annotated image, coordinates, accuracy, address, authority guidance, reporting-app listing, detection count, and limitations.
- Downloadable JSON report metadata for reuse, auditing, or future backend integration.
- Does not automatically submit complaints or store a server-side report history.

## Requirements

- Windows 10/11, Python 3.10–3.12 recommended.
- Internet for dependency installation and reverse geocoding.
- Browser location permission. Geolocation works on `localhost` or a deployed HTTPS site; on a phone, use an HTTPS deployment to obtain location.
- CPU inference is supported; CUDA is not required. Video processing can be slow on CPU; clips longer than 120 seconds are rejected to prevent a long, unresponsive scan.

## Fast Windows setup

- Run `SETUP_MOONWALK.bat` once to create `.venv`, install dependencies, and launch the app.
- Later, run `RUN_MOONWALK.bat` to launch it without reinstalling packages.
- If you prefer the terminal, use the PowerShell steps below.

## Windows setup (PowerShell)

Open PowerShell in the extracted project folder:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run PotholeDetectionApp.py
```

If PowerShell blocks activation, run this for the current terminal only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

The app opens at `http://localhost:8501`. Allow location access when prompted. Keep `best.pt` in the same folder as `PotholeDetectionApp.py`.

## Run the GPS component test

```powershell
streamlit run test_location.py
```

## Build a source ZIP

```powershell
.\build_package.ps1
```

This creates `MOONWALK.zip` in the project folder and excludes `.venv`, `.git`, Python caches, and temporary output. The supplied model weights and sample images are included by default.

## Responsible use and limitations

- Device GPS is not guaranteed to be the exact pothole location. Confirm or manually adjust coordinates before generating a report.
- Reverse geocoding uses the public OpenStreetMap Nominatim service. It requires network access, is rate-limited, and receives the coordinates being looked up. Results may be incomplete or approximate; responses are cached for 24 hours.
- The authority helper uses address text only as a rough hint. It does not establish legal road ownership; roads inside municipal limits may be controlled by PWD, highways agencies, cantonments, or other bodies. The app listings and authority websites are starting points only. Verify the exact road before filing.
- No verified road-specific contractor data is bundled. Contractor names are deliberately not guessed. Check the [Maharashtra e-Tenders portal](https://mahatenders.gov.in/) and match the exact work package.
- The model can produce false positives or miss potholes. Review detections before reporting.
- The app prepares a PDF only; it does not automatically submit a complaint, email anyone, or retain a report database.

## Official starting points

Links go to each authority's official website. MOONWALK does not know their complaint-form URLs, so look for the complaint or grievance section there.


- [Pune Municipal Corporation](https://www.pmc.gov.in/)
- [Pimpri-Chinchwad Municipal Corporation](https://www.pcmcindia.gov.in/)
- [Maharashtra e-Tenders](https://mahatenders.gov.in/)
- [Maharashtra State Grievance Portal](https://grievances.maharashtra.gov.in/)
- [PMC Road Mitra app (Google Play)](https://play.google.com/store/apps/details?id=com.nyatitechnologies.pmcroadmitra)
- [PCMC Pothole Management app (Google Play)](https://play.google.com/store/apps/details?id=io.framework7.pcmcpotholemanagement)
- [OpenStreetMap](https://www.openstreetmap.org/)

## Project files

- `PotholeDetectionApp.py` — the MOONWALK Streamlit app (file name kept so existing run commands keep working).
- `moonwalk_ui.py` — MOONWALK design system: scoped CSS and HTML building blocks.
- `detection_pipeline.py` — image/video detection helpers around the YOLO model.
- `.streamlit/config.toml` — theme and upload settings.
- `DESIGN.md` — design direction.
- `location_component.py` — browser geolocation custom component.
- `authority_lookup.py` — cautious authority and contractor guidance.
- `report_generator.py` — PDF creation.
- `test_location.py` — location component test page.
- `build_package.ps1` — reproducible ZIP builder.
- `SETUP_MOONWALK.bat` / `RUN_MOONWALK.bat` — Windows setup and launch helpers.
- `best.pt` — original model weights.
