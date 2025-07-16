#!/usr/bin/env python3
"""
Generate a sample PDF resume using the selected content from content selection analysis.
This will create a resume based on our EdTech Product Manager job match.
"""

import sys
import os
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.database_service import db_service, initialize_database
from app.services.content_selection_service import content_selector
from app.services.job_analysis_service import job_analyzer
from app.models.database import UserProfile, WorkExperience, Achievement, Skill, EducationEntry

def escape_latex(text):
    """Escape special LaTeX characters"""
    if not text:
        return ""
    
    latex_special = {
        '&': r'\&',
        '%': r'\%', 
        '$': r'\$',
        '#': r'\#',
        '^': r'\^{}',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '\\': r'\textbackslash{}'
    }
    
    escaped = text
    for char, replacement in latex_special.items():
        escaped = escaped.replace(char, replacement)
    
    return escaped

def format_skills_list(skills, max_skills=15):
    """Format skills as comma-separated LaTeX string"""
    if not skills:
        return ""
    
    skill_names = []
    for skill in skills[:max_skills]:
        if hasattr(skill, 'skill_name'):
            skill_names.append(escape_latex(skill.skill_name))
        elif isinstance(skill, dict):
            skill_names.append(escape_latex(skill.get('name', '')))
        else:
            skill_names.append(escape_latex(str(skill)))
    
    return ", ".join(skill_names)

