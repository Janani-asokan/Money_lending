from pathlib import Path
from datetime import date

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


OUT = Path(__file__).with_name("Sri_Sakthi_Thirumurugan_Finance_Client_Handover.docx")

BLUE = "D86F45"
NAVY = "123F35"
INK = "173D35"
MUTED = "596B66"
PALE = "E8E2D8"
PALE_BLUE = "EFE9DF"
GREEN = "2F705D"
PALE_GREEN = "E3EEE8"
AMBER = "A45D35"
PALE_AMBER = "F5E7D8"
RED = "B42318"
PALE_RED = "F4DEDA"
WHITE = "F8F4EC"
LINE = "C9C0B3"
PAGE_IVORY = "F7F3EB"
SANS = "Aptos"
DISPLAY = "Aptos Display"
SERIF = "Georgia"


def rgb(value):
    return RGBColor.from_string(value)


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=80, start=120, bottom=80, end=120):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_table_geometry(table, widths_in):
    table.autofit = False
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    total_dxa = sum(round(width * 1440) for width in widths_in)
    tbl_pr = table._tbl.tblPr
    tbl_w = tbl_pr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:w"), str(total_dxa))
    tbl_w.set(qn("w:type"), "dxa")
    tbl_ind = tbl_pr.find(qn("w:tblInd"))
    if tbl_ind is None:
        tbl_ind = OxmlElement("w:tblInd")
        tbl_pr.append(tbl_ind)
    tbl_ind.set(qn("w:w"), "120")
    tbl_ind.set(qn("w:type"), "dxa")
    grid = table._tbl.tblGrid
    for child in list(grid):
        grid.remove(child)
    for width in widths_in:
        col = OxmlElement("w:gridCol")
        col.set(qn("w:w"), str(round(width * 1440)))
        grid.append(col)
    for row in table.rows:
        for idx, cell in enumerate(row.cells):
            width_dxa = round(widths_in[idx] * 1440)
            cell.width = Inches(widths_in[idx])
            tc_pr = cell._tc.get_or_add_tcPr()
            tc_w = tc_pr.find(qn("w:tcW"))
            if tc_w is None:
                tc_w = OxmlElement("w:tcW")
                tc_pr.append(tc_w)
            tc_w.set(qn("w:w"), str(width_dxa))
            tc_w.set(qn("w:type"), "dxa")
            set_cell_margins(cell)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def set_repeat_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def keep_with_next(paragraph, value=True):
    paragraph.paragraph_format.keep_with_next = value


def set_repeat_table_rows(table):
    if table.rows:
        set_repeat_header(table.rows[0])


def add_page_field(paragraph):
    run = paragraph.add_run()
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "end")
    run._r.extend([fld_char1, instr, fld_char2])


def style_run(run, size=None, bold=None, color=None, italic=None, font=SANS):
    run.font.name = font
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), font)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), font)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color:
        run.font.color.rgb = rgb(color)


def add_para(doc, text="", *, bold=False, italic=False, size=11, color=INK,
             align=WD_ALIGN_PARAGRAPH.LEFT, before=0, after=6, keep=False):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.25
    p.paragraph_format.keep_with_next = keep
    r = p.add_run(text)
    style_run(r, size=size, bold=bold, italic=italic, color=color)
    return p


def add_bullet(doc, text, level=0):
    p = doc.add_paragraph(style="List Bullet" if level == 0 else "List Bullet 2")
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.25
    r = p.add_run(text)
    style_run(r, size=11, color=INK)
    return p


def add_number(doc, text):
    p = doc.add_paragraph(style="List Number")
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.25
    r = p.add_run(text)
    style_run(r, size=11, color=INK)
    return p


def add_heading(doc, text, level=1):
    p = doc.add_paragraph(text, style=f"Heading {level}")
    keep_with_next(p)
    return p


def add_callout(doc, label, text, tone="blue"):
    tones = {
        "blue": (PALE_BLUE, NAVY),
        "green": (PALE_GREEN, GREEN),
        "amber": (PALE_AMBER, AMBER),
        "red": (PALE_RED, RED),
    }
    fill, color = tones[tone]
    table = doc.add_table(rows=1, cols=1)
    set_table_geometry(table, [6.5])
    cell = table.cell(0, 0)
    set_cell_shading(cell, fill)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.2
    r = p.add_run(f"{label}: ")
    style_run(r, size=10.5, bold=True, color=color)
    r = p.add_run(text)
    style_run(r, size=10.5, color=INK)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def add_table(doc, headers, rows, widths, header_fill=PALE):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    hdr = table.rows[0]
    for idx, value in enumerate(headers):
        cell = hdr.cells[idx]
        set_cell_shading(cell, header_fill)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(str(value))
        style_run(r, size=9.5, bold=True, color=NAVY)
    for row_data in rows:
        row = table.add_row()
        for idx, value in enumerate(row_data):
            p = row.cells[idx].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.15
            r = p.add_run(str(value))
            style_run(r, size=9.3, color=INK)
    set_table_geometry(table, widths)
    set_repeat_table_rows(table)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


def add_section_intro(doc, title, text):
    add_heading(doc, title, 1)
    add_para(doc, text, size=11.3, color=MUTED, after=9)


