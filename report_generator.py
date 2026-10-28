"""MOONWALK PDF field report generation."""
from datetime import datetime
from io import BytesIO
from html import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.utils import ImageReader

PAPER = colors.HexColor("#F7F6F2")
INK = colors.HexColor("#171717")
GREY = colors.HexColor("#5C5C5C")
RED = colors.HexColor("#FF4D32")


def _chrome(report_id):
    def draw(canvas, doc):
        w, h = A4
        canvas.saveState()
        canvas.setFillColor(INK)
        canvas.rect(0, h - 22*mm, w, 22*mm, stroke=0, fill=1)
        canvas.setFillColor(PAPER)
        canvas.setFont("Helvetica-Bold", 17)
        canvas.drawString(18*mm, h - 13.5*mm, "MOONWALK")
        from reportlab.pdfbase.pdfmetrics import stringWidth
        word_w = stringWidth("MOONWALK", "Helvetica-Bold", 17)
        canvas.setFillColor(RED)
        canvas.circle(18*mm + word_w + 2.2*mm, h - 13.5*mm + 0.9*mm, 1.2*mm, stroke=0, fill=1)
        canvas.setFillColor(PAPER)
        canvas.setFont("Helvetica-Bold", 7)
        canvas.drawRightString(w - 18*mm, h - 11*mm, "URBAN INFRASTRUCTURE / FIELD REPORTING")
        if report_id:
            canvas.drawRightString(w - 18*mm, h - 15.5*mm, f"REPORT No. {report_id}")
        canvas.setStrokeColor(INK)
        canvas.setLineWidth(0.6)
        canvas.line(18*mm, 12*mm, w - 18*mm, 12*mm)
        canvas.setFillColor(GREY)
        canvas.setFont("Helvetica", 7)
        canvas.drawString(18*mm, 8*mm, "MOONWALK - prepared on your device. Not submitted to any authority.")
        canvas.drawRightString(w - 18*mm, 8*mm, f"Page {doc.page}")
        canvas.restoreState()
    return draw


def generate_report(image_bytes, *, latitude=None, longitude=None, accuracy=None,
                    address=None, authority=None, complaint_url=None, reporting_url=None,
                    detected_count=None, timestamp=None, manual_location=False,
                    report_id=None, confidences=None, source_kind="image"):
    """Return a MOONWALK PDF report as bytes. image_bytes should be an image byte string."""
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm,
                            topMargin=32*mm, bottomMargin=18*mm,
                            title="MOONWALK field report", author="MOONWALK")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="SmallNote", parent=styles["BodyText"], fontSize=8, leading=11, textColor=GREY))
    styles.add(ParagraphStyle(name="MWTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=30,
                              leading=29, alignment=0, textColor=INK, spaceAfter=2))
    styles.add(ParagraphStyle(name="MWLabel", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=7.5,
                              leading=10, textColor=GREY))
    styles.add(ParagraphStyle(name="MWBody", parent=styles["BodyText"], fontSize=10, leading=13.5, textColor=INK))
    styles.add(ParagraphStyle(name="MWH", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=9,
                              textColor=INK, spaceBefore=6, spaceAfter=4))

    stamp = timestamp or datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    count_text = str(detected_count) if detected_count is not None else "Not recorded"
    if detected_count is not None and source_kind == "video":
        count_text += " (most in a single video frame)"
    if confidences:
        count_text += " - model confidence " + ", ".join(f"{c*100:.0f}%" for c in confidences[:5])
    rows = [
        ["REPORT GENERATED", stamp],
        ["COORDINATES", f"{latitude:.6f}, {longitude:.6f}" if latitude is not None and longitude is not None else "Not available"],
        ["GPS ACCURACY", f"+/-{accuracy:.0f} m" if accuracy is not None else "Not available"],
        ["LOCATION SOURCE", "Adjusted manually by user" if manual_location else "Browser device location"],
        ["ADDRESS / NEAREST MAPPED PLACE", address or "Could not be resolved"],
        ["LIKELY ROAD AUTHORITY", authority or "Not determined - please verify locally"],
        ["DETECTED POTHOLES", count_text],
        ["OFFICIAL AUTHORITY SITE", complaint_url or "No verified portal link available"],
        ["REPORTING APP LISTING", reporting_url or "No verified app listing available"],
    ]
    table = Table([[Paragraph(escape(a), styles["MWLabel"]), Paragraph(escape(str(b)), styles["MWBody"])] for a, b in rows],
                  colWidths=[48*mm, 116*mm])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEABOVE", (0, 0), (-1, 0), 1.2, INK),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, INK),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story = [Paragraph("FIELD REPORT /<br/>POTHOLE DAMAGE", styles["MWTitle"]), Spacer(1, 6*mm), table,
             Spacer(1, 6*mm), Paragraph("EVIDENCE - ANNOTATED DETECTION", styles["MWH"])]
    if image_bytes:
        try:
            image = ImageReader(BytesIO(image_bytes))
            iw, ih = image.getSize()
            max_w, max_h = 174*mm, 100*mm
            scale = min(max_w / iw, max_h / ih, 1)
            story.append(RLImage(BytesIO(image_bytes), width=iw*scale, height=ih*scale, hAlign="LEFT"))
        except Exception:
            story.append(Paragraph("The image could not be embedded in this report.", styles["MWBody"]))
    story += [Spacer(1, 5*mm), Paragraph(
        "Important: model results can contain false positives or miss potholes. Device GPS indicates the device location, "
        "not necessarily the exact pothole location. Confirm the map pin and road authority before submitting. "
        "This report was generated on your device; no complaint was automatically sent. You remain responsible for the final submission.",
        styles["SmallNote"])]
    chrome = _chrome(report_id)
    doc.build(story, onFirstPage=chrome, onLaterPages=chrome)
    return output.getvalue()
