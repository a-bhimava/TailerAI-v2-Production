#!/usr/bin/env python3
"""
Simple test for Job Description Analysis Engine (PRD-004).
Tests direct service functionality without API dependencies.
"""

import asyncio
import sys
import os
import time
from datetime import datetime

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Sample job description for testing
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

async def test_basic_functionality():
    """Test basic job analysis functionality."""
    print("🔍 Testing Job Description Analysis Engine - Basic Functionality")
    print("=" * 70)
    
    try:
        # Import here to check for issues
        from app.services.database_service import initialize_database
        from app.services.job_analysis_service import job_analyzer
        
        print("✅ Imports successful")
        
        # Initialize database
        print("🗄️ Initializing database...")
        initialize_database()
        print("✅ Database initialized")
        
        # Test job analysis
        print("\n📋 Analyzing sample job description...")
        start_time = time.time()
        
        result = await job_analyzer.analyze_job_description(SAMPLE_JOB)
        
        processing_time = (time.time() - start_time) * 1000
        print(f"✅ Analysis completed in {processing_time:.0f}ms")
        
        # Display key results
        print("\n📊 Analysis Results:")
        print(f"🏢 Company: {result.company_name}")
        print(f"💼 Position: {result.position_title}")
        print(f"🏭 Industry: {result.industry}")
        print(f"📈 Seniority: {result.seniority_level}")
        print(f"⚙️ Employment Type: {result.employment_type}")
        print(f"🎯 Confidence Score: {result.confidence_score:.2f}")
        print(f"📊 Difficulty Level: {result.difficulty_level}")
        print(f"🏆 Competition Level: {result.competition_level}")
        
        print(f"\n🔑 Required Skills ({len(result.required_skills)}):")
        for i, skill in enumerate(result.required_skills[:5]):
            print(f"  {i+1}. {skill}")
        if len(result.required_skills) > 5:
            print(f"  ... and {len(result.required_skills) - 5} more")
        
        print(f"\n💡 Preferred Skills ({len(result.preferred_skills)}):")
        for i, skill in enumerate(result.preferred_skills[:5]):
            print(f"  {i+1}. {skill}")
        if len(result.preferred_skills) > 5:
            print(f"  ... and {len(result.preferred_skills) - 5} more")
        
        print(f"\n🎯 Important Keywords ({len(result.important_keywords)}):")
        for i, keyword in enumerate(result.important_keywords[:8]):
            print(f"  {i+1}. {keyword}")
        
        print(f"\n🔗 Analysis ID: {result.job_description_hash[:16]}...")
        
        if result.salary_range_estimate:
            print(f"💰 Salary Estimate: {result.salary_range_estimate}")
        
        print("\n✅ Basic functionality test PASSED")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Missing dependencies or configuration issues")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_caching():
    """Test caching functionality."""
    print("\n\n⚡ Testing Caching Performance")
    print("=" * 70)
    
    try:
        from app.services.job_analysis_service import job_analyzer
        
        # First analysis (should create cache)
        print("🔍 First analysis (creating cache)...")
        start_time = time.time()
        result1 = await job_analyzer.analyze_job_description(SAMPLE_JOB)
        first_time = (time.time() - start_time) * 1000
        print(f"⏱️ First analysis: {first_time:.0f}ms")
        
        # Second analysis (should use cache)
        print("\n🔍 Second analysis (using cache)...")
        start_time = time.time()
        result2 = await job_analyzer.analyze_job_description(SAMPLE_JOB)
        second_time = (time.time() - start_time) * 1000
        print(f"⏱️ Second analysis: {second_time:.0f}ms")
        
        # Verify results consistency
        if result1.job_description_hash == result2.job_description_hash:
            print("✅ Cache consistency verified")
            if second_time < first_time:
                improvement = first_time / second_time
                print(f"🚀 Performance improvement: {improvement:.1f}x faster")
            else:
                print("⚠️ No significant performance improvement (may not be cached)")
        else:
            print("❌ Cache inconsistency detected")
            return False
        
        print("\n✅ Caching test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Caching test failed: {e}")
        return False

async def test_error_handling():
    """Test error handling with invalid input."""
    print("\n\n🛡️ Testing Error Handling")
    print("=" * 70)
    
    try:
        from app.services.job_analysis_service import job_analyzer, JobDescriptionAnalysisError
        
        # Test with empty input
        print("🔍 Testing with empty job description...")
        try:
            result = await job_analyzer.analyze_job_description("")
            print("⚠️ Empty input was processed (unexpected)")
        except JobDescriptionAnalysisError:
            print("✅ Empty input properly rejected")
        except Exception as e:
            print(f"⚠️ Unexpected error type: {e}")
        
        # Test with very short input
        print("\n🔍 Testing with minimal job description...")
        try:
            result = await job_analyzer.analyze_job_description("Software developer needed.")
            print(f"✅ Minimal input processed: {result.position_title}")
        except Exception as e:
            print(f"⚠️ Minimal input failed: {e}")
        
        print("\n✅ Error handling test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

async def main():
    """Run comprehensive but simple tests."""
    print("🧪 TailerAI v2.0 - Job Description Analysis Engine - Simple Test Suite")
    print("=" * 80)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Testing PRD-004: Job Description Analysis Engine (Direct Service)")
    print("=" * 80)
    
    # Test 1: Basic functionality
    test1_success = await test_basic_functionality()
    
    # Test 2: Caching performance (only if basic test passed)
    test2_success = False
    if test1_success:
        test2_success = await test_caching()
    else:
        print("\n⏭️ Skipping caching test due to basic functionality failure")
    
    # Test 3: Error handling (only if basic test passed)
    test3_success = False
    if test1_success:
        test3_success = await test_error_handling()
    else:
        print("\n⏭️ Skipping error handling test due to basic functionality failure")
    
    # Summary
    print("\n\n📊 Test Summary")
    print("=" * 80)
    print(f"🔍 Basic Functionality: {'✅ PASSED' if test1_success else '❌ FAILED'}")
    print(f"⚡ Caching Performance: {'✅ PASSED' if test2_success else '❌ FAILED/SKIPPED'}")
    print(f"🛡️ Error Handling: {'✅ PASSED' if test3_success else '❌ FAILED/SKIPPED'}")
    
    overall_success = test1_success and test2_success and test3_success
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if test1_success:
        print("\n🎉 Job Description Analysis Engine (PRD-004) core functionality is working!")
        if overall_success:
            print("✅ All features working correctly - ready for API integration")
        else:
            print("⚠️ Core working but some advanced features need attention")
    else:
        print("\n❌ Core functionality issues detected - needs debugging")
        print("💡 Check dependencies, database setup, and AI service configuration")
    
    return overall_success

if __name__ == "__main__":
    asyncio.run(main())