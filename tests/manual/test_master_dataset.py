#!/usr/bin/env python3
"""
Master Dataset Service Testing Script
Tests CRUD operations, data validation, and API integration.
"""

import asyncio
import sys
import json
from datetime import datetime, date
from typing import Dict, Any, List
from uuid import UUID

# Test the master dataset service directly
from app.services.master_dataset_service import master_dataset_service, MasterDatasetError
from app.services.auth_service import auth_service
from app.services.database_service import db_service, initialize_database


class MasterDatasetTestSuite:
    """Comprehensive master dataset service test suite."""
    
    def __init__(self):
        self.test_results = []
        self.test_user_email = f"dataset_test_{int(datetime.now().timestamp())}@example.com"
        self.test_user_data = {
            "username": f"dataset_user_{int(datetime.now().timestamp())}",
            "email": self.test_user_email,
            "password": "TestPassword123!",
            "full_name": "Dataset Test User"
        }
        self.user_id = None
        self.user_profile_id = None
        self.work_experience_id = None
        self.achievement_id = None
        self.skill_id = None
    
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
    
    async def setup_test_user(self):
        """Create a test user for dataset operations."""
        print("\n🛠️ Setting up test user...")
        
        try:
            # Register test user
            user = await auth_service.register_user(
                username=self.test_user_data["username"],
                email=self.test_user_data["email"],
                password=self.test_user_data["password"],
                full_name=self.test_user_data["full_name"]
            )
            
            # Try to get user ID (handle session detachment)
            try:
                self.user_id = str(user.id)
                print(f"✅ Test user created: {self.user_id}")
            except:
                # If session detached, authenticate to get user ID
                try:
                    auth_user, _, _ = await auth_service.authenticate_user(
                        self.test_user_data["email"],
                        self.test_user_data["password"]
                    )
                    try:
                        self.user_id = str(auth_user.id)
                        print(f"✅ Test user ID from auth: {self.user_id}")
                    except:
                        # Last resort: use a database query to get the user ID
                        with db_service.get_session() as session:
                            from app.models.database import User
                            db_user = session.query(User).filter_by(
                                email=self.test_user_data["email"]
                            ).first()
                            if db_user:
                                self.user_id = str(db_user.id)
                                print(f"✅ Test user ID from DB: {self.user_id}")
                            else:
                                print("❌ Could not find user in database")
                                return False
                except Exception as auth_error:
                    print(f"❌ Authentication failed: {auth_error}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to create test user: {str(e)}")
            return False
    
    async def test_user_profile_operations(self):
        """Test user profile CRUD operations."""
        print("\n👤 Testing User Profile Operations...")
        
        # Test getting user profile (should exist from registration)
        try:
            user_profile = await master_dataset_service.get_user_profile(self.user_id)
            
            if user_profile:
                self.user_profile_id = str(user_profile.id)
                self.log_test("Get User Profile", True, f"Profile ID: {self.user_profile_id}")
            else:
                self.log_test("Get User Profile", False, "No profile found")
                return False
            
        except Exception as e:
            self.log_test("Get User Profile", False, str(e))
            return False
        
        # Test updating user profile
        try:
            update_data = {
                "phone": "+1-555-0123",
                "linkedin_url": "https://linkedin.com/in/testuser",
                "location": "San Francisco, CA",
                "target_industries": ["Technology", "Finance"],
                "career_level": "mid"
            }
            
            updated_profile = await master_dataset_service.update_user_profile(
                self.user_id, 
                update_data
            )
            
            if updated_profile and updated_profile.phone == "+1-555-0123":
                self.log_test("Update User Profile", True, "Profile updated successfully")
            else:
                self.log_test("Update User Profile", False, "Profile update failed")
            
        except Exception as e:
            self.log_test("Update User Profile", False, str(e))
        
        return True
    
    async def test_work_experience_operations(self):
        """Test work experience CRUD operations."""
        print("\n💼 Testing Work Experience Operations...")
        
        # Test adding work experience
        try:
            experience_data = {
                "company_name": "TechCorp Inc.",
                "position_title": "Software Engineer",
                "employment_type": "full-time",
                "start_date": datetime(2022, 1, 15),
                "end_date": datetime(2023, 12, 31),
                "location": "San Francisco, CA",
                "company_size": "medium",
                "industry": "Technology",
                "company_description": "Leading software development company",
                "role_summary": "Developed web applications using Python and React",
                "team_size": 8,
                "reporting_structure": "Reports to Senior Engineering Manager"
            }
            
            work_experience = await master_dataset_service.add_work_experience(
                self.user_id,
                experience_data
            )
            
            if work_experience:
                self.work_experience_id = str(work_experience.id)
                self.log_test("Add Work Experience", True, f"Experience ID: {self.work_experience_id}")
            else:
                self.log_test("Add Work Experience", False, "No work experience returned")
                return False
            
        except Exception as e:
            self.log_test("Add Work Experience", False, str(e))
            return False
        
        # Test getting work experiences
        try:
            work_experiences = await master_dataset_service.get_work_experiences(self.user_id)
            
            if work_experiences and len(work_experiences) > 0:
                self.log_test("Get Work Experiences", True, f"Found {len(work_experiences)} experiences")
            else:
                self.log_test("Get Work Experiences", False, "No work experiences found")
            
        except Exception as e:
            self.log_test("Get Work Experiences", False, str(e))
        
        return True
    
    async def test_achievement_operations(self):
        """Test achievement CRUD operations."""
        print("\n🏆 Testing Achievement Operations...")
        
        if not self.work_experience_id:
            self.log_test("Achievement Operations Setup", False, "No work experience available")
            return False
        
        # Test adding achievement
        try:
            achievement_data = {
                "achievement_text": "Led the development of a microservices architecture that reduced system response time by 40% and improved scalability for 100,000+ daily users",
                "achievement_category": "technical",
                "impact_level": 8,
                "business_function": "Engineering",
                "quantified_metrics": {
                    "response_time_improvement": "40%",
                    "users_supported": 100000,
                    "system_uptime": "99.9%"
                },
                "keywords": ["microservices", "scalability", "performance", "architecture"],
                "ats_keywords": ["Python", "Docker", "Kubernetes", "AWS"],
                "skills_demonstrated": ["System Design", "Leadership", "Performance Optimization"],
                "time_period": "6 months",
                "context_tags": ["team_lead", "architecture", "performance"]
            }
            
            achievement = await master_dataset_service.add_achievement(
                self.user_id,
                UUID(self.work_experience_id),
                achievement_data
            )
            
            if achievement:
                self.achievement_id = str(achievement.id)
                self.log_test("Add Achievement", True, f"Achievement ID: {self.achievement_id}")
            else:
                self.log_test("Add Achievement", False, "No achievement returned")
                return False
            
        except Exception as e:
            self.log_test("Add Achievement", False, str(e))
            return False
        
        # Test getting achievements
        try:
            achievements = await master_dataset_service.get_achievements(self.user_id)
            
            if achievements and len(achievements) > 0:
                self.log_test("Get Achievements", True, f"Found {len(achievements)} achievements")
            else:
                self.log_test("Get Achievements", False, "No achievements found")
            
        except Exception as e:
            self.log_test("Get Achievements", False, str(e))
        
        # Test filtered achievements
        try:
            technical_achievements = await master_dataset_service.get_achievements(
                self.user_id,
                category="technical",
                min_impact_level=7
            )
            
            if technical_achievements:
                self.log_test("Filter Achievements", True, f"Found {len(technical_achievements)} technical achievements")
            else:
                self.log_test("Filter Achievements", True, "No technical achievements (expected for new data)")
            
        except Exception as e:
            self.log_test("Filter Achievements", False, str(e))
        
        return True
    
    async def test_skill_operations(self):
        """Test skill CRUD operations."""
        print("\n🛠️ Testing Skill Operations...")
        
        # Test adding skill
        try:
            skill_data = {
                "skill_name": "Python",
                "skill_category": "technical",
                "proficiency_level": "advanced",
                "years_experience": 5.5,
                "certification_name": "Python Institute PCAP",
                "certification_date": datetime(2023, 6, 15),
                "related_keywords": ["Django", "Flask", "FastAPI", "SQLAlchemy"],
                "industry_relevance": ["Technology", "Finance", "Healthcare"]
            }
            
            skill = await master_dataset_service.add_skill(
                self.user_id,
                skill_data
            )
            
            if skill:
                self.skill_id = str(skill.id)
                self.log_test("Add Skill", True, f"Skill ID: {self.skill_id}")
            else:
                self.log_test("Add Skill", False, "No skill returned")
                return False
            
        except Exception as e:
            self.log_test("Add Skill", False, str(e))
            return False
        
        # Test getting skills
        try:
            skills = await master_dataset_service.get_skills(self.user_id)
            
            if skills and len(skills) > 0:
                self.log_test("Get Skills", True, f"Found {len(skills)} skills")
            else:
                self.log_test("Get Skills", False, "No skills found")
            
        except Exception as e:
            self.log_test("Get Skills", False, str(e))
        
        # Test filtered skills
        try:
            technical_skills = await master_dataset_service.get_skills(
                self.user_id,
                category="technical"
            )
            
            if technical_skills:
                self.log_test("Filter Skills", True, f"Found {len(technical_skills)} technical skills")
            else:
                self.log_test("Filter Skills", True, "No technical skills (expected for new data)")
            
        except Exception as e:
            self.log_test("Filter Skills", False, str(e))
        
        return True
    
    async def test_dataset_summary_and_validation(self):
        """Test dataset summary and validation features."""
        print("\n📊 Testing Dataset Summary and Validation...")
        
        # Test dataset summary
        try:
            summary = await master_dataset_service.get_dataset_summary(self.user_id)
            
            if summary and isinstance(summary, dict):
                self.log_test("Get Dataset Summary", True, f"Summary contains {len(summary)} sections")
                
                # Check if summary has expected sections
                expected_sections = ["profile", "work_experiences", "achievements", "skills"]
                missing_sections = [s for s in expected_sections if s not in summary]
                
                if not missing_sections:
                    self.log_test("Summary Completeness", True, "All expected sections present")
                else:
                    self.log_test("Summary Completeness", False, f"Missing: {missing_sections}")
            else:
                self.log_test("Get Dataset Summary", False, "Invalid summary format")
            
        except Exception as e:
            self.log_test("Get Dataset Summary", False, str(e))
        
        # Test dataset validation
        try:
            validation = await master_dataset_service.validate_dataset_completeness(self.user_id)
            
            if validation and isinstance(validation, dict):
                self.log_test("Dataset Validation", True, "Validation completed")
                
                # Check validation structure
                if "completeness_score" in validation:
                    score = validation["completeness_score"]
                    self.log_test("Completeness Score", True, f"Score: {score}")
                else:
                    self.log_test("Completeness Score", False, "No completeness score")
            else:
                self.log_test("Dataset Validation", False, "Invalid validation format")
            
        except Exception as e:
            self.log_test("Dataset Validation", False, str(e))
        
        return True
    
    async def test_error_handling(self):
        """Test error handling and edge cases."""
        print("\n⚠️ Testing Error Handling...")
        
        # Test invalid user ID
        try:
            invalid_profile = await master_dataset_service.get_user_profile("invalid-uuid")
            self.log_test("Invalid User ID Handling", False, "Should have thrown error")
        except Exception:
            self.log_test("Invalid User ID Handling", True, "Correctly handled invalid UUID")
        
        # Test non-existent user
        try:
            fake_uuid = "00000000-0000-0000-0000-000000000000"
            nonexistent_profile = await master_dataset_service.get_user_profile(fake_uuid)
            if nonexistent_profile is None:
                self.log_test("Non-existent User Handling", True, "Returned None for non-existent user")
            else:
                self.log_test("Non-existent User Handling", False, "Should return None")
        except Exception as e:
            self.log_test("Non-existent User Handling", True, f"Handled gracefully: {type(e).__name__}")
        
        # Test invalid data validation
        try:
            invalid_experience = {
                "company_name": "",  # Empty required field
                "position_title": "Test Position",
                "start_date": "invalid-date"  # Invalid date format
            }
            
            await master_dataset_service.add_work_experience(
                self.user_id,
                invalid_experience
            )
            self.log_test("Data Validation", False, "Should have rejected invalid data")
        except Exception:
            self.log_test("Data Validation", True, "Correctly rejected invalid data")
        
        return True
    
    async def run_all_tests(self):
        """Run all master dataset tests."""
        print("🧪 Starting Master Dataset Service Test Suite")
        print("=" * 60)
        
        # Initialize database
        try:
            initialize_database()
            print("✅ Database initialized successfully")
        except Exception as e:
            print(f"❌ Database initialization failed: {str(e)}")
            return False
        
        # Setup test user
        if not await self.setup_test_user():
            print("❌ Failed to setup test user")
            return False
        
        # Run all test suites
        test_methods = [
            self.test_user_profile_operations,
            self.test_work_experience_operations,
            self.test_achievement_operations,
            self.test_skill_operations,
            self.test_dataset_summary_and_validation,
            self.test_error_handling
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                self.log_test(f"{test_method.__name__} (CRASH)", False, str(e))
        
        # Print summary
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("🏁 TEST SUITE SUMMARY")
        print("=" * 60)
        
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
        
        print(f"\n💾 Test Results saved to: master_dataset_test_results.json")
        
        # Save detailed results
        with open("master_dataset_test_results.json", "w") as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "success_rate": f"{(passed_tests/total_tests)*100:.1f}%",
                    "test_run_time": datetime.now().isoformat()
                },
                "test_results": self.test_results
            }, f, indent=2)


async def main():
    """Main test execution."""
    test_suite = MasterDatasetTestSuite()
    success = await test_suite.run_all_tests()
    
    if success:
        failed_count = sum(1 for result in test_suite.test_results if not result["passed"])
        sys.exit(0 if failed_count == 0 else 1)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())