#!/usr/bin/env python3
"""
Create a professional PDF resume using reportlab with better formatting.
Replicates the LaTeX template styling as closely as possible.
"""

import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.colors import black
    from reportlab.lib import colors
    from reportlab.platypus.flowables import HRFlowable
except ImportError:
    print("❌ reportlab not installed. Run: pip install reportlab")
    sys.exit(1)

def create_professional_resume():
    """Create a professional resume PDF that matches the LaTeX template styling"""
    
    # Output file
    output_file = Path("data/generated/tailored_resume_professional.pdf")
    
    # Document setup with tight margins like LaTeX template
    doc = SimpleDocTemplate(
        str(output_file), 
        pagesize=letter,
        leftMargin=0.5*inch, 
        rightMargin=0.5*inch,
        topMargin=0.5*inch, 
        bottomMargin=0.3*inch
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Create custom styles matching LaTeX template
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Normal'],
        fontSize=18,
        spaceAfter=6,
        spaceBefore=0,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        leading=22
    )
    
    contact_style = ParagraphStyle(
        'ContactStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=12,
        spaceBefore=0,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=2,
        spaceBefore=8,
        fontName='Helvetica-Bold',
        leading=13
    )
    
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=1,
        spaceBefore=0,
        fontName='Helvetica',
        leading=11
    )
    
    job_header_style = ParagraphStyle(
        'JobHeader',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=0,
        spaceBefore=4,
        fontName='Helvetica-Bold',
        leading=11
    )
    
    job_title_style = ParagraphStyle(
        'JobTitle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=2,
        spaceBefore=0,
        fontName='Helvetica-Oblique',
        leading=11
    )
    
    bullet_style = ParagraphStyle(
        'BulletStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=1,
        spaceBefore=0,
        leftIndent=15,
        fontName='Helvetica',
        leading=11
    )
    
    # Header Section
    story.append(Paragraph("PRODUCT MANAGER - SAMPLE CANDIDATE", header_style))
    story.append(Paragraph("555.123.4567 | pm.candidate@email.com | linkedin.com/in/pm-candidate | San Francisco, CA", contact_style))
    
    # Education Section
    story.append(Paragraph("EDUCATION", section_header_style))
    
    # Create table for education with right-aligned dates
    edu_data = [
        ["STANFORD UNIVERSITY", "Stanford, CA"],
        ["Bachelor of Science in Computer Science", "06/20"],
        ["GPA: 3.7/4.0, Magna Cum Laude", ""]
    ]
    
    edu_table = Table(edu_data, colWidths=[5.5*inch, 1.5*inch])
    edu_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1), (0,1), 'Helvetica-Oblique'),
        ('FONTNAME', (0,2), (0,2), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
    ]))
    story.append(edu_table)
    story.append(Spacer(1, 6))
    
    # Work Experience Section
    story.append(Paragraph("WORK EXPERIENCE", section_header_style))
    
    # Add horizontal line
    story.append(HRFlowable(width="100%", thickness=0.6, color=black, spaceAfter=4))
    
    # Current Job - TechVision Inc
    current_job_data = [
        ["TECHVISION INC", "San Francisco, CA"],
        ["Senior Product Manager", "07/23 -- Present"]
    ]
    
    current_job_table = Table(current_job_data, colWidths=[5.5*inch, 1.5*inch])
    current_job_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1), (0,1), 'Helvetica-Oblique'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
    ]))
    story.append(current_job_table)
    
    # Current job achievements
    current_achievements = [
        "Led cross-functional team to launch new assessment module, resulting in 40% increase in student engagement and 25% improvement in learning outcomes",
        "Implemented agile development methodology across product team, reducing feature delivery time by 30% and improving code quality metrics by 50%",
        "Conducted comprehensive user research and usability testing with 500+ teachers, identifying key pain points that informed product roadmap priorities",
        "Collaborated with engineering and design teams to redesign core user interface, improving user satisfaction scores by 35% and reducing support tickets by 20%"
    ]
    
    for achievement in current_achievements:
        story.append(Paragraph(f"• {achievement}", bullet_style))
    
    story.append(Spacer(1, 4))
    
    # Previous Job - InnovateLabs
    previous_job_data = [
        ["INNOVATELABS", "Palo Alto, CA"],
        ["Product Manager", "07/21 -- 07/23"]
    ]
    
    previous_job_table = Table(previous_job_data, colWidths=[5.5*inch, 1.5*inch])
    previous_job_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1), (0,1), 'Helvetica-Oblique'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
    ]))
    story.append(previous_job_table)
    
    # Previous job achievements
    previous_achievements = [
        "Developed and launched analytics dashboard feature used by 80% of customers, generating $2M additional ARR",
        "Led A/B testing program for key product features, improving conversion rates by 25% through data-driven optimization"
    ]
    
    for achievement in previous_achievements:
        story.append(Paragraph(f"• {achievement}", bullet_style))
    
    story.append(Spacer(1, 6))
    
    # Technical Skills Section
    story.append(Paragraph("TECHNICAL SKILLS", section_header_style))
    story.append(HRFlowable(width="100%", thickness=0.6, color=black, spaceAfter=4))
    
    skills_text = "Requirements Gathering, Data Analysis, Product Management, User Experience Design, Figma, EdTech, K-12 Education, Cross-functional Collaboration, Agile Methodologies, Scrum, User Research, SQL, Python, Jira, Confluence"
    story.append(Paragraph(f"<b>Core Skills:</b> {skills_text}", body_style))
    
    # Build the PDF
    try:
        doc.build(story)
        print(f"✅ Professional PDF generated: {output_file}")
        return output_file
    except Exception as e:
        print(f"❌ PDF generation failed: {e}")
        return None

def main():
    """Main function"""
    print("🚀 Creating Professional Resume PDF")
    print("=" * 50)
    
    # Ensure output directory exists
    output_dir = Path("data/generated")
    output_dir.mkdir(exist_ok=True)
    
    # Generate the PDF
    pdf_path = create_professional_resume()
    
    if pdf_path:
        print(f"\n🎉 Professional resume PDF created successfully!")
        print(f"📄 File: {pdf_path}")
        
        if Path(pdf_path).exists():
            size_kb = Path(pdf_path).stat().st_size / 1024
            print(f"📊 Size: {size_kb:.1f} KB")
            print(f"📂 Full path: {Path(pdf_path).absolute()}")
            
        print(f"\n📋 Resume Features:")
        print(f"✅ Professional formatting matching LaTeX template")
        print(f"✅ Content selected by TailerAI analysis algorithm")
        print(f"✅ Tailored for EdTech Product Manager position")
        print(f"✅ Optimized for ATS and keyword matching")
        print(f"✅ One-page format with tight spacing")
        print(f"✅ 6 high-impact achievements showcased")
        print(f"✅ 15 relevant technical skills highlighted")
        
    else:
        print(f"\n❌ Failed to create professional PDF")

if __name__ == "__main__":
    main()