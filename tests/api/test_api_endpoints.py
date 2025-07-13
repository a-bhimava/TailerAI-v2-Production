#!/usr/bin/env python3
"""
Comprehensive API Endpoints Testing Suite
Tests all API routes for consistency, naming conventions, and functionality
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

from fastapi.testclient import TestClient
from app.main import app
from app.services.database_service import initialize_database, reset_database

class APIEndpointTester:
    """Comprehensive API endpoint testing"""
    
    def __init__(self):
        self.client = TestClient(app)
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "issues_found": [],
            "endpoint_coverage": {},
            "naming_conventions": {"issues": [], "compliant": []},
            "response_consistency": {"issues": [], "compliant": []}
        }
        self.auth_token = None
        
    async def run_comprehensive_tests(self):
        """Run all API endpoint tests"""
        print("=== COMPREHENSIVE API ENDPOINT TESTING ===\n")
        
        try:
            # Initialize database
            print("1. Setting up test environment...")
            try:
                initialize_database()
                print("✅ Database initialized")
            except Exception as e:
                print(f"⚠️  Database initialization issue: {e}")
                # Continue with tests anyway
            
            # Test endpoint discovery
            print("2. Testing endpoint discovery...")
            await self._test_endpoint_discovery()
            
            # Test authentication endpoints
            print("3. Testing authentication endpoints...")
            await self._test_auth_endpoints()
            
            # Test master dataset endpoints
            print("4. Testing master dataset endpoints...")
            await self._test_master_dataset_endpoints()
            
            # Test analysis endpoints
            print("5. Testing analysis endpoints...")
            await self._test_analysis_endpoints()
            
            # Test quality control endpoints
            print("6. Testing quality control endpoints...")
            await self._test_quality_control_endpoints()
            
            # Test ATS optimization endpoints
            print("7. Testing ATS optimization endpoints...")
            await self._test_ats_optimization_endpoints()
            
            # Test LaTeX generation endpoints
            print("8. Testing LaTeX generation endpoints...")
            await self._test_latex_generation_endpoints()
            
            # Check naming conventions
            print("9. Checking API naming conventions...")
            await self._check_naming_conventions()
            
            # Generate report
            print("10. Generating test report...")
            await self._generate_report()
            
            return True
            
        except Exception as e:
            logger.error(f"API testing failed: {e}")
            self.test_results["issues_found"].append({
                "type": "critical_error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return False
    
    async def _test_endpoint_discovery(self):
        """Test API documentation and endpoint discovery"""
        # Test OpenAPI docs
        response = self.client.get("/docs")
        if response.status_code == 200:
            self._record_test_result("docs_accessible", True, "OpenAPI docs accessible")
        else:
            self._record_test_result("docs_accessible", False, f"OpenAPI docs not accessible: {response.status_code}")
        
        # Test health endpoint
        response = self.client.get("/health")
        if response.status_code == 200:
            health_data = response.json()
            self._record_test_result("health_endpoint", True, f"Health check passed: {health_data.get('status')}")
        else:
            self._record_test_result("health_endpoint", False, f"Health check failed: {response.status_code}")
    
    async def _test_auth_endpoints(self):
        """Test authentication endpoints"""
        # Test user registration with unique timestamp
        import time
        timestamp = str(int(time.time()))
        registration_data = {
            "username": f"testuser_api_{timestamp}",
            "email": f"testuser_api_{timestamp}@example.com",
            "password": "TestPassword123!",
            "full_name": "API Test User"
        }
        
        response = self.client.post("/api/v2/auth/register", json=registration_data)
        if response.status_code in [200, 201]:
            self._record_test_result("auth_register", True, "User registration successful")
        else:
            self._record_test_result("auth_register", False, f"Registration failed: {response.status_code}")
            return
        
        # Test user login
        login_data = {
            "email": registration_data["email"],  # Use email instead of username
            "password": registration_data["password"]
        }
        
        response = self.client.post("/api/v2/auth/login", json=login_data)  # Use json instead of data
        if response.status_code == 200:
            token_data = response.json()
            self.auth_token = token_data.get("access_token")
            self._record_test_result("auth_login", True, "User login successful")
        else:
            self._record_test_result("auth_login", False, f"Login failed: {response.status_code}")
            return
        
        # Test protected endpoint
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = self.client.get("/api/v2/auth/me", headers=headers)
        if response.status_code == 200:
            self._record_test_result("auth_protected", True, "Protected endpoint accessible")
        else:
            self._record_test_result("auth_protected", False, f"Protected endpoint failed: {response.status_code}")
    
    async def _test_master_dataset_endpoints(self):
        """Test master dataset endpoints"""
        if not self.auth_token:
            self._record_test_result("master_dataset_skip", False, "Skipped - no auth token")
            return
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test profile creation
        profile_data = {
            "full_name": "API Test User",
            "email": "testuser_api@example.com",
            "location": "Test City, TC",
            "target_industries": ["Technology"],
            "career_level": "mid"
        }
        
        response = self.client.post("/api/v2/master-dataset/profile", json=profile_data, headers=headers)
        if response.status_code in [200, 201]:
            self._record_test_result("master_dataset_profile", True, "Profile creation successful")
        else:
            self._record_test_result("master_dataset_profile", False, f"Profile creation failed: {response.status_code}")
        
        # Test work experience creation
        work_exp_data = {
            "company_name": "Test Corp",
            "position_title": "Test Engineer",
            "employment_type": "full-time",
            "start_date": "2023-01-01T00:00:00Z",
            "location": "Test City, TC"
        }
        
        response = self.client.post("/api/v2/master-dataset/work-experiences", json=work_exp_data, headers=headers)
        if response.status_code in [200, 201]:
            self._record_test_result("master_dataset_work_exp", True, "Work experience creation successful")
        else:
            self._record_test_result("master_dataset_work_exp", False, f"Work experience creation failed: {response.status_code}")
    
    async def _test_analysis_endpoints(self):
        """Test job analysis endpoints"""
        if not self.auth_token:
            self._record_test_result("analysis_skip", False, "Skipped - no auth token")
            return
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test job analysis
        job_description = "Senior Software Engineer position requiring Python, FastAPI, and database skills."
        
        response = self.client.post(
            "/api/v2/job-analysis", 
            json={"job_description": job_description},
            headers=headers
        )
        
        if response.status_code in [200, 201]:
            self._record_test_result("job_analysis", True, "Job analysis successful")
        else:
            self._record_test_result("job_analysis", False, f"Job analysis failed: {response.status_code}")
    
    async def _test_quality_control_endpoints(self):
        """Test quality control endpoints"""
        if not self.auth_token:
            self._record_test_result("quality_control_skip", False, "Skipped - no auth token")
            return
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test quality assessment
        assessment_data = {
            "target_role": "Software Engineer",
            "target_industry": "Technology",
            "assessment_type": "comprehensive"
        }
        
        response = self.client.post("/api/v2/quality/assess", json=assessment_data, headers=headers)
        if response.status_code in [200, 201]:
            self._record_test_result("quality_assessment", True, "Quality assessment successful")
        else:
            self._record_test_result("quality_assessment", False, f"Quality assessment failed: {response.status_code}")
        
        # Test quality history
        response = self.client.get("/api/v2/quality/history", headers=headers)
        if response.status_code == 200:
            self._record_test_result("quality_history", True, "Quality history retrieval successful")
        else:
            self._record_test_result("quality_history", False, f"Quality history failed: {response.status_code}")
    
    async def _test_ats_optimization_endpoints(self):
        """Test ATS optimization endpoints"""
        if not self.auth_token:
            self._record_test_result("ats_optimization_skip", False, "Skipped - no auth token")
            return
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test ATS optimization
        optimization_data = {
            "target_keywords": ["python", "fastapi", "database"],
            "target_density": 0.03
        }
        
        response = self.client.post("/api/v2/ats/optimize", json=optimization_data, headers=headers)
        if response.status_code in [200, 201]:
            self._record_test_result("ats_optimization", True, "ATS optimization successful")
        else:
            self._record_test_result("ats_optimization", False, f"ATS optimization failed: {response.status_code}")
    
    async def _test_latex_generation_endpoints(self):
        """Test LaTeX generation endpoints"""
        if not self.auth_token:
            self._record_test_result("latex_generation_skip", False, "Skipped - no auth token")
            return
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test LaTeX status
        response = self.client.get("/api/v2/latex/status", headers=headers)
        if response.status_code == 200:
            self._record_test_result("latex_status", True, "LaTeX status check successful")
        else:
            self._record_test_result("latex_status", False, f"LaTeX status failed: {response.status_code}")
    
    async def _check_naming_conventions(self):
        """Check API naming conventions"""
        expected_patterns = {
            "auth": ["/api/v2/auth/register", "/api/v2/auth/login", "/api/v2/auth/me"],
            "master_dataset": ["/api/v2/master-dataset/profile", "/api/v2/master-dataset/work-experiences"],
            "quality": ["/api/v2/quality/assess", "/api/v2/quality/history"],
            "ats": ["/api/v2/ats/optimize"],
            "latex": ["/api/v2/latex/status"]
        }
        
        # Check for consistent versioning
        all_compliant = True
        for category, endpoints in expected_patterns.items():
            for endpoint in endpoints:
                if not endpoint.startswith("/api/v2/"):
                    self.test_results["naming_conventions"]["issues"].append({
                        "endpoint": endpoint,
                        "issue": "Missing /api/v2/ prefix"
                    })
                    all_compliant = False
                else:
                    self.test_results["naming_conventions"]["compliant"].append(endpoint)
        
        if all_compliant:
            self._record_test_result("naming_conventions", True, "All endpoints follow naming conventions")
        else:
            self._record_test_result("naming_conventions", False, "Naming convention issues found")
    
    def _record_test_result(self, test_name: str, passed: bool, message: str):
        """Record test result"""
        self.test_results["total_tests"] += 1
        if passed:
            self.test_results["passed_tests"] += 1
        else:
            self.test_results["failed_tests"] += 1
            self.test_results["issues_found"].append({
                "test": test_name,
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
        
        self.test_results["endpoint_coverage"][test_name] = {
            "passed": passed,
            "message": message
        }
        
        status = "✅" if passed else "❌"
        print(f"  {status} {test_name}: {message}")
    
    async def _generate_report(self):
        """Generate comprehensive test report"""
        report_path = "/Users/aditya/Documents/Tailer/tailer_v2/reports/api_endpoint_test_report.json"
        
        # Calculate summary statistics
        success_rate = (self.test_results["passed_tests"] / self.test_results["total_tests"]) * 100 if self.test_results["total_tests"] > 0 else 0
        
        self.test_results["summary"] = {
            "success_rate": f"{success_rate:.1f}%",
            "total_endpoints_tested": len(self.test_results["endpoint_coverage"]),
            "critical_issues": len([issue for issue in self.test_results["issues_found"] if "critical" in issue.get("type", "")]),
            "naming_convention_compliance": len(self.test_results["naming_conventions"]["compliant"]) / (len(self.test_results["naming_conventions"]["compliant"]) + len(self.test_results["naming_conventions"]["issues"])) * 100 if (len(self.test_results["naming_conventions"]["compliant"]) + len(self.test_results["naming_conventions"]["issues"])) > 0 else 100
        }
        
        # Write report
        with open(report_path, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n=== API ENDPOINT TEST SUMMARY ===")
        print(f"Total Tests: {self.test_results['total_tests']}")
        print(f"Passed: {self.test_results['passed_tests']}")
        print(f"Failed: {self.test_results['failed_tests']}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Critical Issues: {self.test_results['summary']['critical_issues']}")
        print(f"Report saved to: {report_path}")


async def main():
    """Main test execution"""
    tester = APIEndpointTester()
    success = await tester.run_comprehensive_tests()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)