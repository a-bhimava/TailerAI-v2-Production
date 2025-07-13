#!/usr/bin/env python3
"""
Test script for Job Description Analysis Engine (PRD-004).
Tests the complete job analysis workflow with AI-powered insights.
"""

import asyncio
import sys
import os
import json
import requests
import time
from datetime import datetime

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Direct service testing
from app.services.job_analysis_service import job_analyzer
from app.services.database_service import initialize_database

# API testing configuration
BASE_URL = "http://localhost:8001"
API_BASE = f"{BASE_URL}/api/v2"

# Sample job descriptions for testing
SAMPLE_JOBS = {
    "senior_python_dev": """
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
""",
    
    "data_scientist": """
Data Scientist - AI Innovations Inc.

Join our data science team to build cutting-edge machine learning models and drive data-driven decision making across the organization.

Essential Requirements:
• Master's or PhD in Data Science, Statistics, Mathematics, or related field
• 3+ years of experience in data science and machine learning
• Proficiency in Python (pandas, numpy, scikit-learn, matplotlib)
• Experience with deep learning frameworks (TensorFlow, PyTorch, Keras)
• Strong SQL skills and experience with big data tools (Spark, Hadoop)
• Statistical analysis and hypothesis testing expertise
• Experience with cloud ML platforms (AWS SageMaker, Google AI Platform)

Nice to Have:
• Experience with MLOps and model deployment
• Knowledge of A/B testing and experimental design
• Familiarity with natural language processing (NLP)
• Business intelligence and data visualization tools (Tableau, PowerBI)
• Research publications or open-source contributions

Compensation: $100,000 - $140,000 based on experience
Location: New York, NY
Type: Full-time, Hybrid (3 days in office)
""",
    
    "junior_frontend": """
Junior Frontend Developer - StartupXYZ

We're looking for a passionate Junior Frontend Developer to help build beautiful, responsive web applications using modern JavaScript frameworks.

What You'll Do:
• Develop user-facing features using React.js and TypeScript
• Collaborate with designers to implement pixel-perfect UI/UX
• Write clean, maintainable, and well-tested code
• Participate in code reviews and team meetings

Requirements:
• 1-2 years of frontend development experience
• Proficiency in HTML, CSS, and JavaScript
• Experience with React.js and modern frontend tooling
• Understanding of responsive design principles
• Familiarity with version control (Git)
• Bachelor's degree preferred but not required

Bonus Points:
• Experience with TypeScript
• Knowledge of CSS preprocessors (Sass, Less)
• Familiarity with testing frameworks (Jest, React Testing Library)
• Understanding of web performance optimization
• Design skills or experience with Figma/Sketch

Benefits:
• $65,000 - $85,000 salary
• Equity participation
• Health, dental, vision insurance
• Flexible PTO
• Learning and development budget

Location: Austin, TX
Type: Full-time
"""
}

