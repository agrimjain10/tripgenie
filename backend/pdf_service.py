from io import BytesIO
from html import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

INK = colors.HexColor("#203d37")
GREEN = colors.HexColor("#276653")
PALE = colors.HexColor("#eff3ed")
LINE = colors.HexColor("#e2e8e2")


def _paragraph(value) -> str:
    return escape(str(value or "")).replace("\n", "<br/>")


def _table(rows, widths, header=True):
    cell_style = ParagraphStyle(name="TableCell", fontName="Helvetica", fontSize=8.5, leading=12)
    wrapped = [[Paragraph(str(cell), cell_style) for cell in row] for row in rows]
    table = Table(wrapped, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]
    if header:
        commands.extend([("BACKGROUND", (0, 0), (-1, 0), PALE), ("TEXTCOLOR", (0, 0), (-1, 0), GREEN)])
    table.setStyle(TableStyle(commands))
    return table


def create_pdf(trip, plan: dict) -> bytes:
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=17*mm, bottomMargin=17*mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TripTitle", parent=styles["Title"], textColor=INK, alignment=0, fontSize=25, leading=30, spaceAfter=5))
    styles.add(ParagraphStyle(name="Section", parent=styles["Heading2"], textColor=GREEN, fontSize=13, leading=17, spaceBefore=11, spaceAfter=7))
    styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8.5, leading=12, textColor=colors.HexColor("#64736b")))
    styles.add(ParagraphStyle(name="Cell", parent=styles["BodyText"], fontSize=8.5, leading=12))

    party = f"{trip.travelers or 1} traveler(s)"
    route = f"{_paragraph(trip.origin)} to " if trip.origin else ""
    date_line = f"{route}{_paragraph(trip.destination)}  |  {_paragraph(trip.start_date)} to {_paragraph(trip.end_date)}  |  {party}"
    if trip.budget is not None:
        date_line += f"  |  Budget INR {trip.budget:,.0f}"
    story = [Paragraph("TripGenie", styles["Small"]), Paragraph(_paragraph(trip.destination), styles["TripTitle"]), Paragraph(date_line, styles["Small"]), Spacer(1, 7*mm), Paragraph("The trip at a glance", styles["Section"]), Paragraph(_paragraph(plan.get("summary")), styles["BodyText"]) ]

    if plan.get('route_summary'):
        story.extend([Paragraph('Route and travel-day accounting', styles['Section']), Paragraph(_paragraph(plan['route_summary']), styles['BodyText']), Paragraph(_paragraph(plan.get('timing_notes')), styles['Small'])])
    for leg in plan.get('journey', []):
        story.extend([Paragraph(_paragraph(leg.get('title')), styles['Section']), Paragraph(_paragraph(leg.get('route')), styles['BodyText']), Paragraph(_paragraph(leg.get('departure_window')) + '<br/>' + _paragraph(leg.get('duration')), styles['Small']), Paragraph(f"Group estimate: INR {float(leg.get('estimated_cost', 0)):,.0f}", styles['BodyText']), Paragraph(_paragraph(leg.get('booking_tip')), styles['Small'])])

    stays = plan.get("stay_recommendations", [])
    if stays:
        story.append(Paragraph("Places to stay", styles["Section"]))
        rows = [["Area", "Stay type and notes", "Est. per night"]]
        for stay in stays:
            rows.append([_paragraph(stay.get("area")), _paragraph(stay.get("stay_type")) + "<br/>" + _paragraph(stay.get("description")), f"INR {float(stay.get('estimated_cost_per_night', 0) or 0):,.0f}"])
        story.append(_table(rows, [37*mm, 103*mm, 30*mm]))

    transport = plan.get("transport_options", [])
    if transport:
        story.append(Paragraph("Getting there and around", styles["Section"]))
        rows = [["Option", "Details", "Estimated total"]]
        for option in transport:
            rows.append([_paragraph(option.get("mode")), _paragraph(option.get("description")), f"INR {float(option.get('estimated_cost', 0) or 0):,.0f}"])
        story.append(_table(rows, [34*mm, 106*mm, 30*mm]))

    story.append(Paragraph("Day by day", styles["Section"]))
    for day in plan.get("days", []):
        story.append(Paragraph(f"Day {day.get('day', '')}: {_paragraph(day.get('title'))}", styles["Heading3"]))
        rows = [["Time", "Activity", "Cost"]]
        for item in day.get("activities", []):
            details = '<b>' + _paragraph(item.get('activity')) + '</b>'
            for field in ('description', 'travel_tip', 'location'):
                if item.get(field):
                    details += '<br/>' + _paragraph(item[field])
            rows.append([_paragraph(item.get("time")), details, f"INR {float(item.get('cost', 0) or 0):,.0f}"])
        story.append(_table(rows, [25*mm, 115*mm, 30*mm]))
        story.append(Paragraph(f"Estimated day spend: INR {float(day.get('day_cost', 0) or 0):,.0f}", styles["Small"]))
        if day.get('notes'):
            story.append(Paragraph(_paragraph(day['notes']), styles['Small']))
        if day.get('overnight'):
            story.append(Paragraph('Tonight: ' + _paragraph(day['overnight']), styles['BodyText']))
        story.append(Spacer(1, 3*mm))

    breakdown = plan.get("budget_breakdown", {})
    if plan.get('budget_line_items'):
        story.append(Paragraph('Itemized group budget', styles['Section']))
        rows = [['Item and assumptions', 'Quantity x rate', 'Total INR']]
        for item in plan['budget_line_items']:
            rows.append(['<b>' + _paragraph(item.get('item')) + '</b><br/>' + _paragraph(item.get('notes')), f"{item.get('quantity', 1)} x INR {float(item.get('unit_cost', 0)):,.0f}", f"INR {float(item.get('total', 0)):,.0f}"])
        story.append(_table(rows, [105*mm, 35*mm, 30*mm]))
    if breakdown:
        story.append(Paragraph("Budget outline", styles["Section"]))
        rows = [["Category", "Estimated INR"]]
        rows.extend([[escape(str(name).title()), f"INR {float(value or 0):,.0f}"] for name, value in breakdown.items()])
        story.append(_table(rows, [100*mm, 70*mm]))

    if plan.get("tips"):
        story.append(Paragraph("Useful notes", styles["Section"]))
        story.extend(Paragraph("- " + _paragraph(tip), styles["BodyText"]) for tip in plan["tips"])
    for field, heading in [('packing_list', 'Packing list'), ('booking_checklist', 'Before you book'), ('alternatives', 'If plans change')]:
        if plan.get(field):
            story.append(Paragraph(heading, styles['Section']))
            story.extend(Paragraph('- ' + _paragraph(item), styles['BodyText']) for item in plan[field])
    if plan.get("booking_guidance"):
        story.extend([Spacer(1, 4*mm), Paragraph(_paragraph(plan["booking_guidance"]), styles["Small"])])
    story.extend([Spacer(1, 5*mm), Paragraph("Prices and suggestions are estimates. Confirm current details directly with travel providers.", styles["Small"])])
    doc.build(story)
    return output.getvalue()
