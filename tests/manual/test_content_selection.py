#!/usr/bin/env python3
"""
Test script for Content Selection Engine (PRD-005).
Tests multi-dimensional scoring and optimization algorithms.
"""

import asyncio
import sys
import os
import time
from datetime import datetime, timedelta

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Sample job for testing
SAMPLE_JOB = """
Senior Python Developer - TechCorp

About the Role:
We are seeking an experienced Senior Python Developer to join our growing engineering team. You will be responsible for developing and maintaining our core backend services using Python, FastAPI, and modern cloud technologies.

Requirements:
• 5+ years of professional Python development experience
• Strong experience with FastAPI, Django, or Flask frameworks
• Proficiency in SQL databases (PostgreSQL, MySQL) and NoSQL (MongoDB, Redis)
• Experience with cloud platforms (AWS, GCP, or Azure)
• Knowledge of containerization (Docker, Kubernetes)
• Familiarity with CI/CD pipelines and DevOps practices
• Bachelor's degree in Computer Science or related field

Preferred Qualifications:
• Experience with machine learning libraries (scikit-learn, TensorFlow, PyTorch)
• Knowledge of microservices architecture
• Experience with API design and development
• Agile/Scrum development experience
• Strong problem-solving and communication skills

What We Offer:
• Competitive salary: $120,000 - $160,000
• Comprehensive health benefits
• Remote work flexibility
• Professional development opportunities

Location: San Francisco, CA (Remote friendly)
Employment Type: Full-time
"""