def configure_document():
    doc = Document()
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.82)
    section.bottom_margin = Inches(0.78)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    section.header_distance = Inches(0.34)
    section.footer_distance = Inches(0.35)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Calibri"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
    normal.font.size = Pt(11)
    normal.font.color.rgb = rgb(INK)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.25
    for level, size, color, before, after in [
        (1, 16, BLUE, 18, 10), (2, 13, BLUE, 14, 7), (3, 12, NAVY, 10, 5)
    ]:
        style = styles[f"Heading {level}"]
        style.font.name = "Calibri"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = rgb(color)
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True

    for style_name in ["List Bullet", "List Bullet 2", "List Number"]:
        style = styles[style_name]
        style.font.name = "Calibri"
        style.font.size = Pt(11)
        style.paragraph_format.space_after = Pt(4)
        style.paragraph_format.line_spacing = 1.25

    header = section.header
    hp = header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = hp.add_run("SRI SAKTHI THIRUMURUGAN FINANCE  |  CLIENT DELIVERY PACK")
    style_run(r, size=8.5, bold=True, color=MUTED)
    p_pr = hp._p.get_or_add_pPr()
    p_bdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "3")
    bottom.set(qn("w:color"), LINE)
    p_bdr.append(bottom)
    p_pr.append(p_bdr)

    footer = section.footer
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = fp.add_run("Confidential client handover  |  Version 1.0  |  Page ")
    style_run(r, size=8.5, color=MUTED)
    add_page_field(fp)
    return doc


doc = configure_document()

# Cover: editorial-cover pattern.
add_para(doc, "CLIENT DELIVERY & OPERATIONS HANDBOOK", bold=True, size=10, color=BLUE,
         align=WD_ALIGN_PARAGRAPH.CENTER, before=82, after=20)
add_para(doc, "Money Lending Management System", bold=True, size=30, color=NAVY,
         align=WD_ALIGN_PARAGRAPH.CENTER, after=8)
add_para(doc, "Sri Sakthi Thirumurugan Finance", bold=True, size=17, color=BLUE,
         align=WD_ALIGN_PARAGRAPH.CENTER, after=14)
add_para(doc, "End-to-end feature guide, implementation record, production handover and operating procedures",
         size=12.5, color=MUTED, align=WD_ALIGN_PARAGRAPH.CENTER, after=54)
add_callout(doc, "Delivery position", "A practical, mobile-friendly lending operations platform for customer onboarding, loan tracking, Cash/UPI collections, area-wise field work, receipts, reporting, accounting controls and audit evidence.", "blue")
add_para(doc, "Prepared for: Business Owner / Client", bold=True, size=10.5, color=INK,
         align=WD_ALIGN_PARAGRAPH.CENTER, before=34, after=4)
add_para(doc, "Prepared on: 28 August 2026  |  Engagement value: ₹60,000", size=10.5, color=MUTED,
         align=WD_ALIGN_PARAGRAPH.CENTER, after=4)
add_para(doc, "Live application: https://money-lending-app.onrender.com", size=9.5, color=BLUE,
         align=WD_ALIGN_PARAGRAPH.CENTER, after=28)
add_para(doc, "CONFIDENTIAL - FOR CLIENT HANDOVER AND OPERATIONAL USE", bold=True, size=8.5, color=MUTED,
         align=WD_ALIGN_PARAGRAPH.CENTER)
doc.add_page_break()

add_section_intro(doc, "Document purpose", "This document explains what the system does, why each capability matters to the lending business, how the owner should operate it, what engineering changes were completed, and which external services remain the client's responsibility before wider production use.")
add_table(doc, ["Document item", "Details"], [
    ("Product", "Sri Sakthi Thirumurugan Finance Money Lending Management System"),
    ("Delivery type", "Responsive web application with React frontend, FastAPI backend and MongoDB Atlas persistence"),
    ("Primary operator", "Business owner; named manager, collector and accountant roles are supported"),
    ("Current hosting", "Render-hosted frontend and API; MongoDB Atlas database"),
    ("Source control", "GitHub repository with traceable implementation commits"),
    ("Document version", "1.0 - client handover, 28 August 2026"),
], [1.875, 4.625])
add_callout(doc, "Important", "This handbook does not claim that a third-party Aadhaar service, SMS gateway, paid high-availability hosting or off-site backup service is active unless the relevant client-owned account and credentials have been configured.", "amber")

add_heading(doc, "How to use this handbook", 2)
for item in [
    "Read Sections 1-3 for the business case and system overview.",
    "Use Sections 4-13 as the day-to-day operating guide.",
    "Use Sections 14-17 for security, deployment, maintenance and production readiness.",
    "Use Sections 18-20 for delivery evidence, client acceptance and future roadmap decisions.",
]:
    add_bullet(doc, item)

add_heading(doc, "Contents", 1)
contents = [
    "1. Executive summary", "2. Business problems addressed", "3. Solution and architecture",
    "4. Signing in and workspace security", "5. Dashboard and area collection planning",
    "6. Customer registration and verification", "7. Customer 360 and safe profile deletion",
    "8. Loan creation and repayment plans", "9. Cash and UPI collection workflow",
    "10. EMI planning and interest treatment", "11. Search, reminders and notifications",
    "12. Reports and printable records", "13. Accounting, ledger and controlled corrections",
    "14. Security, privacy and auditability", "15. Data durability, backup and recovery",
    "16. Responsive design and accessibility", "17. Production deployment and operations",
    "18. Implementation record and engineering care", "19. Client operating checklist",
    "20. Known boundaries and recommended next phase", "Appendix A. Terminology",
]
for item in contents:
    add_bullet(doc, item)
