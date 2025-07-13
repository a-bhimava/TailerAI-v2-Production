#!/usr/bin/env python3
"""
Debug script for Gemini API integration.
Tests the direct Gemini API call to identify issues.
"""

import asyncio
import sys
import os
import json

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_direct_gemini():
    """Test direct Gemini API call."""
    print("🔍 Testing Direct Gemini API Integration")
    print("=" * 50)
    
    try:
        # Import and configure
        import google.generativeai as genai
        from app.config.settings import get_settings
        
        settings = get_settings()
        
        print(f"✅ API Key configured: {bool(settings.gemini_api_key)}")
        print(f"🔑 Key length: {len(settings.gemini_api_key)}")
        
        # Configure Gemini
        genai.configure(api_key=settings.gemini_api_key)
        
        # Create model
        model = genai.GenerativeModel("gemini-1.5-pro")
        print("✅ Model created successfully")
        
        # Simple test prompt
        simple_prompt = """
Analyze this job posting and return JSON:

Job: Senior Python Developer at TechCorp

Return this exact format:
{
    "company_name": "TechCorp",
    "position_title": "Senior Python Developer",
    "industry": "Technology",
    "seniority_level": "senior",
    "required_skills": ["Python", "FastAPI"],
    "confidence_score": 0.95
}
"""
        
        print("🚀 Making API call...")
        
        try:
            # Try with JSON response type
            generation_config = genai.types.GenerationConfig(
                temperature=0.1,
                top_p=0.8,
                top_k=40,
                max_output_tokens=1000,
                response_mime_type="application/json"
            )
            
            response = await asyncio.to_thread(
                model.generate_content,
                simple_prompt,
                generation_config=generation_config
            )
            
            print("✅ API call successful")
            print(f"📝 Response text length: {len(response.text)}")
            print(f"📝 Response text: {response.text}")
            
            # Try to parse JSON
            try:
                data = json.loads(response.text)
                print("✅ JSON parsing successful")
                print(f"🏢 Company: {data.get('company_name')}")
                print(f"💼 Position: {data.get('position_title')}")
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing failed: {e}")
                print(f"Raw response: '{response.text}'")
                
        except Exception as e:
            print(f"❌ API call with JSON config failed: {e}")
            
            # Try without JSON config
            print("\n🔄 Trying without JSON config...")
            response = await asyncio.to_thread(
                model.generate_content,
                simple_prompt
            )
            
            print("✅ API call successful (no JSON config)")
            print(f"📝 Response text: {response.text}")
            
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Run: pip install google-generativeai")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_job_analyzer_client():
    """Test the GeminiClient from our job analyzer."""
    print("\n\n🔧 Testing Our GeminiClient")
    print("=" * 50)
    
    try:
        from app.services.gemini_client import GeminiClient
        
        client = GeminiClient()
        print("✅ GeminiClient created")
        print(f"🔧 Model name: {client.model_name}")
        print(f"🔌 Available: {client.is_available()}")
        
        # Get usage stats
        stats = client.get_usage_stats()
        print(f"📊 Daily calls used: {stats['daily_calls_used']}/{stats['daily_limit']}")
        print(f"🚦 Can make request: {stats['can_make_request']}")
        
        return True
        
    except Exception as e:
        print(f"❌ GeminiClient test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_simple_job_analysis():
    """Test simplified job analysis without complex prompt."""
    print("\n\n🎯 Testing Simple Job Analysis")
    print("=" * 50)
    
    try:
        from app.services.database_service import initialize_database
        
        # Initialize database
        initialize_database()
        print("✅ Database initialized")
        
        # Simple direct Gemini test
        import google.generativeai as genai
        from app.config.settings import get_settings
        
        settings = get_settings()
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-pro")
        
        simple_job_prompt = """
Please analyze this job posting and return a JSON response:

"Senior Python Developer needed. 5+ years experience. Python, FastAPI, AWS required."

Return only this JSON format:
{
    "company_name": "Unknown",
    "position_title": "Senior Python Developer", 
    "industry": "Technology",
    "seniority_level": "senior",
    "required_skills": ["Python", "FastAPI", "AWS"],
    "preferred_skills": [],
    "important_keywords": ["Python", "FastAPI", "AWS", "5+ years"],
    "confidence_score": 0.8
}
"""
        
        response = await asyncio.to_thread(
            model.generate_content,
            simple_job_prompt
        )
        
        print(f"✅ Simple analysis response: {response.text}")
        
        # Try to parse
        try:
            data = json.loads(response.text)
            print("✅ JSON parsing successful")
            return True
        except:
            print("❌ JSON parsing failed, but got response")
            return False
            
    except Exception as e:
        print(f"❌ Simple analysis failed: {e}")
        return False

async def main():
    """Run all debug tests."""
    print("🐛 Gemini API Debug Suite")
    print("=" * 60)
    
    test1 = await test_direct_gemini()
    test2 = await test_job_analyzer_client()
    test3 = await test_simple_job_analysis()
    
    print("\n\n📊 Debug Summary")
    print("=" * 60)
    print(f"🔍 Direct Gemini API: {'✅ PASSED' if test1 else '❌ FAILED'}")
    print(f"🔧 GeminiClient: {'✅ PASSED' if test2 else '❌ FAILED'}")
    print(f"🎯 Simple Analysis: {'✅ PASSED' if test3 else '❌ FAILED'}")
    
    if all([test1, test2, test3]):
        print("\n🎉 All debug tests passed! The issue might be in the complex prompt.")
    else:
        print("\n❌ Some debug tests failed. Check configuration and dependencies.")

if __name__ == "__main__":
    asyncio.run(main())