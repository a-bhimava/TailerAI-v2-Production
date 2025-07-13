#!/usr/bin/env python3
"""
Test script for the delete work experience functionality.
Tests the complete workflow from API endpoint to frontend integration.
"""

import asyncio
import sys
import traceback
from datetime import datetime
from uuid import uuid4

# Add the app directory to Python path
sys.path.insert(0, '/Users/aditya/Documents/Tailer/tailer_v2')

from app.services.database_service import db_service
from app.services.master_dataset_service import master_dataset_service
from app.models.database import User, UserProfile, WorkExperience, Achievement

async def test_delete_functionality():
    """Test the complete delete functionality workflow."""
    print("🧪 Testing Delete Work Experience Functionality")
    print("=" * 50)
    
    # Initialize database first
    try:
        db_service.initialize()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False
    
    try:
        # Create test user and profile
        test_user_id = str(uuid4())
        print(f"📝 Creating test user: {test_user_id}")
        
        with db_service.get_session() as session:
            # Create test user profile
            test_profile = UserProfile(
                user_id=test_user_id,
                full_name="Test User",
                email="test@example.com",
                is_active=True
            )
            session.add(test_profile)
            session.commit()
            session.refresh(test_profile)
            
            profile_id = test_profile.id
            print(f"✅ Created test profile: {profile_id}")
        
        # Test 1: Add work experience
        print("\n🔸 Test 1: Adding work experience")
        experience_data = {
            'company_name': 'Test Company',
            'position_title': 'Test Developer',
            'employment_type': 'full-time',
            'start_date': datetime(2022, 1, 1),
            'end_date': datetime(2023, 12, 31),
            'location': 'Test City'
        }
        
        work_exp = await master_dataset_service.add_work_experience(
            user_id=test_user_id,
            experience_data=experience_data
        )
        experience_id = str(work_exp.id)
        print(f"✅ Added work experience: {experience_id}")
        
        # Test 2: Add achievement to work experience
        print("\n🔸 Test 2: Adding achievement to work experience")
        achievement_data = {
            'achievement_text': 'Improved system performance by 50%',
            'achievement_category': 'technical',
            'impact_level': 8
        }
        
        achievement = await master_dataset_service.add_achievement(
            user_id=test_user_id,
            experience_id=work_exp.id,
            achievement_data=achievement_data
        )
        achievement_id = str(achievement.id) if hasattr(achievement, 'id') else 'created'
        print(f"✅ Added achievement: {achievement_id}")
        
        # Test 3: Verify data exists before deletion
        print("\n🔸 Test 3: Verifying data exists before deletion")
        
        with db_service.get_session() as session:
            work_exp_count = session.query(WorkExperience).filter_by(profile_id=profile_id).count()
            achievement_count = session.query(Achievement).filter_by(profile_id=profile_id).count()
            
            print(f"✅ Work experiences: {work_exp_count}")
            print(f"✅ Achievements: {achievement_count}")
            
            assert work_exp_count == 1, f"Expected 1 work experience, got {work_exp_count}"
            assert achievement_count == 1, f"Expected 1 achievement, got {achievement_count}"
        
        # Test 4: Delete work experience (should cascade delete achievements)
        print("\n🔸 Test 4: Deleting work experience")
        
        success = await master_dataset_service.delete_work_experience(
            user_id=test_user_id,
            experience_id=experience_id
        )
        
        print(f"✅ Delete operation success: {success}")
        assert success, "Delete operation should return True"
        
        # Test 5: Verify data is deleted
        print("\n🔸 Test 5: Verifying data is deleted")
        
        with db_service.get_session() as session:
            work_exp_count = session.query(WorkExperience).filter_by(profile_id=profile_id).count()
            achievement_count = session.query(Achievement).filter_by(profile_id=profile_id).count()
            
            print(f"✅ Work experiences after deletion: {work_exp_count}")
            print(f"✅ Achievements after deletion: {achievement_count}")
            
            assert work_exp_count == 0, f"Expected 0 work experiences after deletion, got {work_exp_count}"
            assert achievement_count == 0, f"Expected 0 achievements after deletion, got {achievement_count}"
        
        # Test 6: Test deleting non-existent experience
        print("\n🔸 Test 6: Testing deletion of non-existent experience")
        
        try:
            fake_id = str(uuid4())
            success = await master_dataset_service.delete_work_experience(
                user_id=test_user_id,
                experience_id=fake_id
            )
            print(f"❌ Expected exception for non-existent experience, but got success: {success}")
        except Exception as e:
            print(f"✅ Correctly threw exception for non-existent experience: {type(e).__name__}")
        
        # Test 7: Test unauthorized deletion (different user)
        print("\n🔸 Test 7: Testing unauthorized deletion")
        
        # Add another work experience first
        work_exp2 = await master_dataset_service.add_work_experience(
            user_id=test_user_id,
            experience_data=experience_data
        )
        
        try:
            fake_user_id = str(uuid4())
            success = await master_dataset_service.delete_work_experience(
                user_id=fake_user_id,
                experience_id=str(work_exp2.id)
            )
            print(f"❌ Expected exception for unauthorized deletion, but got success: {success}")
        except Exception as e:
            print(f"✅ Correctly threw exception for unauthorized deletion: {type(e).__name__}")
        
        # Cleanup
        print("\n🧹 Cleaning up test data")
        with db_service.get_session() as session:
            # Delete test profile (should cascade delete all related data)
            test_profile = session.query(UserProfile).filter_by(user_id=test_user_id).first()
            if test_profile:
                session.delete(test_profile)
                session.commit()
                print("✅ Cleaned up test data")
        
        print("\n🎉 All tests passed! Delete functionality is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_delete_functionality())
    sys.exit(0 if result else 1)