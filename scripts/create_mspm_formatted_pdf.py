#!/usr/bin/env python3
"""
Create PDF resume that strictly follows the mspm_template.tex formatting.
Uses the exact styling and layout from the original template.
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
    from reportlab.platypus.flowables import HRFlowable
except ImportError:
    print("❌ reportlab not installed. Run: pip install reportlab")
    sys.exit(1)

def create_mspm_formatted_resume():
    """Create resume PDF following exact mspm_template.tex formatting"""
    
    # Output file
    output_file = Path("data/generated/tailored_resume_mspm_format.pdf")
    
    # Document setup with exact margins from LaTeX template
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
    
    # Create styles matching mspm_template.tex exactly
    header_style = ParagraphStyle(
        'MSPMHeader',
        parent=styles['Normal'],
        fontSize=16,
        spaceAfter=6,
        spaceBefore=0,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        leading=18
    )
    
    contact_style = ParagraphStyle(
        'MSPMContact',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=12,
        spaceBefore=0,
        alignment=TA_CENTER,
        fontName='Helvetica',
        leading=12
    )
    
    section_style = ParagraphStyle(
        'MSPMSection',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=2,
        spaceBefore=8,
        fontName='Helvetica-Bold',
        leading=10
    )
    
    # Ultra-compact body style
    body_style = ParagraphStyle(
        'MSPMBody',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=0,
        spaceBefore=0,
        fontName='Helvetica',
        leading=10.5
    )
    
    # Ultra-compact bullet style
    bullet_style = ParagraphStyle(
        'MSPMBullet',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=1,
        spaceBefore=0,
        leftIndent=12,
        fontName='Helvetica',
        leading=10.5
    )
    
    # Header Section - Following exact template format
    story.append(Paragraph("PRODUCT MANAGER - EDTECH SPECIALIST", header_style))
    story.append(Paragraph("555.123.4567 | pm.candidate@email.com | linkedin.com/in/pm-candidate | San Francisco, CA", contact_style))
    
    # Education Section (NO LINE above education per template)
    story.append(Paragraph("EDUCATION", section_style))
    
    # Education entries following exact template format
    edu_data = [
        ["STANFORD UNIVERSITY", "Stanford, CA"],
        ["Bachelor of Science in Computer Science -- GPA: 3.7/4.0", "06/20"]
    ]
    
    edu_table = Table(edu_data, colWidths=[5.5*inch, 1.5*inch])
    edu_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1), (0,1), 'Helvetica-Oblique'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0.5),
    ]))
    story.append(edu_table)
    
    # Education bullet points
    story.append(Paragraph("• Magna Cum Laude. Relevant Coursework: Human-Computer Interaction, Data Structures, Database Systems, Software Engineering.", bullet_style))
    story.append(Spacer(1, 4))
    
    # Work Experience Section with section line
    story.append(Paragraph("WORK EXPERIENCE", section_style))
    story.append(HRFlowable(width="100%", thickness=0.6, color=black, spaceAfter=2))
    
    # Current Job - Following exact template format with company descriptor
    current_job_data = [
        ["TECHVISION INC (Leading EdTech Platform)", "San Francisco, CA"],
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
        ('BOTTOMPADDING', (0,0), (-1,-1), 0.5),
    ]))
    story.append(current_job_table)
    
    # Current job achievements with categories (following template pattern)
    current_achievements = [
        "Product Leadership: Led cross-functional team to launch new assessment module, resulting in 40% increase in student engagement and 25% improvement in learning outcomes across K-12 platform serving 500K+ students.",
        "Process Optimization: Implemented agile development methodology across product team, reducing feature delivery time by 30% and improving code quality metrics by 50% through systematic workflow improvements.",
        "User Research & Strategy: Conducted comprehensive user research and usability testing with 500+ teachers, identifying key pain points that informed product roadmap priorities and enhanced user experience design.",
        "Cross-functional Collaboration: Collaborated with engineering and design teams to redesign core user interface, improving user satisfaction scores by 35% and reducing support tickets by 20%."
    ]
    
    for achievement in current_achievements:
        story.append(Paragraph(f"• {achievement}", bullet_style))
    
    story.append(Spacer(1, 2))
    
    # Previous Job
    previous_job_data = [
        ["INNOVATELABS (B2B SaaS Analytics Platform)", "Palo Alto, CA"],
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
        ('BOTTOMPADDING', (0,0), (-1,-1), 0.5),
    ]))
    story.append(previous_job_table)
    
    # Previous job achievements with categories
    previous_achievements = [
        "Revenue Growth: Developed and launched analytics dashboard feature used by 80% of customers, generating $2M additional ARR through improved data visualization and customer insights platform.",
        "Data-Driven Optimization: Led A/B testing program for key product features, improving conversion rates by 25% through systematic experimentation and statistical analysis of user behavior patterns."
    ]
    
    for achievement in previous_achievements:
        story.append(Paragraph(f"• {achievement}", bullet_style))
    
    # Programming/Technical Skills line (following template pattern)
    story.append(Spacer(1, 2))
    story.append(Paragraph("Technical Experience: Product Management, User Research, Data Analysis, SQL, Python; Tools: Jira, Confluence, Figma, Analytics platforms", body_style))
    
    story.append(Spacer(1, 4))
    
    # Project Experience Section with section line
    story.append(Paragraph("PROJECT EXPERIENCE", section_style))
    story.append(HRFlowable(width="100%", thickness=0.6, color=black, spaceAfter=2))
    
    # Project bullets (following template format)
    project_achievements = [
        "Learning Analytics Platform -- Developed comprehensive analytics platform for K-12 educational insights as Product Lead. Improved student outcome tracking by 60% and reduced teacher workload by 30%. Adopted by 500+ schools with 6-person development team using Python, SQL, React, and data visualization tools.",
        "EdTech Assessment Module -- Led product strategy for cross-functional launch of new assessment capabilities. Collaborated with UX design and engineering teams to deliver user-centered solution resulting in 40% engagement increase and 25% learning outcome improvement."
    ]
    
    for project in project_achievements:
        story.append(Paragraph(f"• {project}", bullet_style))
    
    story.append(Spacer(1, 4))
    
    # Additional Information Section with section line
    story.append(Paragraph("ADDITIONAL INFORMATION", section_style))
    story.append(HRFlowable(width="100%", thickness=0.6, color=black, spaceAfter=2))
    
    # Additional info bullets
    additional_info = [
        "Core Skills: Product Management, User Experience Design, Cross-functional Collaboration, Agile Methodologies, Scrum, Requirements Gathering, EdTech, K-12 Education, SaaS platforms.",
        "Technical Proficiencies: Advanced proficiency in data analysis, user research methodologies, A/B testing, SQL querying, and product analytics tools for data-driven decision making."
    ]
    
    for info in additional_info:
        story.append(Paragraph(f"• {info}", bullet_style))
    
    # Build the PDF
    try:
        doc.build(story)
        print(f"✅ MSPM-formatted PDF generated: {output_file}")
        return output_file
    except Exception as e:
        print(f"❌ PDF generation failed: {e}")
        return None

def main():
    """Main function"""
    print("🚀 Creating MSPM Template Formatted Resume PDF")
    print("=" * 60)
    
    # Ensure output directory exists
    output_dir = Path("data/generated")
    output_dir.mkdir(exist_ok=True)
    
    # Generate the PDF
    pdf_path = create_mspm_formatted_resume()
    
    if pdf_path:
        print(f"\n🎉 MSPM-formatted resume PDF created successfully!")
        print(f"📄 File: {pdf_path}")
        
        if Path(pdf_path).exists():
            size_kb = Path(pdf_path).stat().st_size / 1024
            print(f"📊 Size: {size_kb:.1f} KB")
            print(f"📂 Full path: {Path(pdf_path).absolute()}")
            
        print(f"\n📋 MSPM Template Features Applied:")
        print(f"✅ Ultra-compact, high-density formatting")
        print(f"✅ Section lines for Work Experience, Project Experience, Additional Info")
        print(f"✅ No line above Education section (per template)")
        print(f"✅ Company descriptors in parentheses")
        print(f"✅ Categorized bullet points (Product Leadership, Revenue Growth, etc.)")
        print(f"✅ Technical skills line following template pattern")
        print(f"✅ Right-aligned dates and locations")
        print(f"✅ Tight spacing and margins matching original")
        print(f"✅ Content optimized for EdTech Product Manager role")
        
    else:
        print(f"\n❌ Failed to create MSPM-formatted PDF")

if __name__ == "__main__":
    main()