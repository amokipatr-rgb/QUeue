#!/usr/bin/env python3
"""Generate SMQSS Quotation PDF using fpdf2."""

from fpdf import FPDF
from datetime import datetime, timedelta


class QuotationPDF(FPDF):
    GREEN_DARK = (26, 60, 44)
    GREEN_MID = (42, 90, 58)
    GREEN_LIGHT = (232, 245, 233)
    GOLD = (255, 215, 0)
    WHITE = (255, 255, 255)
    BLACK = (33, 33, 33)
    GRAY = (117, 117, 117)
    LIGHT_GRAY = (245, 245, 245)
    CHECK_GREEN = (46, 125, 50)

    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*self.GRAY)
        self.cell(0, 10, "SMQSS | ogwalrichard.kesug.com", align="L")
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="R")

    def bullet(self, x, y, text, w=None):
        self.set_xy(x, y)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*self.GREEN_DARK)
        self.cell(4, 5, ">")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*self.BLACK)
        if w:
            self.cell(w - 4, 5, f" {text}")
        else:
            self.cell(0, 5, f" {text}")

    def line_height(self):
        return 4


def _heading(pdf, text):
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*pdf.GREEN_DARK)
    pdf.set_x(10)
    pdf.cell(0, 7, text)
    pdf.ln(7)
    y = pdf.get_y()
    pdf.set_draw_color(*pdf.GOLD)
    pdf.set_line_width(0.5)
    pdf.line(10, y, pdf.w - 10, y)
    pdf.ln(3)


