#!/usr/bin/env python3
"""
Compile the generated LaTeX resume to PDF using the project's LaTeX service.
"""

import sys
import asyncio
import subprocess
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.latex_generation_service import latex_generation_service

def find_tectonic():
    """Find tectonic binary in PATH"""
    try:
        result = subprocess.run(['which', 'tectonic'], capture_output=True, text=True)
        if result.returncode == 0:
            tectonic_path = result.stdout.strip()
            print(f"✅ Found tectonic at: {tectonic_path}")
            return tectonic_path
    except Exception as e:
        print(f"Error finding tectonic: {e}")
        return None
    
    # Try to find it using which
    try:
        result = subprocess.run(['which', 'pdflatex'], capture_output=True, text=True)
        if result.returncode == 0:
            path = result.stdout.strip()
            print(f"✅ Found pdflatex via which: {path}")
            return path
    except:
        pass
    
    print("❌ pdflatex not found in common locations")
    return None

def try_alternative_compilation():
    """Try alternative PDF generation approaches"""
    print("🔄 Trying alternative PDF generation...")
    
    # Try using online services or python libraries
    try:
        import subprocess
        import tempfile
        from pathlib import Path
        
        # Read the LaTeX content
        tex_file = Path("data/generated/sample_tailored_resume.tex")
        if not tex_file.exists():
            print(f"❌ LaTeX file not found: {tex_file}")
            return None
        
        latex_content = tex_file.read_text()
        
        # Try using tectonic (if available)
        try:
            result = subprocess.run(['which', 'tectonic'], capture_output=True, text=True)
            if result.returncode == 0:
                print("📄 Found tectonic, trying compilation...")
                result = subprocess.run([
                    'tectonic', str(tex_file)
                ], capture_output=True, text=True, cwd=tex_file.parent)
                
                if result.returncode == 0:
                    pdf_file = tex_file.with_suffix('.pdf')
                    if pdf_file.exists():
                        print(f"✅ PDF generated with tectonic: {pdf_file}")
                        return pdf_file
                else:
                    print(f"❌ Tectonic compilation failed: {result.stderr}")
        except:
            pass
        
        # Try xelatex if available
        try:
            result = subprocess.run(['which', 'xelatex'], capture_output=True, text=True)
            if result.returncode == 0:
                print("📄 Found xelatex, trying compilation...")
                result = subprocess.run([
                    'xelatex', '-interaction=nonstopmode', str(tex_file)
                ], capture_output=True, text=True, cwd=tex_file.parent)
                
                if result.returncode == 0:
                    pdf_file = tex_file.with_suffix('.pdf')
                    if pdf_file.exists():
                        print(f"✅ PDF generated with xelatex: {pdf_file}")
                        return pdf_file
                else:
                    print(f"❌ XeLaTeX compilation failed: {result.stderr}")
        except:
            pass
        
    except Exception as e:
        print(f"❌ Alternative compilation failed: {e}")
    
    return None