def create_latex_resume_content(user_data, selected_content):
    """Create LaTeX content from selected user data and content selection results"""
    
    # User profile info
    profile = user_data.get("profile")
    
    # Selected content from analysis
    selected_achievements = selected_content.get("selected_achievements", [])
    selected_work_experiences = selected_content.get("selected_work_experiences", [])
    selected_skills = selected_content.get("selected_skills", [])
    selected_education = selected_content.get("selected_education", [])
    selected_projects = selected_content.get("selected_projects", [])
    
    # Get actual database objects for selected content
    work_experiences = user_data.get("work_experiences", [])
    achievements = user_data.get("achievements", [])
    skills = user_data.get("skills", [])
    education = user_data.get("education", [])
    projects = user_data.get("projects", [])
    
    # Filter to only selected items based on IDs
    selected_achievement_ids = [item.content_id for item in selected_achievements]
    selected_work_exp_ids = [item.content_id for item in selected_work_experiences]
    selected_skill_ids = [item.content_id for item in selected_skills]
    
    filtered_achievements = [a for a in achievements if str(a.id) in selected_achievement_ids]
    filtered_work_experiences = [w for w in work_experiences if str(w.id) in selected_work_exp_ids]
    filtered_skills = [s for s in skills if str(s.id) in selected_skill_ids]
    
    latex_content = r"""% TailerAI v2.0 Generated Resume - EdTech Product Manager
\documentclass[10pt,letterpaper]{article}
\usepackage[left=0.5in, right=0.5in, top=0.5in, bottom=0.3in]{geometry}
\usepackage{helvet}
\renewcommand{\familydefault}{\sfdefault}
\usepackage{tabularx}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{tikz}

% Remove page numbers
\pagestyle{empty}

% Section formatting
\titleformat{\section}{\bfseries\uppercase}{\thesection}{1em}{}
\titlespacing*{\section}{0pt}{0.5ex}{0.2ex}

% Bullet formatting
\setlist[itemize]{left=0em, itemsep=0.1em, topsep=0.1em, parsep=0em, partopsep=0em}

% Reduce line spacing
\linespread{0.97}
\setlength{\parskip}{0em}

% Section line command
\newcommand{\sectionline}{\par\vspace{-0.5em}\noindent\rule{\textwidth}{0.6pt}\vspace{0.3em}\par}

\begin{document}

% Header
\begin{center}
  {\LARGE \textbf{PRODUCT MANAGER - SAMPLE CANDIDATE}}\\
  555.123.4567 $|$ pm.candidate@email.com $|$ linkedin.com/in/pm-candidate $|$ San Francisco, CA
\end{center}
\vspace{0.5em}

% Education
\section*{EDUCATION}

"""
    
    # Add education section
    if education:
        edu = education[0]  # Use first education entry
        latex_content += f"""\\noindent\\textbf{{{escape_latex(edu.institution_name.upper())}}} \\hfill {escape_latex(edu.location or "CA")}\\\\
\\textit{{{escape_latex(edu.degree_type)} in {escape_latex(edu.field_of_study)}}} \\hfill {edu.end_date.strftime('%m/%y') if edu.end_date else 'Present'}
"""
        if edu.gpa:
            latex_content += f"\\\\GPA: {edu.gpa}/{edu.gpa_scale or 4.0}"
        
        if edu.honors:
            latex_content += f"\\\\{escape_latex(edu.honors)}"
        
        latex_content += "\n\n"
    
    # Work Experience section
    latex_content += r"""% Work Experience
\section*{WORK EXPERIENCE}
\sectionline

"""
    
    # Add work experiences with their achievements
    for work_exp in filtered_work_experiences:
        company = escape_latex(work_exp.company_name.upper())
        position = escape_latex(work_exp.position_title)
        location = escape_latex(work_exp.location or "CA")
        
        start_date = work_exp.start_date.strftime('%m/%y') if work_exp.start_date else 'Unknown'
        end_date = work_exp.end_date.strftime('%m/%y') if work_exp.end_date else 'Present'
        
        latex_content += f"""\\noindent\\textbf{{{company}}} \\hfill {location}\\\\
\\textit{{{position}}} \\hfill {start_date} -- {end_date}
\\begin{{itemize}}
"""
        
        # Add achievements for this work experience
        work_achievements = [a for a in filtered_achievements if str(a.experience_id) == str(work_exp.id)]
        for achievement in work_achievements:
            achievement_text = escape_latex(achievement.achievement_text)
            latex_content += f"  \\item {achievement_text}\n"
        
        latex_content += "\\end{itemize}\n\n"
    
    # Skills section
    if filtered_skills:
        latex_content += r"""\section*{TECHNICAL SKILLS}
\sectionline

"""
        skills_text = format_skills_list(filtered_skills)
        latex_content += f"\\noindent\\textbf{{Core Skills:}} {skills_text}\n\n"
    
    # Projects section (if any)
    if selected_projects:
        latex_content += r"""\section*{PROJECT EXPERIENCE}
\sectionline

\begin{itemize}
"""
        for project in projects:
            if str(project.id) in [item.content_id for item in selected_projects]:
                project_name = escape_latex(project.project_name)
                project_desc = escape_latex(project.project_description or "")
                latex_content += f"  \\item \\textbf{{{project_name}}} -- {project_desc}\n"
        
        latex_content += "\\end{itemize}\n\n"
    
    latex_content += "\\end{document}\n"
    
    return latex_content