doc.add_page_break()

add_section_intro(doc, "1. Executive summary", "The delivered application replaces informal notebooks and disconnected spreadsheets with one controlled workspace for customers, loans, collections and evidence. It is designed for the owner's real working day: know whom to visit, how much is due, what was collected, how it was paid, what remains, and which records prove the transaction.")
add_para(doc, "The system now supports the complete operational chain from customer registration through verification, loan creation, schedule generation, payment collection, receipt creation, area review, customer history, reporting, accounting entries and audit review. It also includes production hardening work for persistent MongoDB storage, secure sessions, transactional writes, unique identifiers, responsive layouts and service health diagnostics.")
add_callout(doc, "Client value", "The engagement delivers more than screens. It establishes a traceable operational system in which money movement, customer identity, repayment status and staff actions are connected and reviewable.", "green")

add_heading(doc, "Delivered capability at a glance", 2)
add_table(doc, ["Business capability", "What the client can do", "Business outcome"], [
    ("Customer control", "Register, search, verify, review and safely remove eligible profiles", "Cleaner records and fewer duplicates"),
    ("Loan management", "Create daily, weekly or monthly plans at the approved 2.14% annual rate", "Consistent schedules and clear balances"),
    ("Field collections", "Record Cash or UPI payments with receipt and server timestamp", "Proof of collection and immediate balance update"),
    ("Area planning", "Open only areas with dues and drill into customer-level collection needs", "Faster daily route preparation"),
    ("Financial controls", "Post balanced ledger entries and use controlled reversals", "Improved reconciliation and accountability"),
    ("Audit and security", "Review immutable activity evidence with role-based access", "Reduced dispute and misuse risk"),
], [1.35, 2.75, 2.4])

add_section_intro(doc, "2. Business problems addressed", "The implementation focused on the frustrations that would affect a real owner first: unavailable login, lost data, unclear dues, incorrect schedules, hidden actions, unreliable mobile layouts and financial changes without evidence.")
for title, text in [
    ("Data continuity", "Production no longer depends on an in-memory database. Customer, loan and payment records are stored in MongoDB Atlas and survive application restarts."),
    ("Operational visibility", "The dashboard identifies outstanding exposure, pending dues and the specific areas and customers requiring collection."),
    ("Payment proof", "Every recorded Cash or UPI collection receives a server timestamp, receipt number, payment mode, allocation and audit event."),
    ("Identity evidence", "The design supports time-stamped OTP evidence before disbursal. It does not represent an ordinary SMS as UIDAI Aadhaar verification."),
    ("Concurrent safety", "Atomic counters and uniqueness controls protect customer IDs, loan IDs, receipts, journals and verification references."),
    ("Financial integrity", "Loan, schedule, ledger and audit records are written within transaction boundaries so partial posting is avoided."),
]:
    add_heading(doc, title, 2)
    add_para(doc, text)

add_section_intro(doc, "3. Solution and architecture", "The application is separated into a responsive browser interface, a secured API and a persistent database. This separation makes the system maintainable and allows each layer to be monitored and upgraded independently.")
add_table(doc, ["Layer", "Technology", "Responsibility"], [
    ("User interface", "React + Vite", "Desktop, tablet and mobile workflows; validation; reports; receipts"),
    ("Application API", "FastAPI / Python", "Authentication, business rules, schedules, transactions, audit and reporting"),
    ("Database", "MongoDB Atlas", "Persistent customers, loans, payments, ledgers, sessions and audit records"),
    ("Hosting", "Render", "Managed deployment of frontend and API with build and health behaviour"),
    ("Source control", "GitHub", "Version history, reproducible deployment and rollback reference"),
], [1.25, 1.45, 3.8])
add_callout(doc, "Architecture principle", "The browser never decides the financial truth. Interest, schedules, balances, payment allocation, timestamps and permissions are enforced by the backend.", "blue")

add_heading(doc, "Primary user roles", 2)
add_table(doc, ["Role", "Typical responsibility", "Sensitive capabilities"], [
    ("Owner", "Overall business operation and oversight", "User management, deletion of eligible profiles, audit and configuration"),
    ("Manager", "Customer approval and operational supervision", "Verification decisions, loan and collection oversight"),
    ("Collector", "Field collection for assigned loans", "Record authorized payments and issue receipts"),
    ("Accountant", "Reports, ledger and reconciliation review", "Accounting visibility without unnecessary identity access"),
], [1.15, 2.55, 2.8])
doc.add_page_break()

add_section_intro(doc, "4. Signing in and workspace security", "The login flow creates a secure server-managed session. Users do not need to handle tokens, and sensitive session credentials are not exposed to normal browser scripts.")
add_heading(doc, "How to sign in", 2)
for step in [
    "Open the live application URL in a supported browser.",
    "Enter the username and current password supplied by the owner.",
    "Select Enter secure workspace.",
    "After access is granted, confirm the user name and role in the top-right identity chip.",
]:
    add_number(doc, step)