def create_pdf_with_reportlab():
    """Create PDF using Python reportlab as fallback"""
    print("🐍 Trying PDF generation with Python reportlab...")
    
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        
        # Output file
        output_file = Path("data/generated/sample_tailored_resume_reportlab.pdf")
        doc = SimpleDocTemplate(str(output_file), pagesize=letter,
                              leftMargin=0.5*inch, rightMargin=0.5*inch,
                              topMargin=0.5*inch, bottomMargin=0.3*inch)
        
        story = []
        styles = getSampleStyleSheet()
        
        # Create custom styles
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        section_style = ParagraphStyle(
            'CustomSection',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=6,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=3,
            fontName='Helvetica'
        )
        
        bullet_style = ParagraphStyle(
            'CustomBullet',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=2,
            leftIndent=20,
            fontName='Helvetica'
        )
        
        # Header
        story.append(Paragraph("<b>PRODUCT MANAGER - SAMPLE CANDIDATE</b>", header_style))
        story.append(Paragraph("555.123.4567 | pm.candidate@email.com | linkedin.com/in/pm-candidate | San Francisco, CA", body_style))
        story.append(Spacer(1, 12))
        
        # Education
        story.append(Paragraph("<b>EDUCATION</b>", section_style))
        story.append(Paragraph("<b>STANFORD UNIVERSITY</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Stanford, CA", body_style))
        story.append(Paragraph("<i>Bachelor of Science in Computer Science</i> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 06/20", body_style))
        story.append(Paragraph("GPA: 3.7/4.0, Magna Cum Laude", body_style))
        story.append(Spacer(1, 8))
        
        # Work Experience
        story.append(Paragraph("<b>WORK EXPERIENCE</b>", section_style))
        
        # Current Job
        story.append(Paragraph("<b>TECHVISION INC</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; San Francisco, CA", body_style))
        story.append(Paragraph("<i>Senior Product Manager</i> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 07/23 -- Present", body_style))
        
        achievements_current = [
            "Led cross-functional team to launch new assessment module, resulting in 40% increase in student engagement and 25% improvement in learning outcomes",
            "Implemented agile development methodology across product team, reducing feature delivery time by 30% and improving code quality metrics by 50%",
            "Conducted comprehensive user research and usability testing with 500+ teachers, identifying key pain points that informed product roadmap priorities",
            "Collaborated with engineering and design teams to redesign core user interface, improving user satisfaction scores by 35% and reducing support tickets by 20%"
        ]
        
        for achievement in achievements_current:
            story.append(Paragraph(f"• {achievement}", bullet_style))
        
        story.append(Spacer(1, 6))
        
        # Previous Job
        story.append(Paragraph("<b>INNOVATELABS</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Palo Alto, CA", body_style))
        story.append(Paragraph("<i>Product Manager</i> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 07/21 -- 07/23", body_style))
        
        achievements_previous = [
            "Developed and launched analytics dashboard feature used by 80% of customers, generating $2M additional ARR",
            "Led A/B testing program for key product features, improving conversion rates by 25% through data-driven optimization"
        ]
        
        for achievement in achievements_previous:
            story.append(Paragraph(f"• {achievement}", bullet_style))
        
        story.append(Spacer(1, 8))
        
        # Technical Skills
        story.append(Paragraph("<b>TECHNICAL SKILLS</b>", section_style))
        skills_text = "Requirements Gathering, Data Analysis, Product Management, User Experience Design, Figma, EdTech, K-12 Education, Cross-functional Collaboration, Agile Methodologies, Scrum, User Research, SQL, Python, Jira, Confluence"
        story.append(Paragraph(f"<b>Core Skills:</b> {skills_text}", body_style))
        
        # Build PDF
        doc.build(story)
        
        print(f"✅ PDF generated with reportlab: {output_file}")
        return output_file
        
    except ImportError:
        print("❌ reportlab not installed. Install with: pip install reportlab")
        return None
    except Exception as e:
        print(f"❌ reportlab PDF generation failed: {e}")
        return None

async def main():
    """Main function to compile LaTeX to PDF"""
    print("🚀 Compiling LaTeX Resume to PDF")
    print("=" * 50)
    
    # Check for LaTeX file
    tex_file = Path("data/generated/sample_tailored_resume.tex")
    if not tex_file.exists():
        print(f"❌ LaTeX file not found: {tex_file}")
        return
    
    print(f"📄 Found LaTeX file: {tex_file}")
    
    # Try to find pdflatex
    pdflatex_path = find_pdflatex()
    
    if pdflatex_path:
        # Use the project's LaTeX service
        try:
            latex_content = tex_file.read_text()
            print(f"📝 LaTeX content length: {len(latex_content)} characters")
            
            # Modify the service to use the found pdflatex path
            original_cmd = latex_generation_service._compile_latex_to_pdf
            
            # Try compilation
            success, pdf_path, error_msg = latex_generation_service._compile_latex_to_pdf(
                latex_content, "sample_tailored_resume"
            )
            
            if success:
                print(f"✅ PDF compiled successfully: {pdf_path}")
                return pdf_path
            else:
                print(f"❌ LaTeX compilation failed: {error_msg}")
                
        except Exception as e:
            print(f"❌ Error using LaTeX service: {e}")
    
    # Try alternative compilation methods
    pdf_path = try_alternative_compilation()
    if pdf_path:
        return pdf_path
    
    # Try reportlab as fallback
    pdf_path = create_pdf_with_reportlab()
    if pdf_path:
        return pdf_path
    
    print("❌ All PDF generation methods failed")
    print("💡 Recommendations:")
    print("  1. Install MacTeX: brew install --cask mactex")
    print("  2. Install BasicTeX: brew install --cask basictex")
    print("  3. Install tectonic: brew install tectonic")
    print("  4. Install reportlab: pip install reportlab")
    
    return None

if __name__ == "__main__":
    pdf_path = asyncio.run(main())
    if pdf_path:
        print(f"\n🎉 Resume PDF ready: {pdf_path}")
        
        # Show file info
        if Path(pdf_path).exists():
            size_kb = Path(pdf_path).stat().st_size / 1024
            print(f"📊 File size: {size_kb:.1f} KB")
            print(f"📂 Location: {Path(pdf_path).absolute()}")
    else:
        print(f"\n❌ PDF generation failed")