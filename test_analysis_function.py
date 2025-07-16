#!/usr/bin/env python3
"""
Test script to evaluate TailerAI v2.0 analysis and content selection functions.
Tests the complete pipeline from job analysis to content selection.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.job_analysis_service import job_analyzer
from app.services.content_selection_service import content_selector
from app.services.database_service import db_service, initialize_database
from app.models.database import UserProfile, WorkExperience, Achievement, Skill, EducationEntry
from app.config.settings import get_settings

async def test_job_analysis():
    """Test job description analysis engine."""
    print("🔍 Testing Job Analysis Engine...")
    
    # Load sample job description
    job_file = Path("data/sample_data/sample_job_description.txt")
    if not job_file.exists():
        print(f"❌ Job description file not found: {job_file}")
        return None
    
    job_text = job_file.read_text()
    print(f"📄 Loaded job description: {len(job_text)} characters")
    print(f"📋 Job Preview: {job_text[:200]}...")
    
    try:
        # Analyze job description
        analysis_result = await job_analyzer.analyze_job_description(job_text)
        
        print(f"\n✅ Job Analysis Successful!")
        print(f"🏢 Company: {analysis_result.company_name}")
        print(f"💼 Position: {analysis_result.position_title}")
        print(f"🏭 Industry: {analysis_result.industry}")
        print(f"📊 Seniority: {analysis_result.seniority_level}")
        print(f"🎯 Confidence: {analysis_result.confidence_score:.2f}")
        
        print(f"\n🔧 Required Skills ({len(analysis_result.required_skills)}):")
        for skill in analysis_result.required_skills[:5]:  # Show first 5
            print(f"  • {skill}")
        if len(analysis_result.required_skills) > 5:
            print(f"  ... and {len(analysis_result.required_skills) - 5} more")
        
        print(f"\n🎯 Important Keywords ({len(analysis_result.important_keywords)}):")
        for keyword in analysis_result.important_keywords[:5]:  # Show first 5
            print(f"  • {keyword}")
        if len(analysis_result.important_keywords) > 5:
            print(f"  ... and {len(analysis_result.important_keywords) - 5} more")
        
        print(f"\n🤖 ATS Keywords ({len(analysis_result.ats_keywords)}):")
        for keyword in analysis_result.ats_keywords[:5]:
            print(f"  • {keyword}")
        
        return analysis_result
        
    except Exception as e:
        print(f"❌ Job Analysis Failed: {str(e)}")
        return None

async def check_user_data():
    """Check if we have user data to test content selection."""
    print("\n👤 Checking User Data Availability...")
    
    try:
        with db_service.get_session() as session:
            # Count users and their data
            user_count = session.query(UserProfile).count()
            work_exp_count = session.query(WorkExperience).count()
            achievement_count = session.query(Achievement).count()
            skill_count = session.query(Skill).count()
            education_count = session.query(EducationEntry).count()
            
            print(f"📊 Database Status:")
            print(f"  👥 Users: {user_count}")
            print(f"  💼 Work Experiences: {work_exp_count}")
            print(f"  🏆 Achievements: {achievement_count}")
            print(f"  🔧 Skills: {skill_count}")
            print(f"  🎓 Education: {education_count}")
            
            if user_count > 0:
                # Get first user for testing
                user_profile = session.query(UserProfile).first()
                print(f"\n✅ Found test user: {user_profile.id}")
                return str(user_profile.id)
            else:
                print("❌ No user data found for testing content selection")
                return None
                
    except Exception as e:
        print(f"❌ Database check failed: {str(e)}")
        return None

async def test_content_selection(user_profile_id, job_analysis):
    """Test content selection algorithm."""
    print(f"\n🎯 Testing Content Selection for User: {user_profile_id}")
    
    try:
        # Test algorithmic content selection
        selection_result = await content_selector.select_optimal_content(
            user_profile_id=user_profile_id,
            job_analysis=job_analysis
        )
        
        print(f"\n✅ Content Selection Successful!")
        print(f"📈 Total Score: {selection_result.total_score:.3f}")
        print(f"📝 Estimated Words: {selection_result.estimated_word_count}")
        print(f"📄 One-Page Compliant: {'✅' if selection_result.one_page_compliant else '❌'}")
        print(f"🎯 Keyword Coverage: {selection_result.keyword_coverage_percentage:.1f}%")
        print(f"🌈 Content Diversity: {selection_result.content_diversity_score:.2f}")
        
        print(f"\n🏆 Selected Achievements ({len(selection_result.selected_achievements)}):")
        for i, achievement in enumerate(selection_result.selected_achievements[:3]):
            print(f"  {i+1}. Score: {achievement.total_score:.3f} | Words: {achievement.estimated_word_count}")
            print(f"     Keywords: {', '.join(achievement.keywords_matched[:3])}")
            print(f"     Text: {achievement.content_data.get('description', '')[:100]}...")
        
        print(f"\n💼 Selected Work Experiences ({len(selection_result.selected_work_experiences)}):")
        for i, work_exp in enumerate(selection_result.selected_work_experiences):
            print(f"  {i+1}. {work_exp.content_data.get('position', '')} at {work_exp.content_data.get('company', '')}")
            print(f"     Score: {work_exp.total_score:.3f} | Duration: {work_exp.content_data.get('duration', '')}")
        
        print(f"\n🔧 Selected Skills ({len(selection_result.selected_skills)}):")
        skill_names = [skill.content_data.get('name', '') for skill in selection_result.selected_skills[:10]]
        print(f"  {', '.join(skill_names)}")
        
        print(f"\n📋 Optimization Notes:")
        for note in selection_result.optimization_notes:
            print(f"  • {note}")
        
        return selection_result
        
    except Exception as e:
        print(f"❌ Content Selection Failed: {str(e)}")
        return None

async def check_ai_settings():
    """Check AI configuration and capabilities."""
    print("\n🤖 Checking AI Configuration...")
    
    settings = get_settings()
    
    print(f"🔧 AI Settings:")
    print(f"  Gemini API Key: {'✅ Set' if settings.gemini_api_key and settings.gemini_api_key != 'your_gemini_api_key_here' else '❌ Not Set'}")
    print(f"  AI Content Selection: {'✅ Enabled' if getattr(settings, 'enable_ai_content_selection', False) else '❌ Disabled'}")
    print(f"  AI Fallback: {'✅ Enabled' if getattr(settings, 'ai_selection_fallback_enabled', True) else '❌ Disabled'}")
    print(f"  Confidence Threshold: {getattr(settings, 'ai_selection_confidence_threshold', 0.7)}")
    
    # Test Gemini client availability
    try:
        from app.services.gemini_client import GeminiClient
        gemini_client = GeminiClient()
        is_available = gemini_client.is_available()
        print(f"  Gemini Client: {'✅ Available' if is_available else '❌ Not Available'}")
        
        if is_available:
            usage_stats = gemini_client.get_usage_stats()
            print(f"  API Usage: {usage_stats.get('total_requests', 0)} requests")
            
    except Exception as e:
        print(f"  Gemini Client: ❌ Error - {str(e)}")

async def main():
    """Run complete analysis function evaluation."""
    print("🚀 TailerAI v2.0 Analysis Function Evaluation")
    print("=" * 60)
    
    # Initialize database first
    print("🗄️ Initializing database...")
    try:
        initialize_database()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return
    
    # Check AI configuration
    await check_ai_settings()
    
    # Test 1: Job Analysis
    job_analysis = await test_job_analysis()
    if not job_analysis:
        print("❌ Cannot proceed without job analysis")
        return
    
    # Test 2: Check user data
    user_profile_id = await check_user_data()
    if not user_profile_id:
        print("❌ Cannot test content selection without user data")
        return
    
    # Test 3: Content Selection
    selection_result = await test_content_selection(user_profile_id, job_analysis)
    if not selection_result:
        print("❌ Content selection test failed")
        return
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 EVALUATION SUMMARY")
    print("=" * 60)
    print("✅ Job Analysis Engine: Working")
    print("✅ Content Selection Algorithm: Working")
    print(f"📈 Selection Quality Score: {selection_result.total_score:.3f}/1.0")
    print(f"📝 Resume Optimization: {selection_result.keyword_coverage_percentage:.1f}% keyword coverage")
    print(f"📄 One-Page Compliance: {'✅ Pass' if selection_result.one_page_compliant else '❌ Fail'}")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    
    if selection_result.total_score < 0.6:
        print("  ⚠️  Consider improving content quality or job-profile match")
    
    if not selection_result.one_page_compliant:
        print("  ⚠️  Content selection exceeds one-page limit - algorithm needs tuning")
    
    if selection_result.keyword_coverage_percentage < 70:
        print("  ⚠️  Low keyword coverage - need better skill matching")
        
    settings = get_settings()
    if not getattr(settings, 'enable_ai_content_selection', False):
        print("  💡 Enable AI content selection for enhanced results")
    
    print("\n🎉 Analysis function evaluation complete!")

if __name__ == "__main__":
    asyncio.run(main())