add_heading(doc, "Security behaviour", 2)
for item in [
    "Short-lived authenticated sessions use Secure, HTTP-only, SameSite cookies.",
    "A separate CSRF token protects authenticated write operations.",
    "Strong password changes require uppercase, lowercase, number and symbol characters.",
    "Other sessions are revoked when the owner changes the password.",
    "Production startup rejects weak demo secrets and unsafe memory fallback settings.",
]:
    add_bullet(doc, item)
add_callout(doc, "Owner action", "Use a unique password that is not reused for email, MongoDB, GitHub or Render. Never share production credentials in chat or screenshots.", "red")

add_section_intro(doc, "5. Dashboard and area collection planning", "The dashboard is the owner's daily control centre. It summarizes the portfolio and then narrows attention to the areas and customers where money is actually due.")
add_heading(doc, "What the dashboard shows", 2)
for item in [
    "Today's collection, active loans, overdue loans, pending verification and total outstanding.",
    "Pending dues ordered by the nearest due date, with daily, weekly, monthly and overdue filters.",
    "A compact collection trend; when no payments exist, the interface shows a clear empty state instead of a large blank chart.",
    "Only areas requiring collection. Empty configured areas are intentionally hidden from the collection worklist.",
    "For every collectible area: customers with dues, paid today, yet to pay and total outstanding.",
]:
    add_bullet(doc, item)
add_heading(doc, "How to prepare an area visit", 2)
for step in [
    "Open Dashboard and scroll to Areas requiring collection.",
    "Select the relevant area to expand its active customer list.",
    "Review each customer's plan, installment, total paid, outstanding amount, remaining installments and next due date.",
    "Select the customer name to open Customer 360 for complete history before visiting or calling.",
    "After collecting, use Collections to post the payment and return to the dashboard to confirm the updated position.",
]:
    add_number(doc, step)

add_section_intro(doc, "6. Customer registration and verification", "Customer records are created once and reused for future daily, weekly and monthly loans. Duplicate suggestions reduce accidental repeat profiles.")
add_heading(doc, "Manual registration", 2)
for step in [
    "Open Customers and choose Manual registration.",
    "Enter name, father's name, 10-digit Indian mobile number, area, address and guarantor details where applicable.",
    "Review any existing-customer suggestion before creating a new profile.",
    "Create the profile. It remains Pending Verification until an owner or manager decides its status.",
]:
    add_number(doc, step)
add_heading(doc, "Aadhaar-assisted registration", 2)
for step in [
    "Choose Aadhaar registration and capture the 12-digit Aadhaar number only with informed customer consent.",
    "Record the disclosed purpose and consent reference.",
    "When an authorized provider is configured, send the OTP to the Aadhaar-linked mobile.",
    "Enter exactly the 4- or 6-digit OTP. Non-numeric or longer input is blocked.",
    "Incorrect OTPs reduce the remaining attempts; the request locks after three incorrect attempts and OTPs expire automatically.",
]:
    add_number(doc, step)
add_callout(doc, "Compliance boundary", "Direct Aadhaar OTP/eKYC requires a UIDAI-authorized AUA/KUA or approved provider. Until the client supplies such credentials, the application must not claim that Aadhaar was verified automatically.", "amber")

add_heading(doc, "Customer status workflow", 2)
add_table(doc, ["Status", "Meaning", "Operator action"], [
    ("Pending Verification", "Details exist but approval is not complete", "Review identity and supporting evidence"),
    ("Manual Verification Approved", "Owner/manager accepted the manual verification basis", "Customer may proceed according to business policy"),
    ("Verification Failed", "Evidence was inadequate or inconsistent", "Correct details or perform a fresh verification"),
    ("Verified", "Authorized electronic verification succeeded", "Retain the verification reference and timestamp"),
], [1.65, 2.35, 2.5])

add_section_intro(doc, "7. Customer 360 and safe profile deletion", "Customer 360 joins the customer's identity, all loan plans, repayment history, balances and verification events in one place.")
add_heading(doc, "Customer 360 contains", 2)
for item in [
    "Customer identity, area, mobile number, current verification status and risk indicator.",
    "Every daily, weekly and monthly loan linked to the same customer profile.",
    "Total borrowed, total repaid and total outstanding across those plans.",
    "A reverse-chronological timeline covering customer creation, verification, loans, payments and OTP evidence.",
]:
    add_bullet(doc, item)
add_heading(doc, "Deleting an eligible customer profile", 2)
add_para(doc, "Deletion is intentionally controlled. A customer with an active or unpaid loan cannot be deleted. A customer with no loan, or whose loans are fully completed/closed, can be removed from the active registry by the owner.")
for step in [
    "Open Customers or Customer 360 and select Delete customer.",
    "Read the consequence statement.",
    "Type the exact customer ID shown in the dialog.",
    "Enter a deletion reason of at least five characters.",
    "Tick the final acknowledgement and select Confirm profile deletion.",
]:
    add_number(doc, step)
add_callout(doc, "Financial record protection", "Deletion removes or redacts personal profile details from the active list. Loan, payment, receipt, journal and audit evidence is retained so financial history is not silently erased.", "red")