def build_pdf(output_path="SMQSS_Quotation.pdf"):
    pdf = QuotationPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    W = pdf.w - 20
    today = datetime.now()
    valid_until = today + timedelta(days=30)

    # ── HEADER ──
    pdf.set_fill_color(*pdf.GREEN_DARK)
    pdf.rect(0, 0, 210, 40, "F")
    pdf.set_fill_color(*pdf.GOLD)
    pdf.rect(0, 40, 210, 2, "F")

    pdf.set_xy(10, 8)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*pdf.WHITE)
    pdf.cell(0, 10, "SMQSS")
    pdf.ln(10)

    pdf.set_xy(10, 18)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*pdf.GOLD)
    pdf.cell(0, 6, "Smart Queue Management System")
    pdf.ln(6)

    pdf.set_xy(W - 50, 10)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*pdf.WHITE)
    pdf.cell(50, 10, "QUOTATION", align="R")

    pdf.set_xy(W - 70, 20)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*pdf.GOLD)
    pdf.cell(70, 6, f"Ref: SMQSS-Q-001  |  Date: {today.strftime('%d %B %Y')}", align="R")

    pdf.set_y(48)

    # ── FROM / TO ──
    half_w = W / 2 - 3
    y_top = pdf.get_y()

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*pdf.GREEN_DARK)
    pdf.set_x(10)
    pdf.cell(half_w, 6, "FROM:")

    pdf.set_xy(10 + half_w + 6, y_top)
    pdf.cell(half_w, 6, "TO (Institution):")
    pdf.ln(6)

    pdf.set_font("Helvetica", "", 9)
    from_lines = [
        "Ogwal Richard",
        "SMQSS (Smart Queue Management System)",
        "Makerere University, Kampala",
        "Uganda",
        "ogwalrichard.kesug.com",
    ]
    to_fields = [
        "Institution Name: _______________________",
        "Department: _____________________________",
        "Contact Person: _________________________",
        "Phone/Email: ____________________________",
        "Address: ________________________________",
    ]

    y_after = pdf.get_y()
    pdf.set_x(10)
    for line in from_lines:
        pdf.set_x(10)
        pdf.cell(half_w, 5, line)
        pdf.ln(5)

    y_from_end = pdf.get_y()
    pdf.set_xy(10 + half_w + 6, y_after)
    for field in to_fields:
        pdf.set_x(10 + half_w + 6)
        pdf.cell(half_w, 5, field)
        pdf.ln(5)

    pdf.set_y(max(y_from_end, pdf.get_y()) + 4)

    # ── VALIDITY ──
    pdf.set_fill_color(*pdf.LIGHT_GRAY)
    pdf.set_x(10)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*pdf.GRAY)
    pdf.cell(W, 6,
             f"  This quotation is valid until {valid_until.strftime('%d %B %Y')} (30 days from issue date).",
             fill=True)
    pdf.ln(8)

    # ── ABOUT SMQSS ──
    _heading(pdf, "About SMQSS")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*pdf.BLACK)
    pdf.set_x(10)
    pdf.multi_cell(W, 5,
        "SMQSS is a smart queue management system built for institutions that serve "
        "students and the public. It replaces manual queuing with a digital system "
        "that keeps service flowing smoothly, reduces wait times, and gives management "
        "clear visibility into daily operations. The system is easy to use, works on "
        "standard computers and printers, and is accessible from any web browser.")
    pdf.ln(2)

    # ── TRUSTED BY ──
    _heading(pdf, "Trusted By")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*pdf.BLACK)
    pdf.set_x(10)
    pdf.cell(0, 5, "SMQSS is currently deployed and in active use at:")
    pdf.ln(5)

    for item in ["Makerere University", "Ministry of Internal Affairs",
                  "Various startup businesses across Uganda"]:
        pdf.set_x(16)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*pdf.GREEN_DARK)
        pdf.cell(5, 5, ">")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*pdf.BLACK)
        pdf.cell(0, 5, f" {item}")
        pdf.ln(5)

    pdf.set_x(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*pdf.GRAY)
    pdf.cell(0, 5, "Copyrighted and patented with the Uganda Registration Services Bureau (URSB).")
    pdf.ln(7)

    # ── KEY BENEFITS COMPARISON ──
    _heading(pdf, "Key Benefits Comparison")

    benefits = [
        ("Streamlined student queue flow - no more crowding", True, True),
        ("Faster service delivery with automated token routing", True, True),
        ("Real-time visibility into queue status across all offices", True, True),
        ("Digital receipts and printed queue tickets", True, True),
        ("Student satisfaction feedback on every service", True, True),
        ("Basic daily and weekly service reports", True, True),
        ("Data-driven decision making with comprehensive analytics", False, True),
        ("Intelligent insights and recommendations for management", False, True),
        ("Staff performance evaluation and accountability", False, True),
        ("Staff attendance monitoring and reporting", False, True),
        ("Exportable reports for record-keeping and audits", False, True),
        ("Peak demand forecasting for better resource planning", False, True),
        ("Deep understanding of student satisfaction trends", False, True),
        ("End-to-end service lifecycle tracking and optimization", False, True),
    ]

    col0 = W * 0.52
    col1 = W * 0.24
    col2 = W * 0.24

    # Header row
    pdf.set_fill_color(*pdf.GREEN_DARK)
    pdf.set_text_color(*pdf.WHITE)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_x(10)
    pdf.cell(col0, 7, "  Key Benefit", fill=True, border=1)
    pdf.cell(col1, 7, "Standard $25/mo", fill=True, border=1, align="C")
    pdf.cell(col2, 7, "Premium $50/mo", fill=True, border=1, align="C")
    pdf.ln()

    for i, (benefit, std, prem) in enumerate(benefits):
        bg = pdf.WHITE if i % 2 == 0 else pdf.LIGHT_GRAY
        pdf.set_fill_color(*bg)
        pdf.set_text_color(*pdf.BLACK)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_x(10)
        pdf.cell(col0, 6, f"  {benefit}", fill=True, border=1)

        x_pos = 10 + col0

        # Standard
        if std:
            pdf.set_text_color(*pdf.CHECK_GREEN)
            pdf.set_font("Helvetica", "B", 9)
            mark = "YES"
        else:
            pdf.set_text_color(*pdf.GRAY)
            pdf.set_font("Helvetica", "", 9)
            mark = "--"
        pdf.set_xy(x_pos, pdf.get_y())
        pdf.cell(col1, 6, mark, fill=True, border=1, align="C")

        # Premium
        if prem:
            pdf.set_text_color(*pdf.CHECK_GREEN)
            pdf.set_font("Helvetica", "B", 9)
            mark = "YES"
        else:
            pdf.set_text_color(*pdf.GRAY)
            pdf.set_font("Helvetica", "", 9)
            mark = "--"
        pdf.set_xy(x_pos + col1, pdf.get_y())
        pdf.cell(col2, 6, mark, fill=True, border=1, align="C")

        pdf.ln()

    pdf.ln(6)

    # ── PRICING ──
    _heading(pdf, "Pricing")

    pdf.set_fill_color(*pdf.GREEN_DARK)
    pdf.set_text_color(*pdf.WHITE)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_x(10)
    pdf.cell(W * 0.08, 7, " #", fill=True, border=1)
    pdf.cell(W * 0.47, 7, " Tier", fill=True, border=1)
    pdf.cell(W * 0.22, 7, "Monthly (USD)", fill=True, border=1, align="C")
    pdf.cell(W * 0.23, 7, "Annual (USD)", fill=True, border=1, align="C")
    pdf.ln()

    rows = [
        ("1", "Standard - Queue mgmt, officer desks, basic reports", "$25.00", "$300.00"),
        ("2", "Premium - Full system + analytics, insights, export", "$50.00", "$600.00"),
    ]

    pdf.set_font("Helvetica", "", 9)
    for i, (num, tier, monthly, annual) in enumerate(rows):
        bg = pdf.WHITE if i == 0 else pdf.LIGHT_GRAY
        pdf.set_fill_color(*bg)
        pdf.set_text_color(*pdf.BLACK)
        pdf.set_x(10)
        pdf.cell(W * 0.08, 7, f" {num}", fill=True, border=1)
        pdf.cell(W * 0.47, 7, f" {tier}", fill=True, border=1)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(W * 0.22, 7, monthly, fill=True, border=1, align="C")
        pdf.cell(W * 0.23, 7, annual, fill=True, border=1, align="C")
        pdf.set_font("Helvetica", "", 9)
        pdf.ln()

    pdf.ln(6)

    # ── WHAT'S INCLUDED ──
    _heading(pdf, "What's Included (All Tiers)")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*pdf.BLACK)

    for item in [
        "Cloud-hosted platform - accessible from any device with a web browser",
        "Automated queue management and token routing",
        "Student self-service options (kiosk and mobile)",
        "Email notifications and voice announcements",
        "Ongoing software updates and technical support",
    ]:
        pdf.set_x(16)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*pdf.GREEN_DARK)
        pdf.cell(5, 5, ">")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*pdf.BLACK)
        pdf.cell(0, 5, f" {item}")
        pdf.ln(5)

    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*pdf.GRAY)
    pdf.set_x(16)
    pdf.multi_cell(W - 6, 5,
        "Note: Institution provides and owns all computers, printers, kiosks, and "
        "other hardware devices. Hardware is not included in the subscription.")
    pdf.ln(4)

    # ── TERMS & CONDITIONS ──
    _heading(pdf, "Terms & Conditions")

    terms = [
        ("1.", "Payment:", "Monthly or annual subscription, payable in advance."),
        ("2.", "Renewal:", "Subscription auto-renews unless cancelled in writing 30 days before the renewal date."),
        ("3.", "Ownership:",
         "This subscription does not grant ownership of the SMQSS software or system. "
         "Subscribers are entitled to use the system solely for the services it provides "
         "to their business operations. No rights, title, or interest in the software, "
         "source code, or intellectual property are transferred to the subscriber."),
        ("4.", "Device Ownership:",
         "Only business entities in formal partnership with SMQSS have the right to "
         "permanently own the devices on which the software runs. All other subscribers "
         "use the software on devices that remain the property of the subscriber and "
         "are not covered under this subscription."),
        ("5.", "License:", "Single-institution, non-transferable, revocable upon non-payment."),
        ("6.", "Hosting:", "Infrastructure maintained by SMQSS on cloud servers; subscriber accesses via web browser."),
        ("7.", "Support:", "Email and remote technical support included in the subscription."),
        ("8.", "Termination:", "SMQSS reserves the right to terminate access upon 30 days' notice for breach of terms."),
    ]

    for num, title, desc in terms:
        pdf.set_x(10)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*pdf.BLACK)
        pdf.cell(6, 4, num)
        pdf.cell(0, 4, title)
        pdf.ln(4)
        pdf.set_x(16)
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(W - 6, 4, desc)
        pdf.ln(1)

    pdf.ln(4)

    # ── ACCEPTANCE ──
    _heading(pdf, "Acceptance")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*pdf.BLACK)

    pdf.set_x(10)
    pdf.cell(0, 6, "Selected Tier (tick one):")
    pdf.ln(7)

    pdf.set_x(10)
    pdf.cell(6, 6, "[ ]")
    pdf.cell(55, 6, "  Standard ($25/mo)")
    pdf.cell(10, 6, "")
    pdf.cell(6, 6, "[ ]")
    pdf.cell(55, 6, "  Premium ($50/mo)")
    pdf.ln(8)

    pdf.set_font("Helvetica", "", 9)
    for field in [
        "Institution Name: _________________________________________________",
        "",
        "Authorized Signature: __________________________  Date: _______________",
        "",
        "Name (Print): ___________________________________",
        "",
        "Official Stamp / Seal:",
    ]:
        pdf.set_x(10)
        pdf.cell(0, 6, field)
        pdf.ln(6)

    pdf.rect(pdf.get_x() + 10, pdf.get_y(), 40, 25)
    pdf.set_y(pdf.get_y() + 30)

    pdf.output(output_path)


if __name__ == "__main__":
    build_pdf("SMQSS_Quotation.pdf")
    print("Generated: SMQSS_Quotation.pdf")
