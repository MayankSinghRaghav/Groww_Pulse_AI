from fpdf import FPDF
import datetime

def diagnostic_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.text(10, 10, "DIAGNOSTIC TEST - KUVERA PULSE")
    pdf.set_text_color(255, 0, 0)
    pdf.rect(10, 20, 50, 50, 'F') # BIG RED BOX
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=12)
    pdf.set_xy(10, 80)
    pdf.multi_cell(0, 10, "If you see a red box above and this text, the PDF engine is working fine.")
    pdf.output("data/outputs/diagnostic.pdf")
    print("Diagnostic PDF generated at data/outputs/diagnostic.pdf")

if __name__ == "__main__":
    diagnostic_pdf()