add_section_intro(doc, "8. Loan creation and repayment plans", "A verified customer can hold multiple simultaneous plans. The owner may create a daily plan, a weekly plan and a monthly plan under the same customer without duplicating the profile.")
add_heading(doc, "Supported plan types", 2)
add_table(doc, ["Plan", "Typical period", "Tracking provided"], [
    ("Daily 100-Day", "100 daily installments", "Daily installment, paid count, remaining count and next due"),
    ("Weekly", "Configured number of weekly installments", "Weekly amount, schedule, paid and remaining"),
    ("Monthly EMI", "Configured number of monthly installments", "Monthly EMI, maturity, paid and remaining"),
], [1.45, 2.05, 3.0])
add_heading(doc, "How to create a loan", 2)
for step in [
    "Open Loans and select the customer.",
    "Enter the principal amount and choose Daily, Weekly or Monthly.",
    "Confirm the period, interest method, first due date and any permitted fee, tax, moratorium, late charge or pre-closure setting.",
    "Select the collector and disbursement account (Cash, UPI or Bank Transfer).",
    "Enter the borrower KFS acknowledgement reference.",
    "Optionally preview APR, KFS and schedule. Preview is not required to press Create loan directly.",
    "Create the loan. The backend generates the loan ID, schedule, ledger entry and audit event together.",
]:
    add_number(doc, step)
add_callout(doc, "Approved pricing", "New loans are enforced at the configured annual interest rate of 2.14%. The server rejects a different rate, preventing accidental operator changes.", "green")
add_heading(doc, "Calculation coverage", 2)
add_para(doc, "The current engine supports reducing or flat interest, fee and tax inputs, moratorium periods, late charges, pre-closure settings, part-payment recalculation, restructuring, write-off handling and versioned amortization schedules. Loan displays use the stored contract interest and total repayment rather than a simplified principal-only estimate.")

add_section_intro(doc, "9. Cash and UPI collection workflow", "Collections is designed for field use. The owner or collector can see who has paid today, who has not paid, how much is due and how the customer paid.")
add_heading(doc, "What each collection item shows", 2)
for item in [
    "Customer name and customer ID.", "Loan ID and daily/weekly/monthly frequency.",
    "Paid today or Not paid today status.", "Current installment and remaining balance.",
    "Total paid, remaining installments and the most recent payment method/date.",
]:
    add_bullet(doc, item)
add_heading(doc, "Record a Cash collection", 2)
for step in [
    "Open Collections and search by customer name, customer ID or loan ID.",
    "Select the correct customer plan and confirm the outstanding balance.",
    "Enter the amount received and choose Cash.",
    "Select Save payment and print receipt.",
    "Give or share the generated receipt and confirm the customer now shows Paid today.",
]:
    add_number(doc, step)
add_heading(doc, "Record a UPI collection", 2)
for step in [
    "Follow the same customer and loan selection steps.",
    "Choose UPI and enter the mandatory UPI transaction/reference ID.",
    "Save the payment. The reference is retained for settlement and reconciliation.",
    "Confirm the receipt shows the payment mode, amount, timestamp and remaining balance.",
]:
    add_number(doc, step)
add_callout(doc, "Posting safety", "A payment cannot be zero, negative or greater than the total outstanding. Repeated submissions use an idempotency reference so the same payment is not posted twice.", "blue")
doc.add_page_break()

add_section_intro(doc, "10. EMI planning and interest treatment", "The EMI Planner helps the owner estimate a plan before creating the official loan. The official server-generated schedule remains the source of truth.")
for item in [
    "Annual interest is fixed at 2.14% for new loans.",
    "Reducing-balance and flat-interest approaches are distinguished.",
    "The schedule includes installment dates, principal, interest, payment and closing balance.",
    "APR reflects applicable fee and tax inputs rather than displaying only the headline rate.",
    "Part-payment, pre-closure and restructuring actions generate controlled schedule versions.",
]:
    add_bullet(doc, item)
add_callout(doc, "Good practice", "Give the borrower the Key Fact Statement and schedule before disbursal, retain the acknowledgement reference, and never rely only on an on-screen estimate for a contractual decision.", "amber")

add_section_intro(doc, "11. Search, reminders and notifications", "The application reduces time spent hunting through records by allowing the owner to search across the identifiers used in daily work.")
add_heading(doc, "Search coverage", 2)
for item in [
    "Customer name, customer ID and mobile number.", "Loan ID and receipt-related records.",
    "Area code/name and masked Aadhaar suffix where permitted.", "Global keyboard command access through Ctrl+K on desktop.",
]:
    add_bullet(doc, item)
add_heading(doc, "Operational alerts", 2)
add_para(doc, "Pending dues and overdue alerts are presented as operational work, not decorative notifications. The dashboard prioritizes nearest due dates and identifies the balance, plan and customer involved.")

add_section_intro(doc, "12. Reports and printable records", "Reports convert live operational data into files and views suitable for owner review, follow-up and accountant support.")
add_heading(doc, "Available report families", 2)
for item in [
    "Customer ledger", "Daily collection", "Monthly cash flow", "Annual report",
    "Loan summary", "Defaulters", "Area performance", "Collector performance",
    "Profit report", "Recovery rate", "Business growth",
]:
    add_bullet(doc, item)
add_heading(doc, "How to generate a report", 2)
for step in [
    "Open Reports and select the required report type.",
    "Choose the customer or period when the report requires it.",
    "Select Generate report and review the preview.",
    "Download CSV, Excel or PDF, print it, or use the available sharing action.",
    "If generation fails, the system shows an error and does not present an incomplete file as successful.",
]:
    add_number(doc, step)

