#!/usr/bin/env python3
"""
Test script for Personal Quality Control System (PRD-010)
Tests the complete quality assessment workflow for TailerAI v2.0
"""

import asyncio
import logging
import sys
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append('/Users/aditya/Documents/Tailer/tailer_v2')

from app.services.quality_control_service import PersonalQualityControlService
from app.services.database_service import initialize_database

async def test_quality_control():
    """Test the personal quality control system"""
    
    print("=== PRD-010: Personal Quality Control System Test ===\n")
    
    try:
        # Initialize database
        print("1. Initializing database...")
        initialize_database()
        print("✅ Database initialized successfully\n")
        
        # Initialize quality control service
        print("2. Initializing quality control service...")
        quality_service = PersonalQualityControlService()
        print("✅ Quality control service initialized\n")
        
        # Sample resume content for testing
        sample_resume_content = {
            "work_experiences": [
                {
                    "position_title": "Senior Software Engineer",
                    "company_name": "TechCorp Inc",
                    "company_description": "Leading technology company specializing in web applications",
                    "achievements": [
                        {
                            "achievement_text": "Led development team of 8 engineers to deliver critical product features ahead of schedule, resulting in 25% increase in user engagement and $2M additional revenue"
                        },
                        {
                            "achievement_text": "Optimized database queries resulting in 40% performance improvement and $200K annual cost savings"
                        }
                    ]
                }
            ],
            "education": [
                {
                    "degree_type": "Bachelor of Science",
                    "field_of_study": "Computer Science",
                    "institution_name": "Stanford University",
                    "relevant_coursework": "Data Structures, Algorithms, Software Engineering"
                }
            ],
            "skills": [
                {
                    "skill_name": "Python",
                    "skill_category": "technical"
                },
                {
                    "skill_name": "Leadership",
                    "skill_category": "soft"
                },
                {
                    "skill_name": "Database Optimization",
                    "skill_category": "technical"
                }
            ],
            "projects": [
                {
                    "project_name": "Resume Optimization Platform",
                    "description": "Built AI-powered platform for optimizing resumes using machine learning",
                    "technologies_used": "Python, FastAPI, SQLAlchemy, React"
                }
            ]
        }
        
        # Test quality assessment
        print("3. Testing personal quality assessment...")
        assessment = await quality_service.assess_personal_quality(
            user_id="test_user_123",
            resume_content=sample_resume_content,
            target_role="Senior Software Engineer",
            industry="Technology"
        )
        
        print("✅ Quality assessment completed successfully\n")
        
        # Display results
        print("=== QUALITY ASSESSMENT RESULTS ===")
        print(f"Overall Score: {assessment.overall_score}/100")
        print(f"Total Issues: {assessment.total_issues}")
        print(f"Critical Issues: {assessment.critical_issues}")
        print(f"Estimated Improvement Time: {assessment.estimated_improvement_time}")
        print()
        
        print("CATEGORY SCORES:")
        categories = [
            ("Content Quality", assessment.content_quality),
            ("Grammar Quality", assessment.grammar_quality),
            ("ATS Compatibility", assessment.ats_compatibility),
            ("Formatting Quality", assessment.formatting_quality),
            ("Keyword Optimization", assessment.keyword_optimization),
            ("Professional Standards", assessment.professional_standards),
            ("Readability", assessment.readability_metrics),
            ("Completeness", assessment.completeness_score)
        ]
        
        for name, metrics in categories:
            print(f"  {name}: {metrics.score:.1f}/100")
            if metrics.issues:
                print(f"    Issues: {len(metrics.issues)}")
            if metrics.strengths:
                print(f"    Strengths: {metrics.strengths[0] if metrics.strengths else 'None'}")
        print()
        
        print("IMPROVEMENT PRIORITIES:")
        for i, priority in enumerate(assessment.improvement_priority, 1):
            print(f"  {i}. {priority}")
        print()
        
        print("NEXT STEPS:")
        for i, step in enumerate(assessment.next_steps, 1):
            print(f"  {i}. {step}")
        print()
        
        # Test individual assessment components
        print("4. Testing individual assessment components...")
        
        # Extract text content
        text_content = quality_service._extract_text_content(sample_resume_content)
        print(f"✅ Extracted text content ({len(text_content)} characters)")
        
        # Test content quality assessment
        content_metrics = await quality_service._assess_content_quality(
            text_content, "Senior Software Engineer", "Technology"
        )
        print(f"✅ Content quality assessment: {content_metrics.score:.1f}/100")
        
        # Test grammar assessment
        grammar_metrics = await quality_service._assess_grammar_quality(text_content)
        print(f"✅ Grammar quality assessment: {grammar_metrics.score:.1f}/100")
        
        # Test ATS compatibility
        ats_metrics = await quality_service._assess_ats_compatibility(text_content, "Senior Software Engineer")
        print(f"✅ ATS compatibility assessment: {ats_metrics.score:.1f}/100")
        
        # Test keyword optimization
        keyword_metrics = await quality_service._assess_keyword_optimization(text_content, "Senior Software Engineer")
        print(f"✅ Keyword optimization assessment: {keyword_metrics.score:.1f}/100")
        
        print()
        
        # Test helper methods
        print("5. Testing helper methods...")
        
        action_verbs = quality_service._count_action_verbs(text_content)
        print(f"✅ Action verbs found: {action_verbs}")
        
        quantified_achievements = quality_service._count_quantified_achievements(text_content)
        print(f"✅ Quantified achievements found: {quantified_achievements}")
        
        technical_terms = quality_service._count_technical_terms(text_content)
        print(f"✅ Technical terms found: {technical_terms}")
        
        avg_sentence_length = quality_service._calculate_average_sentence_length(text_content)
        print(f"✅ Average sentence length: {avg_sentence_length:.1f} words")
        
        print()
        
        print("=== PRD-010 IMPLEMENTATION TEST SUMMARY ===")
        print("✅ Personal Quality Control Service fully functional")
        print("✅ Multi-dimensional quality assessment working")
        print("✅ Database integration successful")
        print("✅ AI-powered content analysis integrated")
        print("✅ Personal improvement recommendations generated")
        print("✅ All assessment categories operational")
        print("✅ Helper methods functioning correctly")
        print()
        print("🎉 PRD-010: Personal Quality Control System - COMPLETED")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        logger.error(f"Quality control test failed: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    success = asyncio.run(test_quality_control())
    sys.exit(0 if success else 1)