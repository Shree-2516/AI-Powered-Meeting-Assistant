from fpdf import FPDF
from fpdf.enums import XPos, YPos
import io
from datetime import datetime

class PDFReport(FPDF):
    def header(self):
        # Helvetica bold 15
        self.set_font('helvetica', 'B', 15)
        # Title (centered)
        self.cell(0, 10, 'Meeting Intelligence Report', 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        # Line break
        self.ln(10)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Helvetica italic 8
        self.set_font('helvetica', 'I', 8)
        # Page number
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')

def clean_text(text):
    """Deep clean text for FPDF compatibility."""
    if not text:
        return ""
    if not isinstance(text, str):
        text = str(text)
        
    # Replace common unicode characters that Latin-1 doesn't like
    replacements = {
        '\u2013': '-', # en dash
        '\u2014': '-', # em dash
        '\u2018': "'", # left single quote
        '\u2019': "'", # right single quote
        '\u201c': '"', # left double quote
        '\u201d': '"', # right double quote
        '\u2022': '*', # bullet
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode('latin-1', 'ignore').decode('latin-1')

def generate_meeting_pdf(data: dict) -> bytes:
    try:
        pdf = PDFReport()
        pdf.alias_nb_pages()
        pdf.add_page()
        
        # Calculate safe width for content
        effective_width = pdf.w - 2 * pdf.l_margin
        
        # Meeting Info
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(effective_width, 10, clean_text(f"Meeting ID: {data.get('meetingId', 'N/A')}"), 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        date_str = data.get('createdAt', '').split('T')[0] if data.get('createdAt') else datetime.now().strftime('%Y-%m-%d')
        pdf.cell(effective_width, 10, clean_text(f"Date: {date_str}"), 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)

        # Sentiment
        sentiment = data.get('sentiment') or {}
        pdf.set_font('helvetica', 'B', 14)
        pdf.set_text_color(45, 106, 79)
        pdf.cell(effective_width, 10, "Sentiment Analysis", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('helvetica', '', 11)
        
        score_val = sentiment.get('score')
        if score_val is None:
            score_val = 0
        score_pct = int(score_val * 100)
        
        pdf.cell(effective_width, 8, clean_text(f"Overall Tone: {sentiment.get('label', 'NEUTRAL')} ({score_pct}%)"), 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.multi_cell(effective_width, 8, clean_text(f"Description: {sentiment.get('tone', '')}"))
        pdf.ln(5)

        # Summary
        pdf.set_font('helvetica', 'B', 14)
        pdf.set_text_color(45, 106, 79)
        pdf.cell(effective_width, 10, "Executive Summary", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('helvetica', '', 11)
        pdf.multi_cell(effective_width, 8, clean_text(data.get('summary', '')), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)

        # Key Points
        pdf.set_font('helvetica', 'B', 14)
        pdf.set_text_color(45, 106, 79)
        pdf.cell(effective_width, 10, "Key Takeaways", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('helvetica', '', 11)
        for point in data.get('keyPoints', []):
            pdf.multi_cell(effective_width, 8, clean_text(f"- {point}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)

        # Action Items
        pdf.set_font('helvetica', 'B', 14)
        pdf.set_text_color(45, 106, 79)
        pdf.cell(effective_width, 10, "Action Items", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('helvetica', '', 11)
        for item in data.get('actionItems', []):
            pdf.multi_cell(effective_width, 8, clean_text(f"- {item}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)

        # Topics
        pdf.set_font('helvetica', 'B', 14)
        pdf.set_text_color(45, 106, 79)
        pdf.cell(effective_width, 10, "Topics Covered", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('helvetica', '', 11)
        topics = data.get('topics', [])
        if topics:
            for i, topic in enumerate(topics, 1):
                pdf.multi_cell(effective_width, 8, clean_text(f"{i}. {topic}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            pdf.multi_cell(effective_width, 8, "None", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)

        # Full Transcription
        pdf.add_page()
        pdf.set_font('helvetica', 'B', 14)
        pdf.set_text_color(45, 106, 79)
        pdf.cell(effective_width, 10, "Full Transcription", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('helvetica', '', 10)
        pdf.multi_cell(effective_width, 6, clean_text(data.get('transcription', '')), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Return as bytes
        return bytes(pdf.output())
    except Exception as e:
        print(f"PDF Service Error: {e}")
        import traceback
        traceback.print_exc()
        raise e

