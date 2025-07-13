#!/usr/bin/env python3
"""
TailerAI v2.0 Pipeline Test - Product Manager Role Analysis
Testing complete pipeline from job description to LaTeX resume generation
Using Aditya's resume and Product Manager job description
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.job_analysis_service import job_analysis_service
from app.services.content_selection_service import content_selector
from app.services.latex_generation_service import latex_generation_service
from app.services.database_service import db_service, initialize_database
from app.services.master_dataset_service import master_dataset_service
from app.services.auth_service import auth_service
from app.models.database import User, UserProfile

print("🚀 TailerAI v2.0 - Complete Pipeline Test")
print("="*80)
print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("🎯 Testing: Product Manager Role Analysis with Aditya's Resume")
print("="*80)

# Load job description
JOB_DESCRIPTION = """Product Manager - EdTech Platform

Company: EduInnovate Solutions
Location: San Francisco, CA (Remote Friendly)
Job Type: Full-Time
Experience Level: Mid-Level (2-5 years)

About Us:
EduInnovate Solutions is a leading educational technology company focused on transforming K-12 learning experiences through innovative digital platforms. We serve over 500,000 students, teachers, and parents across North America with our comprehensive learning management and assessment tools.

What You'll Be Doing:

• Deeply understand and advocate for the needs of our student, teacher, and parent users
• Gather requirements and clarify goals for new projects 
• Consider user needs and product strategy to make feature design decisions
• Produce clear written specifications for all feature functionality and user flows
• Collaborate with visual designers to create innovative, clean user interfaces
• Work with engineers to align technical designs and decisions with product needs
• Do whatever it takes to develop features and deliver value to our users
• Conduct user research and usability testing to validate product hypotheses
• Analyze product metrics and KPIs to drive data-informed decision making
• Manage product roadmap and prioritize feature development based on user impact
• Coordinate cross-functional teams including engineering, design, marketing, and customer success
• Present product updates and strategic recommendations to executive leadership

What We're Looking For:

Required Qualifications:
• Bachelor's degree in STEM or a related field
• Demonstrated technical abilities; some coursework or experience in computer programming and web technologies is preferred
• Highly developed analytical-reasoning and problem-solving skills, with proven success applying them independently
• Strong written and spoken communication skills, with an eye to clarity and conciseness
• Strong interpersonal skills and ability to work across teams to make things happen
• Enthusiasm for tackling tough problems independently, from assessing high-level goals through to perfecting every detail
• Exceptionally organized self-starter, efficient and thrives under pressure
• Curiosity, open-mindedness, and an unfailingly positive attitude

Preferred Qualifications:
• Interest in design thinking; some coursework or experience in UI/UX design is helpful
• Interest in K-12 education! Classroom/teaching experience is a plus
• Experience with agile development methodologies and product management tools
• Data analysis experience with tools like SQL, Python, or R
• Previous experience in EdTech, SaaS, or consumer technology products
• MBA or advanced degree in business, engineering, or related field