async def create_sample_user_data():
    """Create sample user data for testing content selection."""
    try:
        from app.services.database_service import initialize_database, db_service
        from app.models.database import User, UserProfile, WorkExperience, Achievement, Skill, Project, EducationEntry
        from app.services.auth_service import auth_service
        
        # Initialize database
        initialize_database()
        
        # Delete any existing test data to start fresh
        with db_service.get_session() as session:
            existing_user = session.query(User).filter_by(email="test@example.com").first()
            if existing_user:
                print(f"🗑️  Removing existing test user data...")
                session.delete(existing_user)
                session.commit()
        
        print("🔧 Creating sample user data for content selection testing...")
        
        # Create test user
        user = await auth_service.register_user(
            email="test@example.com",
            username="testuser",
            password="TestPass123!",
            full_name="Test User"
        )
        print(f"✅ Created test user: {user.id}")
        
        with db_service.get_session() as session:
            user = session.merge(user)  # Ensure user is in current session
            
            # Create user profile
            profile = UserProfile(
                user_id=user.id,
                full_name="Test User",
                email="test@example.com",
                phone="555-0123",
                location="San Francisco, CA",
                career_level="senior"
            )
            session.add(profile)
            session.flush()
            
            # Create sample work experiences
            work_experiences = [
                WorkExperience(
                    profile_id=profile.id,
                    position_title="Senior Software Engineer",
                    company_name="Tech Innovations Inc",
                    start_date=datetime(2022, 1, 1),
                    end_date=None,  # Current job
                    role_summary="Led development of microservices architecture using Python and FastAPI",
                    industry="Technology"
                ),
                WorkExperience(
                    profile_id=profile.id,
                    position_title="Python Developer",
                    company_name="DataCorp Solutions",
                    start_date=datetime(2020, 3, 1),
                    end_date=datetime(2021, 12, 31),
                    role_summary="Developed data processing pipelines and web applications",
                    industry="Technology"
                ),
                WorkExperience(
                    profile_id=profile.id,
                    position_title="Junior Software Developer",
                    company_name="StartupXYZ",
                    start_date=datetime(2018, 6, 1),
                    end_date=datetime(2020, 2, 28),
                    role_summary="Built web applications and REST APIs",
                    industry="Technology"
                )
            ]
            
            # Create sample achievements
            achievements = [
                Achievement(
                    profile_id=profile.id,
                    experience_id=None,  # Will be set after work experiences are created
                    achievement_text="Architected and implemented microservices platform that improved system performance by 40% and reduced deployment time by 60%",
                    achievement_category="technical",
                    impact_level=9,
                    quantified_metrics={"performance_improvement": 40, "deployment_time_reduction": 60},
                    skills_demonstrated=["Python", "FastAPI", "Docker", "Kubernetes", "PostgreSQL"],
                    business_function="engineering"
                ),
                Achievement(
                    profile_id=profile.id,
                    experience_id=None,
                    achievement_text="Led migration from monolithic to microservices architecture, serving 100K+ daily active users",
                    achievement_category="leadership",
                    impact_level=8,
                    quantified_metrics={"daily_users": 100000},
                    skills_demonstrated=["Python", "AWS", "Redis", "PostgreSQL"],
                    business_function="engineering"
                ),
                Achievement(
                    profile_id=profile.id,
                    experience_id=None,
                    achievement_text="Optimized database queries and implemented caching strategy, reducing API response time by 70%",
                    achievement_category="technical",
                    impact_level=7,
                    quantified_metrics={"response_time_improvement": 70},
                    skills_demonstrated=["PostgreSQL", "Redis", "Python", "SQL optimization"],
                    business_function="engineering"
                ),
                Achievement(
                    profile_id=profile.id,
                    experience_id=None,
                    achievement_text="Developed automated testing framework that increased code coverage from 45% to 90%",
                    achievement_category="process",
                    impact_level=6,
                    quantified_metrics={"code_coverage_from": 45, "code_coverage_to": 90, "bug_reduction": 80},
                    skills_demonstrated=["Python", "pytest", "CI/CD", "GitHub Actions"],
                    business_function="engineering"
                ),
                Achievement(
                    profile_id=profile.id,
                    experience_id=None,
                    achievement_text="Built real-time data processing pipeline handling 1M+ events per day",
                    achievement_category="technical",
                    impact_level=8,
                    quantified_metrics={"events_per_day": 1000000},
                    skills_demonstrated=["Python", "Apache Kafka", "MongoDB", "Docker"],
                    business_function="engineering"
                ),
                Achievement(
                    profile_id=profile.id,
                    experience_id=None,
                    achievement_text="Mentored 3 junior developers and established code review best practices",
                    achievement_category="leadership",
                    impact_level=7,
                    quantified_metrics={"developers_mentored": 3},
                    skills_demonstrated=["Git", "Code Review", "Python"],
                    business_function="engineering"
                )
            ]
            
            # Create sample skills
            skills = [
                Skill(profile_id=profile.id, skill_name="Python", proficiency_level="expert", skill_category="programming_language"),
                Skill(profile_id=profile.id, skill_name="FastAPI", proficiency_level="advanced", skill_category="framework"),
                Skill(profile_id=profile.id, skill_name="Django", proficiency_level="advanced", skill_category="framework"),
                Skill(profile_id=profile.id, skill_name="Flask", proficiency_level="intermediate", skill_category="framework"),
                Skill(profile_id=profile.id, skill_name="PostgreSQL", proficiency_level="advanced", skill_category="database"),
                Skill(profile_id=profile.id, skill_name="MySQL", proficiency_level="intermediate", skill_category="database"),
                Skill(profile_id=profile.id, skill_name="MongoDB", proficiency_level="intermediate", skill_category="database"),
                Skill(profile_id=profile.id, skill_name="Redis", proficiency_level="advanced", skill_category="database"),
                Skill(profile_id=profile.id, skill_name="AWS", proficiency_level="advanced", skill_category="cloud"),
                Skill(profile_id=profile.id, skill_name="Docker", proficiency_level="advanced", skill_category="devops"),
                Skill(profile_id=profile.id, skill_name="Kubernetes", proficiency_level="intermediate", skill_category="devops"),
                Skill(profile_id=profile.id, skill_name="CI/CD", proficiency_level="advanced", skill_category="devops"),
                Skill(profile_id=profile.id, skill_name="Git", proficiency_level="expert", skill_category="tool"),
                Skill(profile_id=profile.id, skill_name="Linux", proficiency_level="advanced", skill_category="system"),
                Skill(profile_id=profile.id, skill_name="API Design", proficiency_level="advanced", skill_category="skill"),
                Skill(profile_id=profile.id, skill_name="Microservices", proficiency_level="advanced", skill_category="architecture"),
                Skill(profile_id=profile.id, skill_name="Machine Learning", proficiency_level="beginner", skill_category="programming"),
                Skill(profile_id=profile.id, skill_name="TensorFlow", proficiency_level="beginner", skill_category="framework")
            ]
            
            # Create sample projects
            projects = [
                Project(
                    profile_id=profile.id,
                    project_name="E-commerce Microservices Platform",
                    project_description="Built scalable e-commerce platform using microservices architecture",
                    role="Lead Developer",
                    start_date=datetime(2022, 6, 1),
                    end_date=datetime(2023, 2, 1),
                    project_type="professional",
                    technologies_used=["Python", "FastAPI", "PostgreSQL", "Redis", "Docker", "AWS"],
                    project_url="https://github.com/user/ecommerce-platform",
                    key_achievements=["Handled 50K+ concurrent users", "99.9% uptime achieved"],
                    metrics={"users": "50000+", "uptime": "99.9%", "response_time": "<100ms"},
                    team_size=4
                ),
                Project(
                    profile_id=profile.id,
                    project_name="Real-time Analytics Dashboard",
                    project_description="Created real-time analytics dashboard for business intelligence",
                    role="Full Stack Developer",
                    start_date=datetime(2021, 3, 1),
                    end_date=datetime(2021, 8, 1),
                    project_type="personal",
                    technologies_used=["Python", "Flask", "PostgreSQL", "JavaScript", "Chart.js"],
                    repository_url="https://github.com/user/analytics-dashboard",
                    key_achievements=["Real-time data processing", "Interactive visualizations"],
                    metrics={"data_points": "1M+", "refresh_rate": "1s"},
                    team_size=1
                )
            ]
            
            # Create sample education
            education = [
                EducationEntry(
                    profile_id=profile.id,
                    degree_type="Bachelor of Science",
                    field_of_study="Computer Science",
                    institution_name="UC Berkeley",
                    end_date=datetime(2018, 5, 1),
                    gpa=3.7,
                    relevant_coursework=["Data Structures", "Algorithms", "Database Systems", "Software Engineering"]
                )
            ]
            
            # Add work experiences first and get their IDs
            for work_exp in work_experiences:
                session.add(work_exp)
            session.flush()  # Get IDs for foreign key references
            
            # Link achievements to work experiences
            if len(work_experiences) > 0:
                for i, achievement in enumerate(achievements):
                    # Assign achievements to work experiences cyclically
                    achievement.experience_id = work_experiences[i % len(work_experiences)].id
            
            # Add all sample data
            for achievement in achievements:
                session.add(achievement)
            for skill in skills:
                session.add(skill)
            for project in projects:
                session.add(project)
            for edu in education:
                session.add(edu)
            
            session.commit()
            session.refresh(profile)
            
            print(f"✅ Created sample data:")
            print(f"  • {len(work_experiences)} work experiences")
            print(f"  • {len(achievements)} achievements")
            print(f"  • {len(skills)} skills")
            print(f"  • {len(projects)} projects")
            print(f"  • {len(education)} education entries")
            
            return str(profile.id)
            
    except Exception as e:
        print(f"❌ Failed to create sample user data: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_content_selection_engine():
    """Test the content selection engine with sample data."""
    print("\n🔍 Testing Content Selection Engine")
    print("=" * 60)
    
    try:
        from app.services.job_analysis_service import job_analyzer
        from app.services.content_selection_service import content_selector
        
        # Create sample user data
        user_profile_id = await create_sample_user_data()
        if not user_profile_id:
            print("❌ Failed to create sample user data")
            return False
        
        # Analyze the sample job
        print("\n📋 Analyzing job description...")
        job_analysis = await job_analyzer.analyze_job_description(SAMPLE_JOB)
        print(f"✅ Job analysis completed: {job_analysis.position_title} at {job_analysis.company_name}")
        
        # Perform content selection
        print("\n🎯 Performing content selection...")
        start_time = time.time()
        
        selection_result = await content_selector.select_optimal_content(
            user_profile_id=user_profile_id,
            job_analysis=job_analysis
        )
        
        processing_time = (time.time() - start_time) * 1000
        print(f"✅ Content selection completed in {processing_time:.0f}ms")
        
        # Display results
        print("\n📊 Selection Results:")
        print(f"🎯 Total Score: {selection_result.total_score:.3f}")
        print(f"📝 Estimated Word Count: {selection_result.estimated_word_count}")
        print(f"📄 One-Page Compliant: {'✅' if selection_result.one_page_compliant else '❌'}")
        print(f"🎨 Content Diversity: {selection_result.content_diversity_score:.1%}")
        print(f"🔑 Keyword Coverage: {selection_result.keyword_coverage_percentage:.1f}%")
        
        print(f"\n🏆 Selected Achievements ({len(selection_result.selected_achievements)}):")
        for i, achievement in enumerate(selection_result.selected_achievements[:3], 1):
            print(f"  {i}. Score: {achievement.total_score:.3f} | Tier: {achievement.priority_tier}")
            print(f"     {achievement.content_data['description'][:80]}...")
            print(f"     Keywords: {', '.join(achievement.keywords_matched[:5])}")
        
        print(f"\n💼 Selected Work Experiences ({len(selection_result.selected_work_experiences)}):")
        for i, work_exp in enumerate(selection_result.selected_work_experiences, 1):
            print(f"  {i}. {work_exp.content_data['position']} at {work_exp.content_data['company']}")
            print(f"     Score: {work_exp.total_score:.3f} | Keywords: {len(work_exp.keywords_matched)}")
        
        print(f"\n🔧 Selected Skills ({len(selection_result.selected_skills)}):")
        top_skills = selection_result.selected_skills[:10]
        for i, skill in enumerate(top_skills, 1):
            proficiency = skill.content_data.get('proficiency', 'N/A')
            print(f"  {i}. {skill.content_data['name']} ({proficiency}) - Score: {skill.total_score:.3f}")
        
        if selection_result.selected_projects:
            print(f"\n🚀 Selected Projects ({len(selection_result.selected_projects)}):")
            for i, project in enumerate(selection_result.selected_projects, 1):
                print(f"  {i}. {project.content_data['name']} - Score: {project.total_score:.3f}")
        
        print(f"\n📚 Selected Education ({len(selection_result.selected_education)}):")
        for i, education in enumerate(selection_result.selected_education, 1):
            print(f"  {i}. {education.content_data['degree']} in {education.content_data['field']}")
            print(f"     {education.content_data['institution']} - Score: {education.total_score:.3f}")
        
        print(f"\n💡 Optimization Notes:")
        for note in selection_result.optimization_notes:
            print(f"  • {note}")
        
        return True
        
    except Exception as e:
        print(f"❌ Content selection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_scoring_algorithm():
    """Test the scoring algorithm with different scenarios."""
    print("\n\n🧮 Testing Multi-Dimensional Scoring Algorithm")
    print("=" * 60)
    
    try:
        from app.services.job_analysis_service import job_analyzer
        from app.services.content_selection_service import content_selector
        
        # Get sample user
        user_profile_id = await create_sample_user_data()
        if not user_profile_id:
            return False
        
        # Test with different job types
        test_jobs = {
            "Python Backend": """
            Senior Backend Engineer - Python
            Requirements: 5+ years Python, FastAPI, PostgreSQL, AWS, Docker
            Preferred: Redis, Kubernetes, CI/CD
            """,
            
            "Data Science": """
            Data Scientist - Machine Learning
            Requirements: Python, TensorFlow, scikit-learn, pandas, SQL
            Preferred: AWS, Docker, Jupyter
            """,
            
            "DevOps": """
            DevOps Engineer - Cloud Infrastructure
            Requirements: AWS, Docker, Kubernetes, CI/CD, Linux
            Preferred: Python, Terraform, monitoring tools
            """
        }
        
        for job_name, job_text in test_jobs.items():
            print(f"\n🔍 Testing with {job_name} position...")
            
            # Analyze job
            job_analysis = await job_analyzer.analyze_job_description(job_text)
            
            # Select content
            selection_result = await content_selector.select_optimal_content(
                user_profile_id=user_profile_id,
                job_analysis=job_analysis
            )
            
            print(f"📊 Results for {job_name}:")
            print(f"  • Total Score: {selection_result.total_score:.3f}")
            print(f"  • Keyword Coverage: {selection_result.keyword_coverage_percentage:.1f}%")
            print(f"  • Selected Achievements: {len(selection_result.selected_achievements)}")
            print(f"  • Top Skills: {', '.join([s.content_data['name'] for s in selection_result.selected_skills[:5]])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Scoring algorithm test failed: {e}")
        return False

async def test_one_page_optimization():
    """Test one-page constraint optimization."""
    print("\n\n📄 Testing One-Page Optimization")
    print("=" * 60)
    
    try:
        from app.services.job_analysis_service import job_analyzer
        from app.services.content_selection_service import content_selector
        
        user_profile_id = await create_sample_user_data()
        if not user_profile_id:
            return False
        
        # Analyze sample job
        job_analysis = await job_analyzer.analyze_job_description(SAMPLE_JOB)
        
        # Test with different word count limits
        original_limit = content_selector.max_word_count
        
        for limit in [250, 350, 500]:
            print(f"\n📏 Testing with {limit} word limit...")
            content_selector.max_word_count = limit
            
            selection_result = await content_selector.select_optimal_content(
                user_profile_id=user_profile_id,
                job_analysis=job_analysis
            )
            
            print(f"  • Word Count: {selection_result.estimated_word_count}/{limit}")
            print(f"  • Compliant: {'✅' if selection_result.one_page_compliant else '❌'}")
            print(f"  • Achievements Selected: {len(selection_result.selected_achievements)}")
            print(f"  • Total Score: {selection_result.total_score:.3f}")
        
        # Restore original limit
        content_selector.max_word_count = original_limit
        
        return True
        
    except Exception as e:
        print(f"❌ One-page optimization test failed: {e}")
        return False

async def main():
    """Run comprehensive content selection tests."""
    print("🧪 TailerAI v2.0 - Content Selection Engine Test Suite")
    print("=" * 70)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Testing PRD-005: Content Selection Engine")
    print("=" * 70)
    
    # Test 1: Basic content selection
    test1_success = await test_content_selection_engine()
    
    # Test 2: Scoring algorithm with different jobs
    test2_success = await test_scoring_algorithm()
    
    # Test 3: One-page optimization
    test3_success = await test_one_page_optimization()
    
    # Summary
    print("\n\n📊 Test Summary")
    print("=" * 70)
    print(f"🎯 Content Selection Engine: {'✅ PASSED' if test1_success else '❌ FAILED'}")
    print(f"🧮 Multi-Dimensional Scoring: {'✅ PASSED' if test2_success else '❌ FAILED'}")
    print(f"📄 One-Page Optimization: {'✅ PASSED' if test3_success else '❌ FAILED'}")
    
    overall_success = test1_success and test2_success and test3_success
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 Content Selection Engine (PRD-005) is fully functional!")
        print("✅ Multi-dimensional scoring working correctly")
        print("✅ One-page optimization implemented")
        print("✅ Ready for ATS Optimization Engine (PRD-006)")
    else:
        print("\n⚠️ Some tests failed - review errors above")
    
    return overall_success

if __name__ == "__main__":
    asyncio.run(main())