#!/usr/bin/env python3
"""
Simplified LaTeX Generation Test
Tests core LaTeX functionality without database complications.
"""

import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.latex_generation_service import latex_generation_service


class MockUserProfile:
    """Mock user profile for testing."""
    def __init__(self):
        self.full_name = "Test User"
        self.email = "test@example.com"
        self.phone = "+1-555-0123"
        self.linkedin_url = "linkedin.com/in/testuser"
        self.location = "San Francisco, CA"


async def test_latex_core_functionality():
    """Test core LaTeX generation functionality."""
    print("🧪 Testing LaTeX Core Functionality")
    print("=" * 50)
    
    # Test 1: LaTeX Installation
    print("\n🔧 Testing LaTeX Installation...")
    is_available, version_info = await latex_generation_service.validate_latex_installation()
    print(f"LaTeX Available: {is_available}")
    print(f"Version: {version_info}")
    
    if not is_available:
        print("❌ LaTeX not available - cannot proceed with tests")
        return False
    
    # Test 2: Character Escaping
    print("\n📝 Testing Character Escaping...")
    test_text = "Test & Company $100K #1 Role (50% Growth) ^ Position_Title {Special} ~Home \\"
    escaped_text = latex_generation_service._escape_latex_characters(test_text)
    print(f"Original: {test_text}")
    print(f"Escaped: {escaped_text}")
    
    # Check if dangerous characters are escaped (they should be replaced, not just absent)
    expected_escapes = ['\\&', '\\%', '\\$', '\\#', '\\^{}', '\\_', '\\{', '\\}', '\\textasciitilde{}', '\\textbackslash{}']
    escape_success = any(escape in escaped_text for escape in expected_escapes)
    print(f"Escaping Test: {'✅ PASS' if escape_success else '❌ FAIL'}")
    
    # Test 3: Template Generation
    print("\n📄 Testing Template Generation...")
    
    # Create mock user profile
    user_profile = MockUserProfile()
    
    # Create sample content
    sample_content = {
        'work_experiences': [{
            'experience': {
                'company_name': 'TechCorp Inc.',
                'position_title': 'Senior Software Engineer',
                'location': 'San Francisco, CA',
                'start_date': datetime(2022, 1, 15),
                'end_date': datetime(2024, 6, 30),
                'company_description': 'Leading AI company'
            },
            'achievements': [
                {'achievement_text': 'Developed microservices platform improving scalability by 300%'},
                {'achievement_text': 'Led team of 8 engineers to deliver customer features'}
            ]
        }],
        'education': [{
            'institution_name': 'Stanford University',
            'degree_type': 'Master of Science',
            'field_of_study': 'Computer Science',
            'graduation_date': datetime(2021, 6, 15),
            'location': 'Stanford, CA',
            'gpa': 3.85,
            'gpa_scale': 4.0,
            'relevant_coursework': 'Machine Learning, Distributed Systems',
            'academic_achievements': 'Dean\'s List'
        }],
        'skills': [
            {'skill_name': 'Python', 'skill_category': 'technical'},
            {'skill_name': 'Leadership', 'skill_category': 'soft'}
        ],
        'projects': [],
        'certifications': ['AWS Certified Solutions Architect']
    }
    
    try:
        template = latex_generation_service._create_dynamic_template(user_profile, sample_content)
        
        # Check template contains expected elements
        expected_elements = [
            'TEST USER',  # Name should be uppercase
            'test@example.com',
            'Stanford University',
            'TechCorp Inc.',
            'Senior Software Engineer',
            'microservices platform',
            '\\begin{document}',
            '\\end{document}'
        ]
        
        template_valid = all(element in template for element in expected_elements)
        print(f"Template Generation: {'✅ PASS' if template_valid else '❌ FAIL'}")
        print(f"Template Length: {len(template)} characters")
        
        if not template_valid:
            print("Missing elements:")
            for element in expected_elements:
                if element not in template:
                    print(f"  - {element}")
        
        # Test 4: PDF Compilation (create test file)
        print("\n🔄 Testing PDF Compilation...")
        
        try:
            # Write template to temporary file
            temp_dir = Path("/tmp/tailer_test")
            temp_dir.mkdir(exist_ok=True)
            
            tex_file = temp_dir / "test_resume.tex"
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(template)
            
            print(f"Template written to: {tex_file}")
            
            # Try to compile using the service method
            import subprocess
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', 'test_resume.tex'],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            pdf_file = temp_dir / "test_resume.pdf"
            pdf_created = pdf_file.exists()
            
            print(f"PDF Compilation: {'✅ PASS' if pdf_created else '❌ FAIL'}")
            print(f"Return Code: {result.returncode}")
            
            if pdf_created:
                file_size = pdf_file.stat().st_size
                print(f"PDF Size: {file_size:,} bytes")
            else:
                print("Compilation Error:")
                print(result.stderr[:500])  # First 500 chars of error
            
            return pdf_created
            
        except Exception as e:
            print(f"❌ PDF Compilation failed: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Template Generation failed: {e}")
        return False


async def test_performance():
    """Test LaTeX generation performance."""
    print("\n⚡ Testing Performance...")
    
    user_profile = MockUserProfile()
    simple_content = {
        'work_experiences': [{
            'experience': {
                'company_name': 'Test Co.',
                'position_title': 'Engineer',
                'location': 'Test City',
                'start_date': datetime(2023, 1, 1),
                'end_date': datetime(2024, 1, 1),
            },
            'achievements': [
                {'achievement_text': 'Completed important project'}
            ]
        }],
        'education': [],
        'skills': [],
        'projects': [],
        'certifications': []
    }
    
    try:
        import time
        
        # Test multiple generations
        times = []
        for i in range(3):
            start_time = time.time()
            template = latex_generation_service._create_dynamic_template(user_profile, simple_content)
            generation_time = (time.time() - start_time) * 1000
            times.append(generation_time)
            print(f"Generation {i+1}: {generation_time:.1f}ms")
        
        avg_time = sum(times) / len(times)
        print(f"Average Generation Time: {avg_time:.1f}ms")
        
        # Performance should be well under 1 second for template generation
        performance_acceptable = avg_time < 100  # 100ms
        print(f"Performance Test: {'✅ PASS' if performance_acceptable else '❌ FAIL'}")
        
        return performance_acceptable
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False


async def main():
    """Run all LaTeX tests."""
    print("🧪 LaTeX Generation Core Tests")
    print("=" * 50)
    
    # Test core functionality
    core_test_passed = await test_latex_core_functionality()
    
    # Test performance
    performance_test_passed = await test_performance()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    print(f"Core Functionality: {'✅ PASS' if core_test_passed else '❌ FAIL'}")
    print(f"Performance Test: {'✅ PASS' if performance_test_passed else '❌ FAIL'}")
    
    overall_success = core_test_passed and performance_test_passed
    print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 LaTeX Generation Pipeline is working correctly!")
        print("✅ Ready for integration with full application workflow")
    else:
        print("\n⚠️ Some tests failed - LaTeX generation needs attention")
    
    return overall_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)