add_section_intro(doc, "13. Accounting, ledger and controlled corrections", "The accounting module is intended to connect operational collections with cash, UPI and bank positions. It uses balanced journal entries rather than treating payments as isolated values.")
add_heading(doc, "Covered accounting events", 2)
for item in [
    "Verified opening balances for Cash, UPI or Bank.", "Loan disbursement accounting.",
    "Payment allocation to penalty, interest and principal.", "Expenses and collector deposits.",
    "UPI settlement to bank.", "Daily cash closing.", "Controlled reversal requests and approvals.",
]:
    add_bullet(doc, item)
add_heading(doc, "Why some actions may be blocked", 2)
add_table(doc, ["Message", "Meaning", "Required action"], [
    ("Opening balance required", "The source account has not been established", "Post and lock a verified opening amount"),
    ("No active collector", "Collector deposit has no valid staff owner", "Create/activate a collector account"),
    ("No unsettled UPI", "There is no recorded UPI balance to transfer", "Record UPI collections first"),
    ("Approval required", "A correction needs maker-checker review", "Use a different authorized approver"),
], [1.55, 2.15, 2.8])
add_callout(doc, "Accounting discipline", "A blocked button is not necessarily a defect. In financial workflows it often prevents spending, settlement or correction before the required source balance or approval exists.", "blue")

add_section_intro(doc, "14. Security, privacy and auditability", "Security work was applied to the complete data path: login, browser session, API authorization, database storage, sensitive identity fields and audit evidence.")
add_heading(doc, "Implemented protections", 2)
for item in [
    "Secure HTTP-only session cookies and CSRF protection for write operations.",
    "Role-based endpoint authorization for owner, manager, collector and accountant.",
    "Aadhaar encrypted at rest using authenticated encryption, masked in normal views and hashed for duplicate detection.",
    "Purpose-bound Aadhaar access controls and time-limited one-time viewing patterns.",
    "Password hash and session-secret fields removed from normal API responses.",
    "Append-oriented audit history with hash-chain support and actor, object, timestamp and reason evidence.",
    "Security headers, trusted-origin checks and production fail-closed configuration validation.",
]:
    add_bullet(doc, item)
add_heading(doc, "Controlled financial corrections", 2)
add_para(doc, "Payments and journals are not silently edited or hard-deleted. Corrections are represented through reversal requests that retain the original transaction reference, reason, maker, checker/manager approval and before/after audit evidence.")

add_section_intro(doc, "15. Data durability, backup and recovery", "MongoDB Atlas provides persistent storage, replication and majority/journaled writes. This prevents the restart-related data loss associated with an in-memory demonstration database.")
add_heading(doc, "What is implemented", 2)
for item in [
    "Authenticated MongoDB connection using a production database name.",
    "Retryable writes, majority acknowledgement and journaling in the production connection string.",
    "Atomic counters/unique indexes for operational identifiers.",
    "MongoDB transaction boundaries for connected financial writes.",
    "Backup scripts, verification scripts and a documented restore-drill process in the repository.",
]:
    add_bullet(doc, item)
add_heading(doc, "What the client must still arrange", 2)
for item in [
    "An automated encrypted backup destination separate from the live database.",
    "A retention policy appropriate to business, legal and privacy requirements.",
    "Backup-failure alerts owned by the client.",
    "Regular restore testing into an isolated database with reconciliation evidence.",
]:
    add_bullet(doc, item)
add_callout(doc, "M0 limitation", "MongoDB Atlas M0 is suitable for a low-traffic single-owner launch and persistent reference data, but it is not a substitute for paid backup, point-in-time recovery, guaranteed capacity or enterprise availability.", "amber")

add_section_intro(doc, "16. Responsive design and accessibility", "The interface was corrected for laptop, tablet and mobile use so field operation does not depend on a desktop-sized screen.")
add_table(doc, ["Device", "Navigation behavior", "Operational result"], [
    ("Laptop/Desktop", "Fixed left sidebar with independent scrolling", "Stable navigation during long pages"),
    ("Tablet", "Compact sticky top navigation", "More width for forms and tables"),
    ("Mobile", "Fixed bottom navigation with horizontal access", "One-handed field access without a blank sidebar overlay"),
], [1.4, 2.45, 2.65])
for item in [
    "Touch controls use mobile-safe sizes and native 16px form text to prevent browser zoom.",
    "Wide tables use contained scrolling instead of pushing the entire page beyond the viewport.",
    "Loading, empty, error, disabled and success states are presented explicitly.",
    "Financial meaning is expressed with labels and values, not colour alone.",
]:
    add_bullet(doc, item)

add_section_intro(doc, "17. Production deployment and operations", "The current deployment uses Render for the web application/API and MongoDB Atlas for persistence. GitHub is the source of truth for automated deployments.")
add_heading(doc, "Routine deployment flow", 2)
for step in [
    "Changes are implemented and locally built/tested.",
    "A descriptive Git commit records the change.",
    "The main branch is pushed to GitHub.",
    "Render detects the commit and builds the affected service.",
    "The deployment is checked through Render status and the live application.",
]:
    add_number(doc, step)
