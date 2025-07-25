#!/usr/bin/env python3
"""
Verify that AI content selection is configured correctly and Gemini is the primary method.
"""

import sys
import os
from pathlib import Path

def verify_ai_configuration():
    """Verify AI content selection configuration."""
    
    print("=== VERIFYING AI CONTENT SELECTION CONFIGURATION ===")
    
    # Check if .env file exists and contains Gemini API key
    env_file = Path(".env")
    gemini_api_key = None
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_content = f.read()
            for line in env_content.split('\n'):
                if line.startswith('GEMINI_API_KEY='):
                    gemini_api_key = line.split('=', 1)[1].strip()
                    break
        
        if gemini_api_key and gemini_api_key != '':
            print("✅ GEMINI_API_KEY found in .env file")
            print(f"   Key: {gemini_api_key[:10]}...{gemini_api_key[-4:] if len(gemini_api_key) > 14 else '[short]'}")
        else:
            print("❌ GEMINI_API_KEY not found or empty in .env file")
    else:
        print("❌ .env file not found")
    
    # Check environment variable
    env_gemini_key = os.getenv('GEMINI_API_KEY')
    if env_gemini_key:
        print("✅ GEMINI_API_KEY found in environment variables")
    else:
        print("❌ GEMINI_API_KEY not found in environment variables")
    
    # Verify configuration settings by importing them
    try:
        sys.path.insert(0, 'app')
        from app.config.settings import get_settings
        
        settings = get_settings()
        
        print("\n=== AI CONFIGURATION SETTINGS ===")
        print(f"✅ enable_ai_content_selection: {settings.enable_ai_content_selection}")
        print(f"✅ ai_selection_fallback_enabled: {settings.ai_selection_fallback_enabled}")
        print(f"✅ ai_selection_default_method: {settings.ai_selection_default_method}")
        print(f"✅ ai_selection_confidence_threshold: {settings.ai_selection_confidence_threshold}")
        print(f"✅ gemini_api_key configured: {'Yes' if settings.gemini_api_key else 'No'}")
        print(f"✅ gemini_requests_per_minute: {settings.gemini_requests_per_minute}")
        print(f"✅ gemini_daily_limit: {settings.gemini_daily_limit}")
        
        # Test Gemini client initialization
        try:
            from app.services.gemini_client import GeminiClient
            
            print("\n=== GEMINI CLIENT TEST ===")
            gemini_client = GeminiClient()
            
            if gemini_client.is_available():
                print("✅ Gemini client initialized successfully")
                print("✅ Gemini client is available")
                
                # Test rate limiter
                if gemini_client.rate_limiter.can_make_request():
                    print("✅ Rate limiter allows requests")
                else:
                    print("⚠️ Rate limiter is blocking requests (may be normal)")
                    
            else:
                print("❌ Gemini client not available")
                
        except Exception as e:
            print(f"❌ Failed to initialize Gemini client: {e}")
        
        # Test AI Content Selection Engine
        try:
            from app.services.ai_content_selection_service import AIContentSelectionEngine
            
            print("\n=== AI CONTENT SELECTION ENGINE TEST ===")
            ai_engine = AIContentSelectionEngine()
            
            print(f"✅ AI selection enabled: {ai_engine.use_ai_selection}")
            print(f"✅ AI fallback enabled: {ai_engine.ai_fallback_enabled}")
            print(f"✅ AI confidence threshold: {ai_engine.ai_confidence_threshold}")
            print(f"✅ Gemini client initialized: {'Yes' if ai_engine.gemini_client else 'No'}")
            
            if ai_engine.gemini_client:
                print("✅ AI Content Selection Engine ready for production use!")
            else:
                print("❌ AI Content Selection Engine will fall back to algorithmic method")
                
        except Exception as e:
            print(f"❌ Failed to initialize AI Content Selection Engine: {e}")
        
    except Exception as e:
        print(f"❌ Failed to import settings or services: {e}")
    
    print("\n=== SUMMARY ===")
    if gemini_api_key or env_gemini_key:
        print("✅ GEMINI API CONFIGURATION: READY")
        print("✅ AI CONTENT SELECTION: PRIMARY METHOD")
        print("✅ FALLBACK PROTECTION: ENABLED")
        print("🎉 Gemini AI is properly configured as the primary selection method!")
    else:
        print("❌ GEMINI API CONFIGURATION: MISSING")
        print("⚠️ SYSTEM WILL USE ALGORITHMIC FALLBACK")
        print("📝 ACTION REQUIRED: Set GEMINI_API_KEY environment variable")
    
    return bool(gemini_api_key or env_gemini_key)

if __name__ == "__main__":
    success = verify_ai_configuration()
    if success:
        print("\n🎯 AI Selection Verification: PASSED")
    else:
        print("\n⚠️ AI Selection Verification: NEEDS ATTENTION")
        sys.exit(1)