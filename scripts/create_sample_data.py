#!/usr/bin/env python3
"""
Create sample user data for testing TailerAI v2.0 content selection.
Populates database with realistic product manager profile data.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from uuid import UUID

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.database_service import db_service, initialize_database
from app.models.database import UserProfile, WorkExperience, Achievement, Skill, EducationEntry, Project

def create_sample_user_data():
    """Create comprehensive sample user data for testing."""
    print("🗄️ Initializing database...")
    initialize_database()
    
    try:
        with db_service.get_session() as session:
            # Find existing user or get first user
            user_profile = session.query(UserProfile).first()
            if not user_profile:
                print("❌ No user profile found - please create a user first")
                return None
            
            profile_id = user_profile.id
            print(f"👤 Found user profile: {profile_id}")
            
            # Clear existing data for clean test
            session.query(Achievement).filter_by(profile_id=profile_id).delete()
            session.query(WorkExperience).filter_by(profile_id=profile_id).delete()
            session.query(Skill).filter_by(profile_id=profile_id).delete()
            session.query(EducationEntry).filter_by(profile_id=profile_id).delete()
            session.query(Project).filter_by(profile_id=profile_id).delete()
            session.commit()
            
            # Create Work Experiences
            print("💼 Creating work experiences...")
            
            # Current Job - Senior Product Manager
            current_job = WorkExperience(
                profile_id=profile_id,
                company_name="TechVision Inc",
                position_title="Senior Product Manager",
                employment_type="full_time",
                start_date=datetime.now() - timedelta(days=730),  # 2 years ago
                end_date=None,  # Current job
                location="San Francisco, CA",
                company_size="500-1000",
                industry="EdTech",
                company_description="Leading educational technology platform serving K-12 schools",
                role_summary="Lead product strategy and development for core learning management platform",
                team_size=8,
                department="Product"
            )
            session.add(current_job)
            session.commit()
            session.refresh(current_job)
            
            # Previous Job - Product Manager
            previous_job = WorkExperience(
                profile_id=profile_id,
                company_name="InnovateLabs",
                position_title="Product Manager",
                employment_type="full_time",
                start_date=datetime.now() - timedelta(days=1460),  # 4 years ago
                end_date=datetime.now() - timedelta(days=730),  # 2 years ago
                location="Palo Alto, CA",
                company_size="100-500",
                industry="SaaS",
                company_description="B2B SaaS platform for data analytics",
                role_summary="Managed product roadmap for analytics dashboard and reporting tools",
                team_size=5,
                department="Product"
            )
            session.add(previous_job)
            session.commit()
            session.refresh(previous_job)
            
            # Create Achievements
            print("🏆 Creating achievements...")
            
            achievements = [
                # Current job achievements
                Achievement(
                    profile_id=profile_id,
                    experience_id=current_job.id,
                    achievement_text="Led cross-functional team to launch new assessment module, resulting in 40% increase in student engagement and 25% improvement in learning outcomes",
                    achievement_category="leadership",
                    impact_level=9,
                    business_function="Product Development",
                    quantified_metrics=["40% increase in student engagement", "25% improvement in learning outcomes"],
                    skills_demonstrated=["Product Management", "Cross-functional Collaboration", "Data Analysis", "User Experience Design"],
                    time_period="2024",
                    context_tags=["EdTech", "K-12", "Assessment", "Student Engagement"]
                ),
                Achievement(
                    profile_id=profile_id,
                    experience_id=current_job.id,
                    achievement_text="Implemented agile development methodology across product team, reducing feature delivery time by 30% and improving code quality metrics by 50%",
                    achievement_category="process",
                    impact_level=8,
                    business_function="Operations",
                    quantified_metrics=["30% reduction in delivery time", "50% improvement in code quality"],
                    skills_demonstrated=["Agile Methodologies", "Process Improvement", "Team Leadership", "Project Management"],
                    time_period="2023",
                    context_tags=["Agile", "Scrum", "Development", "Quality"]
                ),
                Achievement(
                    profile_id=profile_id,
                    experience_id=current_job.id,
                    achievement_text="Conducted comprehensive user research and usability testing with 500+ teachers, identifying key pain points that informed product roadmap priorities",
                    achievement_category="strategic",
                    impact_level=7,
                    business_function="Research",
                    quantified_metrics=["500+ teachers surveyed", "15 key insights identified"],
                    skills_demonstrated=["User Research", "Usability Testing", "Data Analysis", "Requirements Gathering"],
                    time_period="2024",
                    context_tags=["User Research", "Teachers", "K-12", "Product Strategy"]
                ),
                Achievement(
                    profile_id=profile_id,
                    experience_id=current_job.id,
                    achievement_text="Collaborated with engineering and design teams to redesign core user interface, improving user satisfaction scores by 35% and reducing support tickets by 20%",
                    achievement_category="technical",
                    impact_level=8,
                    business_function="Design",
                    quantified_metrics=["35% improvement in satisfaction", "20% reduction in support tickets"],
                    skills_demonstrated=["UI/UX Design", "Cross-functional Collaboration", "User Experience", "Problem Solving"],
                    time_period="2023",
                    context_tags=["UI/UX", "User Interface", "Design", "Engineering"]
                ),
                
                # Previous job achievements
                Achievement(
                    profile_id=profile_id,
                    experience_id=previous_job.id,
                    achievement_text="Developed and launched analytics dashboard feature used by 80% of customers, generating $2M additional ARR",
                    achievement_category="financial",
                    impact_level=9,
                    business_function="Revenue",
                    quantified_metrics=["80% customer adoption", "$2M additional ARR"],
                    skills_demonstrated=["Product Development", "Data Analytics", "Revenue Growth", "Customer Success"],
                    time_period="2022",
                    context_tags=["Analytics", "Dashboard", "SaaS", "Revenue"]
                ),
                Achievement(
                    profile_id=profile_id,
                    experience_id=previous_job.id,
                    achievement_text="Led A/B testing program for key product features, improving conversion rates by 25% through data-driven optimization",
                    achievement_category="operational",
                    impact_level=7,
                    business_function="Growth",
                    quantified_metrics=["25% improvement in conversion", "50+ A/B tests conducted"],
                    skills_demonstrated=["A/B Testing", "Data Analysis", "Conversion Optimization", "Statistical Analysis"],
                    time_period="2021",
                    context_tags=["A/B Testing", "Conversion", "Optimization", "Data-Driven"]
                )
            ]
            
            for achievement in achievements:
                session.add(achievement)
            session.commit()
            
            # Create Skills
            print("🔧 Creating skills...")
            
            skills = [
                # Core PM skills
                Skill(profile_id=profile_id, skill_name="Product Management", skill_category="Core", proficiency_level="expert", years_experience=5),
                Skill(profile_id=profile_id, skill_name="User Experience Design", skill_category="Design", proficiency_level="advanced", years_experience=4),
                Skill(profile_id=profile_id, skill_name="Data Analysis", skill_category="Analytics", proficiency_level="advanced", years_experience=4),
                Skill(profile_id=profile_id, skill_name="Cross-functional Collaboration", skill_category="Leadership", proficiency_level="expert", years_experience=5),
                Skill(profile_id=profile_id, skill_name="Requirements Gathering", skill_category="Analysis", proficiency_level="expert", years_experience=5),
                
                # Technical skills
                Skill(profile_id=profile_id, skill_name="SQL", skill_category="Technical", proficiency_level="intermediate", years_experience=3),
                Skill(profile_id=profile_id, skill_name="Python", skill_category="Technical", proficiency_level="beginner", years_experience=1),
                Skill(profile_id=profile_id, skill_name="Jira", skill_category="Tools", proficiency_level="advanced", years_experience=4),
                Skill(profile_id=profile_id, skill_name="Confluence", skill_category="Tools", proficiency_level="advanced", years_experience=4),
                Skill(profile_id=profile_id, skill_name="Figma", skill_category="Design", proficiency_level="intermediate", years_experience=2),
                
                # Methodologies
                Skill(profile_id=profile_id, skill_name="Agile Methodologies", skill_category="Process", proficiency_level="expert", years_experience=5),
                Skill(profile_id=profile_id, skill_name="Scrum", skill_category="Process", proficiency_level="expert", years_experience=5),
                Skill(profile_id=profile_id, skill_name="User Research", skill_category="Research", proficiency_level="advanced", years_experience=3),
                Skill(profile_id=profile_id, skill_name="A/B Testing", skill_category="Analytics", proficiency_level="advanced", years_experience=3),
                Skill(profile_id=profile_id, skill_name="Technical Communication", skill_category="Communication", proficiency_level="expert", years_experience=5),
                
                # Industry specific
                Skill(profile_id=profile_id, skill_name="EdTech", skill_category="Industry", proficiency_level="advanced", years_experience=2),
                Skill(profile_id=profile_id, skill_name="K-12 Education", skill_category="Industry", proficiency_level="intermediate", years_experience=2),
                Skill(profile_id=profile_id, skill_name="SaaS", skill_category="Industry", proficiency_level="advanced", years_experience=4)
            ]
            
            for skill in skills:
                session.add(skill)
            session.commit()
            
            # Create Education
            print("🎓 Creating education...")
            
            education = EducationEntry(
                profile_id=profile_id,
                institution_name="Stanford University",
                degree_type="Bachelor of Science",
                field_of_study="Computer Science",
                start_date=datetime(2016, 9, 1),
                end_date=datetime(2020, 6, 15),
                gpa=3.7,
                gpa_scale=4.0,
                honors="Magna Cum Laude",
                relevant_coursework=["Human-Computer Interaction", "Data Structures", "Database Systems", "Software Engineering"],
                location="Stanford, CA",
                institution_type="University"
            )
            session.add(education)
            session.commit()
            
            # Create Projects
            print("📁 Creating projects...")
            
            project = Project(
                profile_id=profile_id,
                project_name="Learning Analytics Platform",
                project_description="Developed comprehensive analytics platform for K-12 educational insights",
                role="Product Lead",
                start_date=datetime.now() - timedelta(days=365),
                end_date=datetime.now() - timedelta(days=180),
                project_type="Product Development",
                technologies_used=["Python", "SQL", "React", "Data Visualization"],
                key_achievements=["Improved student outcome tracking by 60%", "Reduced teacher workload by 30%"],
                metrics=["60% improvement in tracking", "30% workload reduction", "500+ schools adopted"],
                team_size=6
            )
            session.add(project)
            session.commit()
            
            print("✅ Sample data created successfully!")
            print(f"📊 Created:")
            print(f"  • 2 Work Experiences")
            print(f"  • 6 Achievements")
            print(f"  • 18 Skills")
            print(f"  • 1 Education Entry")
            print(f"  • 1 Project")
            
            return profile_id
            
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        return None

if __name__ == "__main__":
    profile_id = create_sample_user_data()
    if profile_id:
        print(f"\n🎉 Sample data ready for testing with profile: {profile_id}")
    else:
        print("\n❌ Failed to create sample data")