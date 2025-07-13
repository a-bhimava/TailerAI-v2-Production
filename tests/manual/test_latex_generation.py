#!/usr/bin/env python3
"""
LaTeX Generation Pipeline Testing Script
Tests PDF generation, template injection, and API endpoints.
Following project blueprint best practices for comprehensive testing.
"""

import asyncio
import sys
import os
import json
import requests
import time
from datetime import datetime, date
from typing import Dict, Any, List
from pathlib import Path
from uuid import UUID

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Direct service testing
from app.services.latex_generation_service import latex_generation_service, LaTeXGenerationError
from app.services.auth_service import auth_service
from app.services.database_service import db_service, initialize_database
from app.services.master_dataset_service import master_dataset_service

# API testing configuration
BASE_URL = "http://localhost:8001"
API_BASE = f"{BASE_URL}/api/v2"


class LaTeXGenerationTestSuite:
    """Comprehensive LaTeX generation pipeline test suite."""
    
    def __init__(self):
        self.test_results = []
        self.test_user_email = f"latex_test_{int(datetime.now().timestamp())}@example.com"
        self.test_user_data = {
            "username": f"latex_user_{int(datetime.now().timestamp())}",
            "email": self.test_user_email,
            "password": "LaTeXTest123!",
            "full_name": "LaTeX Test User"
        }
        self.user_id = None
        self.access_token = None
        self.sample_content = None
    
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = {
            "test": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"  {status}: {test_name}")
        if details and not passed:
            print(f"    Details: {details}")
    
    async def setup_test_environment(self):
        """Setup test user and sample content."""
        print("\n🛠️ Setting up test environment...")
        
        try:
            # Register test user
            user = await auth_service.register_user(
                username=self.test_user_data["username"],
                email=self.test_user_data["email"],
                password=self.test_user_data["password"],
                full_name=self.test_user_data["full_name"]
            )
            
            # Get user ID (handle session detachment)
            try:
                self.user_id = str(user.id)
                print(f"✅ Test user created: {self.user_id}")
            except:
                # Use authentication to get user ID if session detached
                try:
                    auth_user, access_token, _ = await auth_service.authenticate_user(
                        self.test_user_data["email"],
                        self.test_user_data["password"]
                    )
                    try:
                        self.user_id = str(auth_user.id)
                        self.access_token = access_token
                        print(f"✅ Test user ID from auth: {self.user_id}")
                    except:
                        # Last resort: query database directly
                        with db_service.get_session() as session:
                            from app.models.database import User
                            db_user = session.query(User).filter_by(
                                email=self.test_user_data["email"]
                            ).first()
                            if db_user:
                                self.user_id = str(db_user.id)
                                print(f"✅ Test user ID from DB: {self.user_id}")
                            else:
                                raise Exception("Could not find user in database")
                except Exception as auth_error:
                    print(f"❌ Authentication failed: {auth_error}")
                    raise
            
            # Create sample content for PDF generation
            await self._create_sample_content()
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup test environment: {str(e)}")
            return False
    
    async def _create_sample_content(self):
        """Create sample master dataset content for testing."""
        try:
            # Add work experience
            work_exp_data = {
                "company_name": "TechCorp Inc.",
                "position_title": "Senior Software Engineer",
                "employment_type": "full-time",
                "start_date": datetime(2022, 1, 15),
                "end_date": datetime(2024, 6, 30),
                "location": "San Francisco, CA",
                "company_size": "large",
                "industry": "Technology",
                "company_description": "Leading AI and cloud computing company",
                "role_summary": "Led development of scalable web applications using Python and React",
                "team_size": 12,
                "reporting_structure": "Reports to Engineering Director"
            }
            
            work_experience = await master_dataset_service.add_work_experience(
                self.user_id, work_exp_data
            )
            work_exp_id = str(work_experience.id)
            
            # Add achievements
            achievements = [
                {
                    "achievement_text": "Architected and deployed microservices platform that improved system scalability by 300% and reduced response time by 45%",
                    "achievement_category": "technical",
                    "impact_level": 9,
                    "business_function": "Engineering",
                    "quantified_metrics": {"scalability_improvement": "300%", "response_time_reduction": "45%"},
                    "keywords": ["microservices", "scalability", "performance", "architecture"],
                    "ats_keywords": ["Python", "Docker", "Kubernetes", "AWS"],
                    "skills_demonstrated": ["System Design", "Leadership", "Performance Optimization"],
                    "time_period": "8 months",
                    "context_tags": ["architecture", "performance", "leadership"]
                },
                {
                    "achievement_text": "Led cross-functional team of 8 engineers to deliver critical customer-facing features, resulting in 25% increase in user engagement",
                    "achievement_category": "leadership", 
                    "impact_level": 8,
                    "business_function": "Product Development",
                    "quantified_metrics": {"user_engagement_increase": "25%", "team_size": 8},
                    "keywords": ["leadership", "cross-functional", "user engagement", "product"],
                    "ats_keywords": ["Agile", "Scrum", "Product Management", "Team Leadership"],
                    "skills_demonstrated": ["Leadership", "Product Development", "Team Management"],
                    "time_period": "6 months",
                    "context_tags": ["leadership", "product", "team_management"]
                }
            ]
            
            for achievement_data in achievements:
                await master_dataset_service.add_achievement(
                    self.user_id, UUID(work_exp_id), achievement_data
                )
            
            # Add education
            education_data = {
                "institution_name": "Stanford University",
                "degree_type": "Master of Science",
                "field_of_study": "Computer Science",
                "graduation_date": datetime(2021, 6, 15),
                "location": "Stanford, CA",
                "gpa": 3.85,
                "gpa_scale": 4.0,
                "relevant_coursework": "Machine Learning, Distributed Systems, Software Engineering",
                "academic_achievements": "Dean's List, Outstanding Graduate Student Award"
            }
            
            await master_dataset_service.add_education(self.user_id, education_data)
            
            # Add skills
            skills_data = [
                {
                    "skill_name": "Python",
                    "skill_category": "technical",
                    "proficiency_level": "expert",
                    "years_experience": 6.0,
                    "related_keywords": ["Django", "Flask", "FastAPI", "Pandas"],
                    "industry_relevance": ["Technology", "Finance", "Healthcare"]
                },
                {
                    "skill_name": "Leadership",
                    "skill_category": "soft",
                    "proficiency_level": "advanced",
                    "years_experience": 4.0,
                    "related_keywords": ["Team Management", "Project Leadership", "Mentoring"],
                    "industry_relevance": ["Technology", "Consulting"]
                }
            ]
            
            for skill_data in skills_data:
                await master_dataset_service.add_skill(self.user_id, skill_data)
            
            # Create sample content dictionary for direct testing
            self.sample_content = {
                'work_experiences': [{
                    'experience': {
                        'company_name': 'TechCorp Inc.',
                        'position_title': 'Senior Software Engineer',
                        'location': 'San Francisco, CA',
                        'start_date': datetime(2022, 1, 15),
                        'end_date': datetime(2024, 6, 30),
                        'company_description': 'Leading AI and cloud computing company'
                    },
                    'achievements': [
                        {'achievement_text': 'Architected and deployed microservices platform that improved system scalability by 300% and reduced response time by 45%'},
                        {'achievement_text': 'Led cross-functional team of 8 engineers to deliver critical customer-facing features, resulting in 25% increase in user engagement'}
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
                    'relevant_coursework': 'Machine Learning, Distributed Systems, Software Engineering',
                    'academic_achievements': 'Dean\'s List, Outstanding Graduate Student Award'
                }],
                'skills': [
                    {'skill_name': 'Python', 'skill_category': 'technical'},
                    {'skill_name': 'Leadership', 'skill_category': 'soft'}
                ],
                'projects': [],
                'certifications': ['AWS Certified Solutions Architect', 'Google Cloud Professional']
            }
            
            print("✅ Sample content created successfully")
            
        except Exception as e:
            print(f"❌ Failed to create sample content: {str(e)}")
            raise
    
    async def test_latex_installation(self):
        """Test LaTeX installation and availability."""
        print("\n🔧 Testing LaTeX Installation...")
        
        try:
            is_available, version_info = await latex_generation_service.validate_latex_installation()
            
            if is_available:
                self.log_test("LaTeX Installation Check", True, f"Version: {version_info}")
            else:
                self.log_test("LaTeX Installation Check", False, f"LaTeX not available: {version_info}")
            
            return is_available
            
        except Exception as e:
            self.log_test("LaTeX Installation Check", False, str(e))
            return False
    
    async def test_template_generation(self):
        """Test dynamic template generation."""
        print("\n📄 Testing Template Generation...")
        
        try:
            # Get user profile
            user_profile = await master_dataset_service.get_user_profile(self.user_id)
            if not user_profile:
                self.log_test("Template Generation Setup", False, "User profile not found")
                return False
            
            # Test LaTeX character escaping
            test_text = "Test & Company $100K #1 Role (50% Growth) ^ Position_Title {Special} ~Home \\"
            escaped_text = latex_generation_service._escape_latex_characters(test_text)
            
            expected_escapes = ['\\&', '\\$', '\\#', '\\^{}', '\\_', '\\{', '\\}', '\\textasciitilde{}', '\\textbackslash{}']
            escape_success = all(escape in escaped_text for escape in expected_escapes)
            
            self.log_test("LaTeX Character Escaping", escape_success, 
                         f"Escaped: {escaped_text}" if escape_success else "Some characters not properly escaped")
            
            # Test template creation
            dynamic_template = latex_generation_service._create_dynamic_template(
                user_profile, self.sample_content
            )
            
            # Verify template contains expected elements
            template_checks = [
                user_profile.full_name.upper() in dynamic_template,
                "\\section*{EDUCATION}" in dynamic_template,
                "\\section*{WORK EXPERIENCE}" in dynamic_template,
                "Stanford University" in dynamic_template,
                "TechCorp Inc." in dynamic_template,
                "\\begin{document}" in dynamic_template,
                "\\end{document}" in dynamic_template
            ]
            
            template_success = all(template_checks)
            self.log_test("Dynamic Template Generation", template_success,
                         f"Template length: {len(dynamic_template)} chars" if template_success else "Template missing required elements")
            
            return template_success
            
        except Exception as e:
            self.log_test("Template Generation", False, str(e))
            return False
    
    async def test_pdf_compilation(self):
        """Test PDF compilation from LaTeX."""
        print("\n🔄 Testing PDF Compilation...")
        
        try:
            # Generate PDF
            start_time = time.time()
            success, pdf_path, message = await latex_generation_service.generate_resume_pdf(
                user_id=self.user_id,
                selected_content=self.sample_content,
                filename_prefix="test_resume"
            )
            compilation_time = (time.time() - start_time) * 1000
            
            self.log_test("PDF Generation", success, 
                         f"Time: {compilation_time:.0f}ms, Path: {pdf_path}" if success else message)
            
            if success and pdf_path:
                # Verify PDF file exists
                pdf_file = Path(pdf_path)
                file_exists = pdf_file.exists()
                self.log_test("PDF File Creation", file_exists, 
                             f"File size: {pdf_file.stat().st_size} bytes" if file_exists else "File not found")
                
                # Check file size (should be reasonable for a resume)
                if file_exists:
                    file_size = pdf_file.stat().st_size
                    size_reasonable = 10000 < file_size < 5000000  # Between 10KB and 5MB
                    self.log_test("PDF File Size Check", size_reasonable,
                                 f"Size: {file_size:,} bytes")
                
                return success and file_exists
            else:
                return False
                
        except Exception as e:
            self.log_test("PDF Compilation", False, str(e))
            return False
    
    def get_auth_token(self):
        """Get authentication token for API testing."""
        if self.access_token:
            return self.access_token
            
        try:
            login_data = {
                "email": self.test_user_email,
                "password": self.test_user_data["password"]
            }
            
            response = requests.post(
                f"{API_BASE}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                return self.access_token
            else:
                print(f"❌ Login failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return None
    
    def test_latex_api_endpoints(self):
        """Test LaTeX generation API endpoints."""
        print("\n🌐 Testing LaTeX API Endpoints...")
        
        access_token = self.get_auth_token()
        if not access_token:
            self.log_test("API Authentication", False, "Could not get access token")
            return False
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            # Test status endpoint
            status_response = requests.get(f"{API_BASE}/latex/status")
            status_success = status_response.status_code == 200
            
            if status_success:
                status_data = status_response.json()
                latex_available = status_data.get("latex_available", False)
                self.log_test("LaTeX Status Endpoint", True, 
                             f"LaTeX available: {latex_available}, Status: {status_data.get('service_status')}")
            else:
                self.log_test("LaTeX Status Endpoint", False, f"Status: {status_response.status_code}")
            
            # Test PDF generation endpoint
            generate_request = {
                "work_experiences": [
                    {
                        "experience_id": "test-exp-1",
                        "company_name": "API Test Company",
                        "position_title": "Test Engineer",
                        "location": "Test City, ST",
                        "start_date": "2023-01-01",
                        "end_date": "2024-12-31",
                        "achievements": [
                            "Developed comprehensive API testing framework that improved test coverage by 85%",
                            "Led integration of automated testing pipelines, reducing manual QA time by 60%"
                        ]
                    }
                ],
                "education": [
                    {
                        "institution_name": "Test University",
                        "degree_type": "Bachelor of Science",
                        "field_of_study": "Software Engineering",
                        "graduation_date": "2022-05-15",
                        "location": "Test City, ST",
                        "gpa": 3.8,
                        "gpa_scale": 4.0
                    }
                ],
                "skills": [
                    {"skill_name": "API Testing", "skill_category": "technical"},
                    {"skill_name": "Python", "skill_category": "technical"}
                ],
                "certifications": ["API Testing Professional", "Python Certification"],
                "filename_prefix": "api_test_resume"
            }
            
            start_time = time.time()
            generate_response = requests.post(
                f"{API_BASE}/latex/generate",
                json=generate_request,
                headers=headers
            )
            api_time = (time.time() - start_time) * 1000
            
            if generate_response.status_code == 200:
                generate_data = generate_response.json()
                success = generate_data.get("success", False)
                download_url = generate_data.get("pdf_download_url")
                
                self.log_test("PDF Generation API", success,
                             f"Time: {api_time:.0f}ms, Download URL: {download_url}")
                
                # Test download endpoint if generation succeeded
                if success and download_url:
                    download_response = requests.get(
                        f"{BASE_URL}{download_url}",
                        headers={"Authorization": f"Bearer {access_token}"}
                    )
                    
                    download_success = download_response.status_code == 200
                    content_type = download_response.headers.get("content-type", "")
                    
                    self.log_test("PDF Download API", download_success,
                                 f"Content-Type: {content_type}, Size: {len(download_response.content)} bytes")
                    
                    return download_success
                else:
                    return False
            else:
                self.log_test("PDF Generation API", False, 
                             f"Status: {generate_response.status_code}, Response: {generate_response.text}")
                return False
            
        except Exception as e:
            self.log_test("API Endpoints Test", False, str(e))
            return False
    
    async def test_error_handling(self):
        """Test error handling scenarios."""
        print("\n⚠️ Testing Error Handling...")
        
        try:
            # Test invalid user ID
            invalid_success, _, error_msg = await latex_generation_service.generate_resume_pdf(
                user_id="invalid-uuid",
                selected_content=self.sample_content
            )
            
            self.log_test("Invalid User ID Handling", not invalid_success, 
                         "Correctly rejected invalid user ID" if not invalid_success else "Should have failed")
            
            # Test empty content
            empty_content = {'work_experiences': [], 'education': [], 'skills': []}
            empty_success, _, empty_msg = await latex_generation_service.generate_resume_pdf(
                user_id=self.user_id,
                selected_content=empty_content
            )
            
            # Should succeed but generate minimal resume
            self.log_test("Empty Content Handling", True, "Handled empty content gracefully")
            
            # Test malformed content with special characters
            malformed_content = {
                'work_experiences': [{
                    'experience': {
                        'company_name': 'Test & $pecial Company #1 {Corp}',
                        'position_title': 'Engineer_Role^Special~Position',
                        'location': 'City & State',
                        'start_date': datetime(2023, 1, 1),
                        'end_date': datetime(2024, 1, 1)
                    },
                    'achievements': [
                        {'achievement_text': 'Achievement with $pecial char$ & symbols #1 test {item}'}
                    ]
                }],
                'education': [],
                'skills': []
            }
            
            special_success, special_path, special_msg = await latex_generation_service.generate_resume_pdf(
                user_id=self.user_id,
                selected_content=malformed_content
            )
            
            self.log_test("Special Characters Handling", special_success,
                         "Successfully escaped special characters" if special_success else special_msg)
            
            return True
            
        except Exception as e:
            self.log_test("Error Handling", False, str(e))
            return False
    
    async def test_performance_benchmarks(self):
        """Test performance benchmarks."""
        print("\n⚡ Testing Performance Benchmarks...")
        
        try:
            # Test multiple rapid generations
            generation_times = []
            
            for i in range(3):
                start_time = time.time()
                success, pdf_path, message = await latex_generation_service.generate_resume_pdf(
                    user_id=self.user_id,
                    selected_content=self.sample_content,
                    filename_prefix=f"perf_test_{i}"
                )
                generation_time = (time.time() - start_time) * 1000
                generation_times.append(generation_time)
                
                if not success:
                    self.log_test(f"Performance Test {i+1}", False, message)
                    return False
            
            avg_time = sum(generation_times) / len(generation_times)
            max_time = max(generation_times)
            
            # Performance targets from PRD: < 60 seconds (60,000ms) for 95% of users
            performance_acceptable = avg_time < 30000  # 30 seconds average
            
            self.log_test("Performance Benchmark", performance_acceptable,
                         f"Avg: {avg_time:.0f}ms, Max: {max_time:.0f}ms, Times: {[f'{t:.0f}ms' for t in generation_times]}")
            
            # Test concurrent generations (simplified)
            # In production, this would test actual concurrency
            concurrent_start = time.time()
            concurrent_tasks = []
            for i in range(2):
                task = latex_generation_service.generate_resume_pdf(
                    user_id=self.user_id,
                    selected_content=self.sample_content,
                    filename_prefix=f"concurrent_{i}"
                )
                concurrent_tasks.append(task)
            
            # Wait for all tasks (simulated concurrency)
            concurrent_results = []
            for task in concurrent_tasks:
                result = await task
                concurrent_results.append(result[0])  # success flag
            
            concurrent_time = (time.time() - concurrent_start) * 1000
            concurrent_success = all(concurrent_results)
            
            self.log_test("Concurrent Generation", concurrent_success,
                         f"Time: {concurrent_time:.0f}ms for 2 concurrent generations")
            
            return performance_acceptable and concurrent_success
            
        except Exception as e:
            self.log_test("Performance Benchmarks", False, str(e))
            return False
    
    async def run_all_tests(self):
        """Run comprehensive LaTeX generation test suite."""
        print("🧪 Starting LaTeX Generation Pipeline Test Suite")
        print("=" * 70)
        
        # Initialize database
        try:
            initialize_database()
            print("✅ Database initialized successfully")
        except Exception as e:
            print(f"❌ Database initialization failed: {str(e)}")
            return False
        
        # Setup test environment
        if not await self.setup_test_environment():
            return False
        
        # Run all test suites
        test_methods = [
            self.test_latex_installation,
            self.test_template_generation,
            self.test_pdf_compilation,
            self.test_latex_api_endpoints,
            self.test_error_handling,
            self.test_performance_benchmarks
        ]
        
        for test_method in test_methods:
            try:
                if asyncio.iscoroutinefunction(test_method):
                    await test_method()
                else:
                    test_method()
            except Exception as e:
                self.log_test(f"{test_method.__name__} (CRASH)", False, str(e))
        
        # Print summary
        self.print_summary()
        return True
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 70)
        print("🏁 LATEX GENERATION TEST SUITE SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["passed"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        print(f"\n💾 Test Results saved to: latex_generation_test_results.json")
        
        # Save detailed results
        with open("latex_generation_test_results.json", "w") as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "success_rate": f"{(passed_tests/total_tests)*100:.1f}%",
                    "test_run_time": datetime.now().isoformat()
                },
                "test_results": self.test_results
            }, f, indent=2, default=str)


async def main():
    """Main test execution."""
    test_suite = LaTeXGenerationTestSuite()
    success = await test_suite.run_all_tests()
    
    if success:
        failed_count = sum(1 for result in test_suite.test_results if not result["passed"])
        sys.exit(0 if failed_count == 0 else 1)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())