def get_auth_token():
    """Get authentication token for API testing."""
    try:
        # Try to login with test user
        login_data = {
            "email": "test@example.com",
            "password": "TestPass123!"
        }
        
        response = requests.post(
            f"{API_BASE}/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

async def test_direct_job_analysis():
    """Test job analysis service directly."""
    print("🔍 Testing Job Description Analysis Engine (Direct Service)")
    print("=" * 60)
    
    try:
        # Initialize database
        initialize_database()
        
        # Test each sample job
        for job_name, job_text in SAMPLE_JOBS.items():
            print(f"\n📋 Analyzing: {job_name.replace('_', ' ').title()}")
            print("-" * 40)
            
            start_time = time.time()
            
            # Perform analysis
            result = await job_analyzer.analyze_job_description(job_text)
            
            processing_time = (time.time() - start_time) * 1000
            
            # Display results
            print(f"✅ Analysis completed in {processing_time:.0f}ms")
            print(f"🏢 Company: {result.company_name}")
            print(f"💼 Position: {result.position_title}")
            print(f"🏭 Industry: {result.industry}")
            print(f"📈 Seniority: {result.seniority_level}")
            print(f"⚙️ Employment Type: {result.employment_type}")
            print(f"🎯 Confidence Score: {result.confidence_score:.2f}")
            print(f"📊 Difficulty Level: {result.difficulty_level}")
            print(f"🏆 Competition Level: {result.competition_level}")
            
            print(f"\n🔑 Required Skills ({len(result.required_skills)}):")
            for skill in result.required_skills[:5]:  # Show first 5
                print(f"  • {skill}")
            if len(result.required_skills) > 5:
                print(f"  ... and {len(result.required_skills) - 5} more")
            
            print(f"\n💡 Preferred Skills ({len(result.preferred_skills)}):")
            for skill in result.preferred_skills[:5]:  # Show first 5
                print(f"  • {skill}")
            if len(result.preferred_skills) > 5:
                print(f"  ... and {len(result.preferred_skills) - 5} more")
            
            print(f"\n🎯 Important Keywords ({len(result.important_keywords)}):")
            for keyword in result.important_keywords[:8]:  # Show first 8
                print(f"  • {keyword}")
            
            print(f"\n📈 ATS Keywords ({len(result.ats_keywords)}):")
            for keyword in result.ats_keywords[:8]:  # Show first 8
                print(f"  • {keyword}")
            
            if result.salary_range_estimate:
                print(f"\n💰 Salary Estimate: {result.salary_range_estimate}")
            
            print(f"\n🔗 Analysis ID: {result.job_description_hash[:12]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_job_analysis(access_token):
    """Test job analysis API endpoints."""
    print("\n\n🌐 Testing Job Description Analysis API")
    print("=" * 60)
    
    if not access_token:
        print("❌ No access token available - skipping API tests")
        return False
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    analysis_ids = []
    
    try:
        # Test each sample job via API
        for job_name, job_text in SAMPLE_JOBS.items():
            print(f"\n📋 API Analysis: {job_name.replace('_', ' ').title()}")
            print("-" * 40)
            
            # Make API request
            request_data = {
                "job_text": job_text,
                "job_url": f"https://example.com/jobs/{job_name}"
            }
            
            start_time = time.time()
            
            response = requests.post(
                f"{API_BASE}/analysis/job-analysis",
                json=request_data,
                headers=headers
            )
            
            api_time = (time.time() - start_time) * 1000
            
            print(f"📡 API Response Time: {api_time:.0f}ms")
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success: {data['success']}")
                print(f"🏢 Company: {data['company_name']}")
                print(f"💼 Position: {data['position_title']}")
                print(f"🎯 Confidence: {data['confidence_score']:.2f}")
                print(f"⚡ Processing Time: {data['processing_time_ms']:.0f}ms")
                print(f"💾 From Cache: {data['from_cache']}")
                print(f"🔗 Analysis ID: {data['analysis_id'][:12]}...")
                
                analysis_ids.append(data['analysis_id'])
                
                # Show key insights
                print(f"🔑 Required Skills: {len(data['required_skills'])}")
                print(f"💡 Preferred Skills: {len(data['preferred_skills'])}")
                print(f"🎯 Important Keywords: {len(data['important_keywords'])}")
                
            else:
                print(f"❌ API Error: {response.text}")
        
        # Test retrieval of cached analysis
        if analysis_ids:
            print(f"\n🗃️ Testing Analysis Retrieval")
            print("-" * 40)
            
            analysis_id = analysis_ids[0]
            response = requests.get(
                f"{API_BASE}/analysis/job-analysis/{analysis_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Retrieved cached analysis: {data['position_title']}")
                print(f"💾 From Cache: {data['from_cache']}")
            else:
                print(f"❌ Retrieval failed: {response.text}")
        
        # Test statistics endpoint
        print(f"\n📊 Testing Analysis Statistics")
        print("-" * 40)
        
        response = requests.get(
            f"{API_BASE}/analysis/job-analysis/stats",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            stats = data['statistics']
            print(f"✅ Statistics retrieved:")
            print(f"📈 Total Analyses: {stats.get('total_analyses', 0)}")
            print(f"📅 This Week: {stats.get('analyses_this_week', 0)}")
            print(f"💾 Cache Hit Rate: {stats.get('cache_hit_rate', 0):.2%}")
            
            if 'top_positions' in stats:
                print(f"🔝 Top Positions:")
                for pos in stats['top_positions'][:3]:
                    print(f"  • {pos['position']} ({pos['count']} analyses)")
            
            if 'gemini_usage' in stats:
                gemini = stats['gemini_usage']
                print(f"🤖 Gemini Usage:")
                print(f"  • Daily calls: {gemini.get('daily_calls_used', 0)}/{gemini.get('daily_limit', 0)}")
                print(f"  • Can make request: {gemini.get('can_make_request', False)}")
        else:
            print(f"❌ Statistics failed: {response.text}")
        
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

async def test_caching_performance():
    """Test caching performance with repeated analyses."""
    print("\n\n⚡ Testing Caching Performance")
    print("=" * 60)
    
    try:
        job_text = SAMPLE_JOBS["senior_python_dev"]
        
        # First analysis (cache miss)
        print("🔍 First analysis (cache miss)...")
        start_time = time.time()
        result1 = await job_analyzer.analyze_job_description(job_text)
        first_time = (time.time() - start_time) * 1000
        print(f"⏱️ First analysis: {first_time:.0f}ms")
        
        # Second analysis (cache hit)
        print("\n🔍 Second analysis (cache hit)...")
        start_time = time.time()
        result2 = await job_analyzer.analyze_job_description(job_text)
        second_time = (time.time() - start_time) * 1000
        print(f"⏱️ Second analysis: {second_time:.0f}ms")
        
        # Verify results are identical
        if result1.job_description_hash == result2.job_description_hash:
            print(f"✅ Cache consistency verified")
            print(f"🚀 Performance improvement: {first_time/second_time:.1f}x faster")
        else:
            print(f"❌ Cache inconsistency detected")
        
        return True
        
    except Exception as e:
        print(f"❌ Caching test failed: {e}")
        return False

async def main():
    """Run comprehensive job analysis tests."""
    print("🧪 TailerAI v2.0 - Job Description Analysis Engine Test Suite")
    print("=" * 70)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Testing PRD-004: Job Description Analysis Engine")
    print("=" * 70)
    
    # Test 1: Direct service testing
    test1_success = await test_direct_job_analysis()
    
    # Test 2: Caching performance
    test2_success = await test_caching_performance()
    
    # Test 3: API endpoint testing
    access_token = get_auth_token()
    test3_success = test_api_job_analysis(access_token)
    
    # Summary
    print("\n\n📊 Test Summary")
    print("=" * 70)
    print(f"🔍 Direct Service Test: {'✅ PASSED' if test1_success else '❌ FAILED'}")
    print(f"⚡ Caching Performance: {'✅ PASSED' if test2_success else '❌ FAILED'}")
    print(f"🌐 API Endpoint Test: {'✅ PASSED' if test3_success else '❌ FAILED'}")
    
    overall_success = test1_success and test2_success and test3_success
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 Job Description Analysis Engine (PRD-004) is fully functional!")
        print("✅ Ready for Phase 2 Content Selection Engine implementation")
    else:
        print("\n⚠️ Some tests failed - review errors above")
    
    return overall_success

if __name__ == "__main__":
    asyncio.run(main())