add_heading(doc, "Availability considerations", 2)
add_para(doc, "The Render free plan can sleep after inactivity, causing a delayed first request. For an always-on production commitment, the client should use an always-on paid service or another managed host with health checks, restart policy, monitoring and alerting. The application includes friendly service-unavailable handling, but no application code can keep a free sleeping host or failed internet connection online.")
add_heading(doc, "Daily operational checks", 2)
for item in [
    "Confirm login and dashboard load.", "Review pending verification and overdue dues.",
    "Record all Cash/UPI collections and verify receipts.", "Reconcile Cash and UPI totals before day close.",
    "Review errors, health status and backup age.",
]:
    add_bullet(doc, item)
doc.add_page_break()

add_section_intro(doc, "18. Implementation record and engineering care", "The application was improved through repeated production-focused cycles between 20 and 28 August 2026. Each cycle addressed a real failure mode, then used builds, backend validation, deployment status and live browser checks before handover.")
add_heading(doc, "Delivery timeline", 2)
add_table(doc, ["Date", "Workstream", "Delivered outcome"], [
    ("20 Aug", "Foundation", "Initial production-oriented lending application and core modules"),
    ("25 Aug", "Persistence and deployment", "MongoDB Atlas support, managed hosting, owner login, responsive fixes and health release visibility"),
    ("27 Aug", "Loan and security hardening", "Production loan flow, CSRF/session protections, financial tracking, OTP evidence, area drill-down and index migration safety"),
    ("28 Aug", "Operational usability", "Customer statuses/deletion, focused area worklist, Customer 360 navigation, responsive sidebar and Cash/UPI payment status"),
], [0.8, 1.75, 3.95])

add_heading(doc, "Where engineering care was concentrated", 2)
add_table(doc, ["Workstream", "Relative effort", "Why this required care", "Evidence of completion"], [
    ("Persistent database and migrations", "Very high", "A wrong migration can stop startup or damage live access", "Safe index migration, Atlas deployment and successful restart"),
    ("Loan schedules and accounting", "Very high", "Interest, allocation and balances must remain financially consistent", "Server calculations, transactions, ledger posting and build tests"),
    ("Authentication and sessions", "High", "Login reliability must be balanced with cookie/CSRF security", "Secure session flow and production login verification"),
    ("Customer/OTP controls", "High", "Identity mistakes create fraud and dispute risk", "Exact OTP length, attempts, lockout, consent and evidence timeline"),
    ("Collections and receipts", "High", "Duplicate or unsupported payments directly affect money records", "Idempotency, bounds checks, Cash/UPI modes and references"),
    ("Responsive UX", "High", "The owner works in the field across different screen sizes", "Laptop/tablet/mobile navigation and live visual checks"),
    ("Reporting and audit", "Medium-high", "Owner and accountant need traceable, exportable evidence", "Report corrections, audit trails and controlled reversal design"),
], [1.25, 0.8, 2.7, 1.75])
add_callout(doc, "Effort statement", "Exact hourly effort was not reconstructed or invented for this document. The table communicates relative engineering complexity and the validation applied. The Git history provides objective change evidence.", "blue")

add_heading(doc, "Representative implementation milestones", 2)
milestones = [
    "395707f - Support MongoDB Atlas and managed hosting",
    "4acac68 - Fix production owner login and responsive layout",
    "99a377c - Allow secure cross-origin Render sessions",
    "7e85354 - Harden production and expand loan tracking",
    "1578971 - Fix production customer index startup",
    "4b8f4a7 - Improve loan entry, OTP safety and area collections",
    "6fefe98 - Fix customer actions and focus area collections",
    "9796217 - Simplify customer profile and expose safe deletion",
    "f2fa17e - Fix sidebar across device sizes",
    "13f2059 - Add customer payment tracking for Cash and UPI",
]
for item in milestones:
    add_bullet(doc, item)

add_heading(doc, "Why the ₹60,000 engagement is commercially defensible", 2)
add_para(doc, "The value is not based on the number of pages or forms. The delivery combines domain modelling, secure identity handling, financial calculations, transactional persistence, role permissions, responsive field workflows, production deployment and iterative failure correction. These are the areas that determine whether a lending application can be trusted in daily operation.")
for item in [
    "One connected source of truth replaces fragmented manual tracking.",
    "Persistent cloud data reduces restart-related loss risk.",
    "Customer, loan, payment and area views shorten daily collection planning.",
    "Receipt, timestamp and audit evidence reduce dispute ambiguity.",
    "Backend-enforced rules reduce accidental interest, payment and deletion errors.",
    "Deployment automation and source control make future maintenance practical.",
]:
    add_bullet(doc, item)

add_section_intro(doc, "19. Client operating and acceptance checklist", "The following checklist should be completed jointly before the system is treated as the client's formal live record.")
add_table(doc, ["Acceptance check", "Owner verification", "Status"], [
    ("Owner can sign in and change password", "Login, logout and re-login tested", "□"),
    ("Customer registration and duplicate suggestion", "New and existing customer paths tested", "□"),
    ("Pending / Approve / Fail status workflow", "Each transition tested with audit event", "□"),
    ("Daily, weekly and monthly loan creation", "Schedule and KFS checked against agreed example", "□"),
    ("Cash payment", "Receipt and balance update reconciled", "□"),
    ("UPI payment", "Reference, receipt and UPI balance reconciled", "□"),
    ("Area worklist", "Only collectible areas and correct customers displayed", "□"),
    ("Customer 360", "Loans, payments, outstanding and timeline correct", "□"),
    ("Safe deletion", "No-loan/completed profile test; active loan blocked", "□"),
    ("Reports", "Required formats open and totals reconcile", "□"),
    ("Accounting", "Opening balances and day-close procedure agreed", "□"),
    ("Restart persistence", "Backend restart retains test customer/payment", "□"),
    ("Backup restore", "Newest backup restored in isolation and reconciled", "□"),
    ("Mobile/tablet/laptop", "Primary flows tested on actual client devices", "□"),
], [3.25, 2.55, 0.7])

