from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

class ReportGenerator:
    def generate_pdf(self, filename, content, target, profile, ports):
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph("Attachment Testimony Report", styles['Title']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(content.replace('\n', '<br />'), styles['Normal']))
        doc.build(story)