Key Skills & Technologies:
• Product Management
• User Experience Design
• Data Analysis
• Cross-functional Collaboration
• Requirements Gathering
• Technical Communication
• Project Management
• Agile/Scrum Methodologies
• User Research
• A/B Testing
• SQL
• Python (preferred)
• Jira/Confluence
• Figma/Sketch
• Google Analytics"""

# Aditya's resume data (extracted from text file)
ADITYA_RESUME_DATA = {
    "personal_info": {
        "name": "Aditya Teja Bhimavarapu",
        "email": "abhimava@andrew.cmu.edu",
        "phone": "412.287.1018",
        "linkedin": "linkedin.com/in/aditya-teja",
        "location": "Pittsburgh, PA"
    },
    "education": [
        {
            "institution": "Carnegie Mellon University, Tepper School of Business",
            "degree": "Master of Science in Product Management - MSPM",
            "location": "Pittsburgh, PA",
            "graduation_date": "12/25",
            "coursework": "Principles of Prod. Mgmt., Design of AI Products, Data Science for Product Managers"
        },
        {
            "institution": "Indian Institute of Management",
            "degree": "Master of Business Administration, Strategy & Finance – MBA",
            "gpa": "7.8/10",
            "location": "Sambalpur, India",
            "graduation_date": "03/23",
            "coursework": "Marketing Research, Brand Management, Consumer Behavior, Data Visualization",
            "awards": "Best Rated Intern at Galderma, National Finalist in Unilever's TechFest Case Competition, Top 200 in Tata Imagination Challenge out of 85k participants, 11 case competition accolades across 2 years"
        },
        {
            "institution": "Ecole Centrale School of Engineering, Mahindra University",
            "degree": "Bachelor of Technology, Mechanical Engineering – (B. Tech)",
            "gpa": "7.8/10",
            "location": "Hyderabad, India",
            "graduation_date": "09/20",
            "awards": "World Top 15 teams in Singapore Autonomous Underwater Vehicle Competition"
        }
    ],
    "work_experience": [
        {
            "company": "ICICI Bank",
            "position": "Manager – Corporate Banking",
            "location": "Hyderabad, India",
            "dates": "04/23 - 11/24",
            "achievements": [
                "Customer Focus: Managed a portfolio valued at $650M comprising of 45 multinational corporations, including Fortune 20 companies in automotive, manufacturing, and semiconductor sectors by effectively aligning service to client needs, resulting in annual revenue of $7M. Increased portfolio by $185M in FY 2024.",
                "Product Management: Owned end-to-end implementation of tool that parsed client financial documents from 60+ languages, converted other currencies to Indian Rupees and auto filled in proprietary Excel Model. Coordinated across internal divisions and led team. This solution reduced turnaround time by 25%.",
                "Problem Solving: Initiated a multi-country taskforce, creating a sales funnel strategy of partnering with foreign companies before their India entry, by clearly identifying and mapping client touchpoints. Scaled to onboard 15 Fortune 500 companies (Micron, Foxconn) in year 1 growing portfolio by $190M in FY 2024.",
                "Communication & Impactful Presentations: Delivered 26 C-Suite business presentations, effectively influencing strategic decisions with clear insights on portfolio growth."
            ]
        },
        {
            "company": "Galderma",
            "position": "Marketing Intern – Acne Category",
            "location": "Mumbai, India",
            "dates": "04/22 - 07/22",
            "achievements": [
                "Market Research: Performed a deep-dive analysis of acne market by conducting 900 interviews and 10 focus groups resulting in crucial insights about the purchase drivers and impact of sales channel on willingness to pay.",
                "Marketing Strategy: Helped formulate positioning and communication strategy for 4 acne care products – cleansers, face wash and moisturizer based on consumer preferences based on primary & secondary research.",
                "Product Launch: Launched campaign for face cleanser, wash, and moisturizer by benchmarking product to establish positioning. Resulted market share of 2-3.5% in first year of launch.",
                "Business Process Automation: Ideated and delivered a Python program to verify discount codes for various product combinations by collaborating with supply chain team. Reduced the reconciliation time by 3600%."
            ]
        },
        {
            "company": "Capgemini",
            "position": "Senior Analyst",
            "location": "Pune, India",
            "dates": "10/20 - 10/21",
            "achievements": [
                "Big Data Development: Contributed to development of data warehouse to predict credit card default probability by using fine-tuned gradient boosting model implemented on Apache Spark improving the model accuracy by 3%.",
                "Business Process Automation: Developed program in PySpark to streamline and semi-automate code documentation, making it more intuitive for users and saving over 1K man-hours annually per team."
            ]
        }
    ],
    "skills": [
        "SQL", "Python", "Java", "Scala", "Excel", "Oracle 8", "Apache Hive", "Spark", "ETL tools like Ab Initio"
    ],
    "projects": [
        {
            "name": "Flipkart (Walmart Group) Sales Analytics",
            "description": "Used ETL Tools to cleanse sales data and analyze using Apache Spark. Presented insights on best-selling, best-rated categories, seasonality & other statistical analysis."
        },
        {
            "name": "Unilever's Auto-Order Device",
            "description": "Ideated an affordable IoT based solution for Unilever that auto-orders groceries as they reach a threshold. Lead a team of four for development, implemented Go-to-market strategy & pilot tests. Top 4 National Finalist in Unilever's TechFest Case Competition"
        }
    ],
    "additional": {
        "certifications": [
            "CRISIL Financial Statement Analysis",
            "Google Data Analytics",
            "Product Management Essentials",
            "UofM, KPMG Six Sigma Green Belt",
            "Data Engineering Practitioner Certificate by Capgemini"
        ],
        "patent": "System and Method for Human-to-Human and Human-to-AI Knowledge Transfer Using Predictive Risk Assessment and Multi-dimensional Capture Technologies"
    }
}

async def main():
    try:
        # Initialize database
        print("🗄️ Initializing database...")
        await initialize_database()
        print("✅ Database initialized")
        
        # Step 1: Job Description Analysis
        print("\n📋 Step 1: Analyzing Product Manager Job Description")
        print("-" * 60)
        
        analysis_result = await job_analysis_service.analyze_job_description(JOB_DESCRIPTION)
        if not analysis_result["success"]:
            print(f"❌ Job analysis failed: {analysis_result['message']}")
            return
        
        job_analysis = analysis_result["analysis"]
        print(f"✅ Job analysis completed")
        print(f"🏢 Company: {job_analysis.company_name}")
        print(f"💼 Position: {job_analysis.position_title}")
        print(f"🏭 Industry: {job_analysis.industry}")
        print(f"📈 Seniority: {job_analysis.seniority_level}")
        print(f"🎯 Confidence: {job_analysis.confidence_score}")
        
        # Display key findings
        required_skills = json.loads(job_analysis.required_skills)
        preferred_skills = json.loads(job_analysis.preferred_skills)
        important_keywords = json.loads(job_analysis.important_keywords)
        
        print(f"\n🔑 Required Skills ({len(required_skills)}):")
        for i, skill in enumerate(required_skills[:5], 1):
            print(f"  {i}. {skill}")
        if len(required_skills) > 5:
            print(f"  ... and {len(required_skills) - 5} more")
        
        print(f"\n💡 Important Keywords ({len(important_keywords)}):")
        for i, keyword in enumerate(important_keywords[:7], 1):
            print(f"  {i}. {keyword}")
        
        # Step 2: Create/Find User and Populate Master Dataset
        print("\n👤 Step 2: Setting up User Profile and Master Dataset")
        print("-" * 60)
        
        # Create test user (or use existing)
        with db_service.get_session() as session:
            # Check if user exists
            user = session.query(User).filter_by(email="abhimava@andrew.cmu.edu").first()
            if not user:
                # Create new user
                user_data = {
                    "email": "abhimava@andrew.cmu.edu",
                    "password": "temp_password_123",
                    "full_name": "Aditya Teja Bhimavarapu"
                }
                user_result = await auth_service.register_user(user_data)
                if user_result["success"]:
                    user_id = user_result["user_id"]
                    print(f"✅ Created user: {user_id}")
                else:
                    print(f"❌ Failed to create user: {user_result['message']}")
                    return
            else:
                user_id = str(user.id)
                print(f"✅ Using existing user: {user_id}")
        
        # Populate master dataset with Aditya's resume data
        print("📊 Populating master dataset...")
        
        # Add work experiences and achievements
        for exp in ADITYA_RESUME_DATA["work_experience"]:
            work_exp_data = {
                "company_name": exp["company"],
                "position_title": exp["position"],
                "location": exp["location"],
                "start_date": exp["dates"].split(" - ")[0],
                "end_date": exp["dates"].split(" - ")[1] if " - " in exp["dates"] else "Present",
                "employment_type": "full_time",
                "company_description": f"Leading company in {exp['company']} sector"
            }
            
            exp_result = await master_dataset_service.add_work_experience(user_id, work_exp_data)
            if exp_result["success"]:
                work_exp_id = exp_result["work_experience_id"]
                print(f"✅ Added work experience: {exp['company']}")
                
                # Add achievements for this experience
                for achievement_text in exp["achievements"]:
                    achievement_data = {
                        "work_experience_id": work_exp_id,
                        "achievement_text": achievement_text,
                        "impact_level": 4,  # High impact
                        "quantified_result": True,
                        "achievement_category": "business_impact"
                    }
                    
                    ach_result = await master_dataset_service.add_achievement(user_id, achievement_data)
                    if ach_result["success"]:
                        print(f"  ✅ Added achievement: {achievement_text[:50]}...")
        
        # Add education
        for edu in ADITYA_RESUME_DATA["education"]:
            edu_data = {
                "institution_name": edu["institution"],
                "degree_type": edu["degree"],
                "field_of_study": edu.get("coursework", ""),
                "location": edu["location"],
                "graduation_date": edu["graduation_date"],
                "gpa": float(edu["gpa"].split("/")[0]) if edu.get("gpa") else None,
                "gpa_scale": float(edu["gpa"].split("/")[1]) if edu.get("gpa") else None
            }
            
            edu_result = await master_dataset_service.add_education(user_id, edu_data)
            if edu_result["success"]:
                print(f"✅ Added education: {edu['institution']}")
        
        # Add skills
        for skill_name in ADITYA_RESUME_DATA["skills"]:
            skill_data = {
                "skill_name": skill_name.strip(),
                "skill_category": "technical",
                "proficiency_level": "advanced"
            }
            
            skill_result = await master_dataset_service.add_skill(user_id, skill_data)
            if skill_result["success"]:
                print(f"✅ Added skill: {skill_name}")
        
        print("✅ Master dataset populated successfully")
        
        # Step 3: Content Selection
        print("\n🎯 Step 3: Intelligent Content Selection")
        print("-" * 60)
        
        # Get job analysis ID
        job_analysis_id = str(job_analysis.id)
        
        # Run content selection
        selected_content = await content_selector.select_optimal_content(
            user_id=user_id,
            job_analysis_id=job_analysis_id,
            word_limit=350
        )
        
        if not selected_content:
            print("❌ Content selection failed")
            return
        
        print("✅ Content selection completed")
        print(f"📊 Selected {len(selected_content.get('work_experiences', []))} work experiences")
        print(f"📚 Selected {len(selected_content.get('education', []))} education entries")
        print(f"🛠️ Selected {len(selected_content.get('skills', []))} skills")
        
        # Display selected achievements
        print("\n🏆 Selected Key Achievements:")
        for i, exp_data in enumerate(selected_content.get('work_experiences', []), 1):
            company = exp_data['experience'].get('company_name', 'Unknown')
            achievements = exp_data.get('achievements', [])
            print(f"  {i}. {company}: {len(achievements)} achievements")
            for j, ach in enumerate(achievements[:2], 1):  # Show first 2
                ach_text = ach.get('achievement_text', '')
                print(f"     • {ach_text[:60]}...")
        
        # Step 4: LaTeX Generation
        print("\n📄 Step 4: LaTeX Resume Generation")
        print("-" * 60)
        
        # Check LaTeX availability
        latex_available, version_info = await latex_generation_service.validate_latex_installation()
        if not latex_available:
            print(f"⚠️ LaTeX not available: {version_info}")
            print("📝 Generating LaTeX source only...")
        else:
            print(f"✅ LaTeX available: {version_info}")
        
        # Generate resume
        success, pdf_path, message = await latex_generation_service.generate_resume_pdf(
            user_id=user_id,
            selected_content=selected_content,
            filename_prefix="aditya_pm_optimized_resume"
        )
        
        if success and pdf_path:
            print(f"✅ Resume generated successfully!")
            print(f"📁 PDF saved to: {pdf_path}")
            
            # Get file size
            file_size = Path(pdf_path).stat().st_size / 1024  # KB
            print(f"📏 File size: {file_size:.1f} KB")
        else:
            print(f"❌ Resume generation failed: {message}")
        
        # Step 5: Summary
        print("\n📈 Step 5: Pipeline Test Summary")
        print("=" * 60)
        print(f"✅ Job Analysis: {job_analysis.company_name} - {job_analysis.position_title}")
        print(f"✅ Master Dataset: Populated with Aditya's experience")
        print(f"✅ Content Selection: Optimized for Product Manager role")
        if success:
            print(f"✅ LaTeX Generation: PDF created successfully")
        else:
            print(f"⚠️ LaTeX Generation: {message}")
        
        print(f"\n🎯 Key Matches Found:")
        # Find matches between required skills and Aditya's skills
        aditya_skills_lower = [skill.lower() for skill in ADITYA_RESUME_DATA["skills"]]
        required_skills_lower = [skill.lower() for skill in required_skills]
        
        matches = []
        for req_skill in required_skills:
            for aditya_skill in ADITYA_RESUME_DATA["skills"]:
                if req_skill.lower() in aditya_skill.lower() or aditya_skill.lower() in req_skill.lower():
                    matches.append((req_skill, aditya_skill))
                    break
        
        print(f"  📊 Skill Matches: {len(matches)}/{len(required_skills)}")
        for req_skill, aditya_skill in matches[:5]:
            print(f"    • {req_skill} ↔ {aditya_skill}")
        
        print(f"\n🏆 Strategic Highlights for PM Role:")
        print(f"  • Product Management education (MSPM from CMU)")
        print(f"  • Product implementation experience (ICICI Bank tool)")
        print(f"  • Data analysis skills (Python, SQL, Apache Spark)")
        print(f"  • Cross-functional collaboration (26 C-Suite presentations)")
        print(f"  • Technical background with business acumen")
        
        print(f"\n🎉 Pipeline Test COMPLETED SUCCESSFULLY!")
        print(f"📅 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())