add_heading(doc, "Recommended owner routine", 2)
add_table(doc, ["Frequency", "Owner action"], [
    ("Every collection", "Confirm customer/loan, enter amount and Cash/UPI mode, retain receipt/reference"),
    ("Daily", "Review areas, reconcile Cash/UPI, close the business day and resolve exceptions"),
    ("Weekly", "Review overdue accounts, collector performance, audit events and account balances"),
    ("Monthly", "Export reports, reconcile bank/UPI, review access, verify backup and capacity"),
    ("Quarterly", "Run an isolated restore drill and review security/retention policy"),
], [1.15, 5.35])

add_section_intro(doc, "20. Known boundaries and recommended next phase", "The present system is suitable for a controlled single-owner launch with low traffic, provided the owner accepts the limits of free infrastructure and follows backup and reconciliation procedures.")
add_table(doc, ["Area", "Current position", "Recommended next step"], [
    ("Aadhaar OTP", "Workflow implemented; provider not configured", "Client contracts with an authorized provider and supplies live credentials"),
    ("SMS OTP", "Provider integration requires client account", "Complete MSG91/DLT onboarding and production templates"),
    ("Database backup", "Persistent Atlas M0 data; no paid PITR", "Add encrypted off-site scheduled backup and restore monitoring"),
    ("Hosting uptime", "Render free plan can sleep", "Upgrade to always-on hosting before uptime commitments"),
    ("Maker-checker", "Supported by role design", "Create separate named manager/checker account"),
    ("Legal/compliance", "Controls are implemented in software", "Qualified adviser confirms RBI/UIDAI, consent and retention obligations"),
    ("Monitoring", "Health endpoint available", "Configure external uptime/error/backup alerts owned by client"),
], [1.25, 2.35, 2.9])
add_callout(doc, "Recommended release position", "Use the system with one owner and controlled real records only after the acceptance checklist, credential rotation and a restore drill are complete. Expand to staff and borrowers after external OTP/Aadhaar, monitoring and backup services are contracted.", "green")

add_heading(doc, "Support handover information", 2)
for item in [
    "Application: https://money-lending-app.onrender.com",
    "Source repository: https://github.com/Janani-asokan/Money_lending",
    "Deployment guidance: docs/PRODUCTION_DEPLOYMENT.md",
    "Backup scripts: scripts/run_backup.py, scripts/verify_backup.py and scripts/test_restore.py",
    "Production health endpoint: backend /api/health",
]:
    add_bullet(doc, item)

doc.add_page_break()
add_section_intro(doc, "Appendix A. Terminology", "The following terms are used consistently throughout the application and this handbook.")
add_table(doc, ["Term", "Meaning"], [
    ("Customer", "The borrower profile. One customer may hold several loan plans."),
    ("Loan plan", "A daily, weekly or monthly repayment agreement linked to a customer."),
    ("Principal", "The base amount lent before interest, fees and taxes."),
    ("Installment", "The scheduled amount due for one repayment period."),
    ("Outstanding", "The unpaid contract balance remaining on a loan."),
    ("KFS", "Key Fact Statement describing loan cost and terms."),
    ("APR", "Annual Percentage Rate representing broader annualized loan cost."),
    ("Receipt", "The unique evidence generated after a payment is posted."),
    ("Journal", "A balanced accounting entry with debit and credit lines."),
    ("Reversal", "A controlled correction that references an original transaction."),
    ("Maker-checker", "One person requests a sensitive action and another approves it."),
    ("Customer 360", "The joined customer view containing loans, payments, totals and timeline."),
    ("Idempotency", "Protection that prevents one repeated submission from posting twice."),
], [1.55, 4.95])

add_heading(doc, "Appendix B. Handover sign-off", 1)
add_para(doc, "By signing below, the parties confirm that the delivered features were demonstrated, known boundaries were explained, and the client received the operating and production-readiness guidance in this document.")
add_table(doc, ["Sign-off", "Name / signature / date"], [
    ("Client / Business Owner", "\n"),
    ("Developer / Delivery Partner", "\n"),
], [2.15, 4.35])
add_callout(doc, "Final note", "This system should be operated as a controlled financial record. Accurate data entry, daily reconciliation, secure credentials, monitored backups and documented corrections are shared operational responsibilities after handover.", "blue")

doc.core_properties.title = "Money Lending Management System - Client Delivery and Operations Handbook"
doc.core_properties.subject = "Feature guide, implementation record, production handover and client acceptance"
doc.core_properties.author = "Project Delivery Team"
doc.core_properties.keywords = "money lending, customer management, loans, collections, UPI, accounting, audit, production"
doc.core_properties.comments = "Prepared for client handover. Contains no production credentials."

OUT.parent.mkdir(parents=True, exist_ok=True)
doc.save(OUT)
print(OUT)
