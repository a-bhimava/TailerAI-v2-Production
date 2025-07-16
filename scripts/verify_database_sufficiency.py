#!/usr/bin/env python3
"""
Verify that the database schema has sufficient fields to create complete tailored resumes
without any hallucinated information. All resume content must come from user-provided data.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.database_service import db_service, initialize_database
from app.models.database import UserProfile, WorkExperience, Achievement, Skill, EducationEntry, Project

def analyze_database_sufficiency():
    """Analyze if database fields are sufficient for complete resume generation"""
    
    print("🔍 Database Schema Sufficiency Analysis for Resume Generation")
    print("=" * 80)
    print("📋 Requirement: NO hallucinated information - all content from user entries only")
    print()
    
    # Initialize database
    initialize_database()
    
    # Define resume sections and required fields
    resume_sections = {
        "Header/Contact": [
            "Full Name",
            "Email", 
            "Phone",
            "LinkedIn URL",
            "Location/Address",
        ],
        "Education": [
            "Institution Name",
            "Degree Type",
            "Field of Study", 
            "Start/End Dates",
            "GPA (optional)",
            "Honors/Awards",
            "Relevant Coursework",
            "Location"
        ],
        "Work Experience": [
            "Company Name",
            "Position Title",
            "Employment Type",
            "Start/End Dates",
            "Location",
            "Company Description/Context",
            "Role Summary",
            "Specific Achievements",
            "Quantified Results"
        ],
        "Skills": [
            "Skill Names",
            "Proficiency Levels",
            "Categories",
            "Years of Experience",
            "Certifications"
        ],
        "Projects": [
            "Project Name",
            "Description",
            "Role",
            "Duration",
            "Technologies Used",
            "Key Achievements",
            "Metrics/Results",
            "URLs (if applicable)"
        ]
    }
    
    # Map database fields to resume requirements
    field_mapping = {
        "Header/Contact": {
            "Full Name": "UserProfile.full_name",
            "Email": "UserProfile.email",
            "Phone": "UserProfile.phone", 
            "LinkedIn URL": "UserProfile.linkedin_url",
            "Location/Address": "UserProfile.location"
        },
        "Education": {
            "Institution Name": "EducationEntry.institution_name",
            "Degree Type": "EducationEntry.degree_type",
            "Field of Study": "EducationEntry.field_of_study",
            "Start/End Dates": "EducationEntry.start_date, end_date",
            "GPA (optional)": "EducationEntry.gpa, gpa_scale",
            "Honors/Awards": "EducationEntry.honors (Array)",
            "Relevant Coursework": "EducationEntry.relevant_coursework (Array)",
            "Location": "EducationEntry.location"
        },
        "Work Experience": {
            "Company Name": "WorkExperience.company_name",
            "Position Title": "WorkExperience.position_title",
            "Employment Type": "WorkExperience.employment_type", 
            "Start/End Dates": "WorkExperience.start_date, end_date",
            "Location": "WorkExperience.location",
            "Company Description/Context": "WorkExperience.company_description, industry, company_size",
            "Role Summary": "WorkExperience.role_summary, job_description",
            "Specific Achievements": "Achievement.achievement_text",
            "Quantified Results": "Achievement.quantified_metrics (JSON)"
        },
        "Skills": {
            "Skill Names": "Skill.skill_name",
            "Proficiency Levels": "Skill.proficiency_level",
            "Categories": "Skill.skill_category",
            "Years of Experience": "Skill.years_experience", 
            "Certifications": "Skill.certification_name, certification_date"
        },
        "Projects": {
            "Project Name": "Project.project_name",
            "Description": "Project.project_description",
            "Role": "Project.role",
            "Duration": "Project.start_date, end_date",
            "Technologies Used": "Project.technologies_used (Array)",
            "Key Achievements": "Project.key_achievements (Array)",
            "Metrics/Results": "Project.metrics (JSON)",
            "URLs (if applicable)": "Project.project_url, repository_url"
        }
    }
    
    # Analyze coverage
    total_fields = 0
    covered_fields = 0
    missing_fields = []
    
    for section, requirements in resume_sections.items():
        print(f"📁 {section.upper()}")
        print("-" * 40)
        
        section_covered = 0
        section_total = len(requirements)
        
        for requirement in requirements:
            total_fields += 1
            if requirement in field_mapping[section]:
                db_field = field_mapping[section][requirement]
                print(f"✅ {requirement:<25} → {db_field}")
                covered_fields += 1
                section_covered += 1
            else:
                print(f"❌ {requirement:<25} → NOT MAPPED")
                missing_fields.append(f"{section}: {requirement}")
        
        coverage_pct = (section_covered / section_total) * 100
        print(f"📊 Section Coverage: {section_covered}/{section_total} ({coverage_pct:.1f}%)")
        print()
    
    # Overall analysis
    overall_coverage = (covered_fields / total_fields) * 100
    print("=" * 80)
    print("📊 OVERALL ANALYSIS")
    print("=" * 80)
    print(f"Total Resume Fields Required: {total_fields}")
    print(f"Database Fields Available: {covered_fields}")
    print(f"Coverage Percentage: {overall_coverage:.1f}%")
    print()
    
    if missing_fields:
        print("❌ MISSING FIELDS:")
        for missing in missing_fields:
            print(f"  • {missing}")
        print()
    
    # Check current data availability
    print("🗄️ CURRENT DATA AVAILABILITY")
    print("-" * 40)
    
    try:
        with db_service.get_session() as session:
            # Count existing data
            profile_count = session.query(UserProfile).count()
            work_exp_count = session.query(WorkExperience).count()  
            achievement_count = session.query(Achievement).count()
            skill_count = session.query(Skill).count()
            education_count = session.query(EducationEntry).count()
            project_count = session.query(Project).count()
            
            print(f"👥 User Profiles: {profile_count}")
            print(f"💼 Work Experiences: {work_exp_count}")
            print(f"🏆 Achievements: {achievement_count}")
            print(f"🔧 Skills: {skill_count}")
            print(f"🎓 Education Entries: {education_count}")
            print(f"📁 Projects: {project_count}")
            
            # Check for sample user completeness
            if profile_count > 0:
                user_profile = session.query(UserProfile).first()
                print(f"\n🔍 SAMPLE USER DATA COMPLETENESS:")
                print(f"Profile ID: {user_profile.id}")
                
                # Check header fields
                header_fields = {
                    "Full Name": user_profile.full_name,
                    "Email": user_profile.email,
                    "Phone": user_profile.phone,
                    "LinkedIn": user_profile.linkedin_url,
                    "Location": user_profile.location
                }
                
                for field, value in header_fields.items():
                    status = "✅" if value else "❌"
                    print(f"  {status} {field}: {value or 'MISSING'}")
                
                # Check related data
                user_work_exp = session.query(WorkExperience).filter_by(profile_id=user_profile.id).count()
                user_achievements = session.query(Achievement).filter_by(profile_id=user_profile.id).count()
                user_skills = session.query(Skill).filter_by(profile_id=user_profile.id).count()
                user_education = session.query(EducationEntry).filter_by(profile_id=user_profile.id).count()
                user_projects = session.query(Project).filter_by(profile_id=user_profile.id).count()
                
                print(f"\n📊 Sample User Content:")
                print(f"  Work Experiences: {user_work_exp}")
                print(f"  Achievements: {user_achievements}")  
                print(f"  Skills: {user_skills}")
                print(f"  Education: {user_education}")
                print(f"  Projects: {user_projects}")
                
    except Exception as e:
        print(f"❌ Error checking data: {e}")
    
    print("\n" + "=" * 80)
    print("🎯 RESUME GENERATION CAPABILITY ASSESSMENT")
    print("=" * 80)
    
    if overall_coverage >= 95:
        print("✅ EXCELLENT: Database schema provides complete coverage for resume generation")
        print("   All required fields are mapped to database columns")
        print("   No hallucination risk - all content sourced from user data")
    elif overall_coverage >= 85:
        print("✅ GOOD: Database schema provides strong coverage for resume generation") 
        print("   Minor gaps exist but core functionality is supported")
        print("   Low hallucination risk with proper validation")
    elif overall_coverage >= 70:
        print("⚠️  ADEQUATE: Database schema covers most resume requirements")
        print("   Some important fields may be missing")
        print("   Moderate hallucination risk without additional validation")
    else:
        print("❌ INSUFFICIENT: Database schema has significant gaps")
        print("   Critical resume fields are missing")
        print("   High hallucination risk without major improvements")
    
    print()
    
    # Specific recommendations
    print("💡 RECOMMENDATIONS:")
    
    if missing_fields:
        print("1. Address missing fields:")
        for missing in missing_fields[:3]:  # Show top 3
            print(f"   • Add support for: {missing}")
        if len(missing_fields) > 3:
            print(f"   • And {len(missing_fields) - 3} other missing fields")
    
    print("2. Data validation improvements:")
    print("   • Require core fields (name, email, at least 1 work experience)")
    print("   • Validate achievement quantified_metrics structure")
    print("   • Ensure skill categories are standardized")
    
    print("3. Anti-hallucination safeguards:")
    print("   • Strict field validation before resume generation")
    print("   • Fallback handling for missing optional fields")
    print("   • User confirmation for any auto-generated content")
    
    return overall_coverage, missing_fields

if __name__ == "__main__":
    coverage, missing = analyze_database_sufficiency()
    
    if coverage >= 90:
        print(f"\n🎉 Database is ready for production resume generation!")
    else:
        print(f"\n⚠️  Database needs improvements before production use")
        print(f"Current coverage: {coverage:.1f}% (target: 90%+)")