#!/usr/bin/env python3
"""
Comprehensive Service Integration Testing Suite
Tests all services for functionality, error handling, and integration
"""

import asyncio
import logging
import sys
import json
from typing import Dict, List, Any
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append('/Users/aditya/Documents/Tailer/tailer_v2')

from app.services.database_service import initialize_database, reset_database, db_service
from app.services.auth_service import AuthService
from app.services.master_dataset_service import master_dataset_service
from app.services.job_analysis_service import JobDescriptionAnalyzer
from app.services.content_selection_service import ContentSelectionEngine
from app.services.ats_optimization_service import ATSOptimizationEngine
from app.services.latex_generation_service import LaTeXGenerationService
from app.services.quality_control_service import PersonalQualityControlService

class ServiceIntegrationTester:
    """Comprehensive service integration testing"""
    
    def __init__(self):
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "service_results": {},
            "integration_tests": {},
            "performance_metrics": {},
            "error_handling_tests": {}
        }
        
    async def run_comprehensive_tests(self):
        """Run all service integration tests"""
        print("=== COMPREHENSIVE SERVICE INTEGRATION TESTING ===\n")
        
        try:
            # Initialize database
            print("1. Setting up test environment...")
            try:
                initialize_database()
                print("✅ Database initialized")
            except Exception as e:
                print(f"⚠️  Database initialization issue: {e}")
                # Continue with tests anyway
            
            # Test database service
            print("2. Testing database service...")
            await self._test_database_service()
            
            # Test authentication service
            print("3. Testing authentication service...")
            await self._test_auth_service()
            
            # Test master dataset service
            print("4. Testing master dataset service...")
            await self._test_master_dataset_service()
            
            # Test job analysis service
            print("5. Testing job analysis service...")
            await self._test_job_analysis_service()
            
            # Test content selection service
            print("6. Testing content selection service...")
            await self._test_content_selection_service()
            
            # Test ATS optimization service
            print("7. Testing ATS optimization service...")
            await self._test_ats_optimization_service()
            
            # Test quality control service
            print("8. Testing quality control service...")
            await self._test_quality_control_service()
            
            # Test LaTeX generation service
            print("9. Testing LaTeX generation service...")
            await self._test_latex_generation_service()
            
            # Test service integrations
            print("10. Testing service integrations...")
            await self._test_service_integrations()
            
            # Test error handling
            print("11. Testing error handling...")
            await self._test_error_handling()
            
            # Generate report
            print("12. Generating test report...")
            await self._generate_report()
            
            return True
            
        except Exception as e:
            logger.error(f"Service integration testing failed: {e}")
            return False
    
    async def _test_database_service(self):
        """Test database service functionality"""
        try:
            # Test health check
            health = db_service.health_check()
            self._record_test_result("database_health", health["status"] == "healthy", 
                                   f"Database health: {health['status']}")
            
            # Test table info
            table_info = db_service.get_table_info()
            self._record_test_result("database_tables", table_info["status"] == "success",
                                   f"Table info: {len(table_info.get('tables', {}))}")
            
        except Exception as e:
            self._record_test_result("database_service", False, f"Database service error: {e}")
    
    async def _test_auth_service(self):
        """Test authentication service"""
        try:
            auth_service = AuthService()
            
            # Test user registration
            user_data = {
                "username": "testuser_service",
                "email": "testuser_service@example.com",
                "password": "TestPassword123!",
                "full_name": "Service Test User"
            }
            
            start_time = datetime.now()
            user = await auth_service.create_user(**user_data)
            registration_time = (datetime.now() - start_time).total_seconds() * 1000
            
            self._record_test_result("auth_registration", user is not None, 
                                   f"User registration: {registration_time:.0f}ms")
            
            if user:
                # Test login
                start_time = datetime.now()
                login_result = await auth_service.authenticate_user(user_data["username"], user_data["password"])
                login_time = (datetime.now() - start_time).total_seconds() * 1000
                
                self._record_test_result("auth_login", login_result is not None,
                                       f"User login: {login_time:.0f}ms")
                
                # Test token generation
                start_time = datetime.now()
                token = auth_service.create_access_token(user.id)
                token_time = (datetime.now() - start_time).total_seconds() * 1000
                
                self._record_test_result("auth_token", token is not None,
                                       f"Token generation: {token_time:.0f}ms")
            
        except Exception as e:
            self._record_test_result("auth_service", False, f"Auth service error: {e}")
    
    async def _test_master_dataset_service(self):
        """Test master dataset service"""
        try:
            # Test profile creation
            profile_data = {
                "user_id": "test_user_service",
                "full_name": "Service Test User",
                "email": "testuser_service@example.com",
                "target_industries": ["Technology"],
                "career_level": "mid"
            }
            
            start_time = datetime.now()
            profile = await master_dataset_service.create_user_profile(**profile_data)
            profile_time = (datetime.now() - start_time).total_seconds() * 1000
            
            self._record_test_result("master_dataset_profile", profile is not None,
                                   f"Profile creation: {profile_time:.0f}ms")
            
            if profile:
                # Test work experience creation
                work_exp_data = {
                    "profile_id": profile.id,
                    "company_name": "Test Corp",
                    "position_title": "Test Engineer",
                    "employment_type": "full-time",
                    "start_date": datetime(2023, 1, 1),
                    "location": "Test City"
                }
                
                start_time = datetime.now()
                work_exp = await master_dataset_service.create_work_experience(**work_exp_data)
                work_exp_time = (datetime.now() - start_time).total_seconds() * 1000
                
                self._record_test_result("master_dataset_work_exp", work_exp is not None,
                                       f"Work experience creation: {work_exp_time:.0f}ms")
            
        except Exception as e:
            self._record_test_result("master_dataset_service", False, f"Master dataset service error: {e}")
    
    async def _test_job_analysis_service(self):
        """Test job analysis service"""
        try:
            job_service = JobDescriptionAnalyzer()
            
            job_description = """
            Senior Software Engineer
            
            We are looking for a Senior Software Engineer with expertise in Python, FastAPI, 
            and database design. The ideal candidate will have 5+ years of experience in 
            web development and API design.
            
            Requirements:
            - Python programming
            - FastAPI framework
            - Database design (PostgreSQL)
            - REST API development
            - Agile methodologies
            """
            
            start_time = datetime.now()
            analysis = await job_service.analyze_job_posting(job_description)
            analysis_time = (datetime.now() - start_time).total_seconds() * 1000
            
            self._record_test_result("job_analysis", analysis is not None,
                                   f"Job analysis: {analysis_time:.0f}ms")
            
            self.test_results["performance_metrics"]["job_analysis_time"] = analysis_time
            
        except Exception as e:
            self._record_test_result("job_analysis_service", False, f"Job analysis service error: {e}")
    
    async def _test_content_selection_service(self):
        """Test content selection service"""
        try:
            content_service = ContentSelectionEngine()
            
            # Mock job analysis result
            mock_job_analysis = {
                "required_skills": ["Python", "FastAPI", "Database"],
                "preferred_skills": ["PostgreSQL", "REST API"],
                "key_requirements": ["5+ years experience", "web development"],
                "important_keywords": ["python", "fastapi", "database", "api"]
            }
            
            start_time = datetime.now()
            result = await content_service.select_optimal_content("test_user_service", mock_job_analysis)
            selection_time = (datetime.now() - start_time).total_seconds() * 1000
            
            self._record_test_result("content_selection", result is not None,
                                   f"Content selection: {selection_time:.0f}ms")
            
            self.test_results["performance_metrics"]["content_selection_time"] = selection_time
            
        except Exception as e:
            self._record_test_result("content_selection_service", False, f"Content selection service error: {e}")
    
    async def _test_ats_optimization_service(self):
        """Test ATS optimization service"""
        try:
            ats_service = ATSOptimizationEngine()
            
            sample_content = "Software Engineer with Python and FastAPI experience"
            target_keywords = ["python", "fastapi", "software engineer"]
            
            start_time = datetime.now()
            optimization = await ats_service.optimize_content(
                user_id="test_user_service",
                content=sample_content,
                target_keywords=target_keywords
            )
            optimization_time = (datetime.now() - start_time).total_seconds() * 1000
            
            self._record_test_result("ats_optimization", optimization is not None,
                                   f"ATS optimization: {optimization_time:.0f}ms")
            
            self.test_results["performance_metrics"]["ats_optimization_time"] = optimization_time
            
        except Exception as e:
            self._record_test_result("ats_optimization_service", False, f"ATS optimization service error: {e}")
    
    async def _test_quality_control_service(self):
        """Test quality control service"""
        try:
            quality_service = PersonalQualityControlService()
            
            sample_resume_content = {
                "work_experiences": [{
                    "position_title": "Software Engineer",
                    "company_name": "Test Corp",
                    "achievements": [{
                        "achievement_text": "Developed Python applications with 25% performance improvement"
                    }]
                }],
                "education": [{
                    "degree_type": "Bachelor of Science",
                    "field_of_study": "Computer Science",
                    "institution_name": "Test University"
                }],
                "skills": [{
                    "skill_name": "Python",
                    "skill_category": "technical"
                }]
            }
            
            start_time = datetime.now()
            assessment = await quality_service.assess_personal_quality(
                user_id="test_user_service",
                resume_content=sample_resume_content,
                target_role="Software Engineer"
            )
            assessment_time = (datetime.now() - start_time).total_seconds() * 1000
            
            self._record_test_result("quality_assessment", assessment is not None,
                                   f"Quality assessment: {assessment_time:.0f}ms")
            
            self.test_results["performance_metrics"]["quality_assessment_time"] = assessment_time
            
        except Exception as e:
            self._record_test_result("quality_control_service", False, f"Quality control service error: {e}")
    
    async def _test_latex_generation_service(self):
        """Test LaTeX generation service"""
        try:
            latex_service = LaTeXGenerationService()
            
            # Test LaTeX system status
            status = latex_service.check_latex_installation()
            self._record_test_result("latex_installation", status["latex_available"],
                                   f"LaTeX installation: {status['status']}")
            
            if status["latex_available"]:
                sample_resume_data = {
                    "name": "Test User",
                    "email": "test@example.com",
                    "phone": "+1234567890",
                    "work_experiences": [{
                        "position": "Software Engineer",
                        "company": "Test Corp",
                        "start_date": "2023-01",
                        "end_date": "Present",
                        "achievements": ["Developed Python applications"]
                    }]
                }
                
                start_time = datetime.now()
                template = latex_service.generate_latex_template(sample_resume_data)
                template_time = (datetime.now() - start_time).total_seconds() * 1000
                
                self._record_test_result("latex_template", template is not None,
                                       f"LaTeX template generation: {template_time:.0f}ms")
                
                self.test_results["performance_metrics"]["latex_template_time"] = template_time
            
        except Exception as e:
            self._record_test_result("latex_generation_service", False, f"LaTeX generation service error: {e}")
    
    async def _test_service_integrations(self):
        """Test service integrations and workflows"""
        try:
            # Test end-to-end workflow simulation
            print("  Testing end-to-end workflow...")
            
            # 1. Job analysis -> Content selection integration
            job_service = JobDescriptionAnalyzer()
            content_service = ContentSelectionEngine()
            
            job_description = "Python developer with FastAPI experience needed"
            
            start_time = datetime.now()
            job_analysis = await job_service.analyze_job_posting(job_description)
            
            if job_analysis:
                content_result = await content_service.select_optimal_content("test_user_service", job_analysis.__dict__)
                integration_time = (datetime.now() - start_time).total_seconds() * 1000
                
                self._record_test_result("job_to_content_integration", content_result is not None,
                                       f"Job->Content integration: {integration_time:.0f}ms")
            
            # 2. Quality assessment integration
            quality_service = PersonalQualityControlService()
            
            sample_content = {
                "work_experiences": [{"position_title": "Developer", "company_name": "Corp"}],
                "skills": [{"skill_name": "Python"}]
            }
            
            start_time = datetime.now()
            quality_result = await quality_service.assess_personal_quality(
                "test_user_service", sample_content
            )
            quality_integration_time = (datetime.now() - start_time).total_seconds() * 1000
            
            self._record_test_result("quality_integration", quality_result is not None,
                                   f"Quality integration: {quality_integration_time:.0f}ms")
            
        except Exception as e:
            self._record_test_result("service_integrations", False, f"Service integration error: {e}")
    
    async def _test_error_handling(self):
        """Test error handling across services"""
        try:
            # Test invalid input handling
            job_service = JobDescriptionAnalyzer()
            
            # Test with empty job description
            try:
                result = await job_service.analyze_job_posting("")
                self._record_test_result("error_empty_job", True, "Empty job description handled gracefully")
            except Exception:
                self._record_test_result("error_empty_job", False, "Empty job description not handled")
            
            # Test master dataset with invalid data
            try:
                result = await master_dataset_service.create_user_profile(
                    user_id="", full_name="", email="invalid-email"
                )
                self._record_test_result("error_invalid_profile", False, "Invalid profile data accepted")
            except Exception:
                self._record_test_result("error_invalid_profile", True, "Invalid profile data rejected properly")
            
        except Exception as e:
            self._record_test_result("error_handling", False, f"Error handling test failed: {e}")
    
    def _record_test_result(self, test_name: str, passed: bool, message: str):
        """Record test result"""
        self.test_results["total_tests"] += 1
        if passed:
            self.test_results["passed_tests"] += 1
        else:
            self.test_results["failed_tests"] += 1
        
        self.test_results["service_results"][test_name] = {
            "passed": passed,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        status = "✅" if passed else "❌"
        print(f"  {status} {test_name}: {message}")
    
    async def _generate_report(self):
        """Generate comprehensive test report"""
        report_path = "/Users/aditya/Documents/Tailer/tailer_v2/reports/service_integration_test_report.json"
        
        # Calculate summary statistics
        success_rate = (self.test_results["passed_tests"] / self.test_results["total_tests"]) * 100 if self.test_results["total_tests"] > 0 else 0
        
        self.test_results["summary"] = {
            "success_rate": f"{success_rate:.1f}%",
            "total_services_tested": len(set([test.split("_")[0] for test in self.test_results["service_results"].keys()])),
            "average_response_time": sum(self.test_results["performance_metrics"].values()) / len(self.test_results["performance_metrics"]) if self.test_results["performance_metrics"] else 0,
            "performance_benchmark": "Good" if sum(self.test_results["performance_metrics"].values()) / len(self.test_results["performance_metrics"]) < 2000 else "Needs Optimization" if self.test_results["performance_metrics"] else "N/A"
        }
        
        # Write report
        with open(report_path, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n=== SERVICE INTEGRATION TEST SUMMARY ===")
        print(f"Total Tests: {self.test_results['total_tests']}")
        print(f"Passed: {self.test_results['passed_tests']}")
        print(f"Failed: {self.test_results['failed_tests']}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Services Tested: {self.test_results['summary']['total_services_tested']}")
        print(f"Average Response Time: {self.test_results['summary']['average_response_time']:.0f}ms")
        print(f"Performance Benchmark: {self.test_results['summary']['performance_benchmark']}")
        print(f"Report saved to: {report_path}")


async def main():
    """Main test execution"""
    tester = ServiceIntegrationTester()
    success = await tester.run_comprehensive_tests()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)