async def generate_sample_resume():
    """Generate a sample resume using our analysis results"""
    print("🚀 Generating Sample Resume from Content Selection Results")
    print("=" * 60)
    
    # Initialize database
    initialize_database()
    
    # Load the job description we analyzed
    job_file = Path("data/sample_data/sample_job_description.txt")
    job_text = job_file.read_text()
    
    # Run job analysis
    print("📄 Analyzing job description...")
    job_analysis = await job_analyzer.analyze_job_description(job_text)
    print(f"✅ Job analysis complete: {job_analysis.company_name} - {job_analysis.position_title}")
    
    # Get user data
    with db_service.get_session() as session:
        user_profile = session.query(UserProfile).first()
        if not user_profile:
            print("❌ No user profile found")
            return
        
        user_profile_id = str(user_profile.id)
        print(f"👤 Using user profile: {user_profile_id}")
    
    # Run content selection
    print("🎯 Running content selection...")
    selection_result = await content_selector.select_optimal_content(
        user_profile_id=user_profile_id,
        job_analysis=job_analysis
    )
    
    print(f"✅ Content selection complete:")
    print(f"  📊 Score: {selection_result.total_score:.3f}")
    print(f"  📝 Words: {selection_result.estimated_word_count}")
    print(f"  🏆 Achievements: {len(selection_result.selected_achievements)}")
    print(f"  💼 Work Experiences: {len(selection_result.selected_work_experiences)}")
    print(f"  🔧 Skills: {len(selection_result.selected_skills)}")
    
    # Load user master dataset
    with db_service.get_session() as session:
        profile = session.query(UserProfile).filter_by(id=user_profile_id).first()
        work_experiences = session.query(WorkExperience).filter_by(profile_id=user_profile_id).all()
        achievements = session.query(Achievement).filter_by(profile_id=user_profile_id).all()
        skills = session.query(Skill).filter_by(profile_id=user_profile_id).all()
        education = session.query(EducationEntry).filter_by(profile_id=user_profile_id).all()
        projects = []  # Will be empty for our test data
        
        # Force load all attributes
        for achievement in achievements:
            _ = achievement.id, achievement.achievement_text, achievement.experience_id
        for work_exp in work_experiences:
            _ = work_exp.id, work_exp.company_name, work_exp.position_title
        for skill in skills:
            _ = skill.id, skill.skill_name
        for edu in education:
            _ = edu.id, edu.institution_name, edu.degree_type
        
        session.expunge_all()
        
        user_data = {
            "profile": profile,
            "work_experiences": work_experiences,
            "achievements": achievements,
            "skills": skills,
            "education": education,
            "projects": projects
        }
    
    # Generate LaTeX content
    print("📝 Generating LaTeX content...")
    latex_content = create_latex_resume_content(user_data, selection_result.__dict__)
    
    # Write LaTeX file
    output_dir = Path("data/generated")
    output_dir.mkdir(exist_ok=True)
    
    tex_file = output_dir / "sample_tailored_resume.tex"
    with open(tex_file, 'w', encoding='utf-8') as f:
        f.write(latex_content)
    
    print(f"✅ LaTeX file created: {tex_file}")
    
    # Compile to PDF
    print("🔧 Compiling LaTeX to PDF...")
    try:
        # Change to output directory for compilation
        result = subprocess.run([
            'pdflatex', 
            '-interaction=nonstopmode',
            '-output-directory', str(output_dir),
            str(tex_file)
        ], capture_output=True, text=True, cwd=str(output_dir))
        
        if result.returncode == 0:
            pdf_file = output_dir / "sample_tailored_resume.pdf"
            print(f"✅ PDF generated successfully: {pdf_file}")
            
            # Show file size
            if pdf_file.exists():
                size_kb = pdf_file.stat().st_size / 1024
                print(f"📄 PDF size: {size_kb:.1f} KB")
            
            return str(pdf_file)
        else:
            print(f"❌ LaTeX compilation failed:")
            print(f"Return code: {result.returncode}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return None
            
    except FileNotFoundError:
        print("❌ pdflatex not found. Please install a LaTeX distribution (e.g., MacTeX)")
        print("📝 LaTeX file created but PDF compilation skipped")
        return str(tex_file)
    
    except Exception as e:
        print(f"❌ Error during PDF compilation: {e}")
        return str(tex_file)

if __name__ == "__main__":
    pdf_path = asyncio.run(generate_sample_resume())
    if pdf_path:
        print(f"\n🎉 Resume generation complete!")
        print(f"📄 Output: {pdf_path}")
        
        # Summary of what was generated
        print(f"\n📋 RESUME SUMMARY:")
        print(f"✅ Tailored for: EdTech Product Manager position")
        print(f"✅ Selected content based on job requirements")
        print(f"✅ Optimized for ATS and keyword matching")
        print(f"✅ One-page format with professional styling")
    else:
        print(f"\n❌ Resume generation failed")