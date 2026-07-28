"""
Convert Markdown Status Report to PDF using ReportLab
"""
import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Preformatted
from reportlab.lib import colors

def clean_text(text):
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    text = re.sub(r'`(.*?)`', r'<font face="Courier">\1</font>', text)
    return text

def parse_markdown_to_pdf(md_path, pdf_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1E88E5'),
        spaceAfter=10
    )

    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1565C0'),
        spaceBefore=12,
        spaceAfter=6
    )

    h3_style = ParagraphStyle(
        'DocH3',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#37474F'),
        spaceBefore=8,
        spaceAfter=4
    )

    h4_style = ParagraphStyle(
        'DocH4',
        parent=styles['Heading4'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#455A64'),
        spaceBefore=6,
        spaceAfter=2
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#212121'),
        spaceAfter=4
    )

    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=3
    )

    code_style = ParagraphStyle(
        'DocCode',
        fontName='Courier',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#1B5E20'),
        backColor=colors.HexColor('#F5F5F5'),
        borderPadding=6,
        spaceAfter=6
    )

    story = []
    in_code_block = False
    code_lines = []

    for line in lines:
        raw_line = line.rstrip()

        if raw_line.startswith("```"):
            if in_code_block:
                code_text = "\n".join(code_lines)
                story.append(Preformatted(code_text, code_style))
                code_lines = []
                in_code_block = False
            else:
                in_code_block = True
            continue

        if in_code_block:
            code_lines.append(raw_line)
            continue

        if not raw_line.strip():
            story.append(Spacer(1, 4))
            continue

        if raw_line.startswith("---"):
            story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor('#CFD8DC'), spaceBefore=8, spaceAfter=8))
            continue

        c_text = clean_text(raw_line)

        if raw_line.startswith("# "):
            story.append(Paragraph(c_text[2:], title_style))
        elif raw_line.startswith("## "):
            story.append(Paragraph(c_text[3:], h2_style))
        elif raw_line.startswith("### "):
            story.append(Paragraph(c_text[4:], h3_style))
        elif raw_line.startswith("#### "):
            story.append(Paragraph(c_text[5:], h4_style))
        elif raw_line.startswith("- ") or raw_line.startswith("* "):
            story.append(Paragraph("&bull; " + c_text[2:], bullet_style))
        elif re.match(r'^\d+\.\s', raw_line):
            story.append(Paragraph(c_text, bullet_style))
        else:
            story.append(Paragraph(c_text, body_style))

    doc.build(story)
    print(f"PDF Status Report successfully generated at: {pdf_path}")

if __name__ == "__main__":
    md_file = "/Users/rakeshpathlavath/Desktop/health_insurance/project_status_report.md"
    pdf_file = "/Users/rakeshpathlavath/Desktop/health_insurance/project_status_report.pdf"
    parse_markdown_to_pdf(md_file, pdf_file)
