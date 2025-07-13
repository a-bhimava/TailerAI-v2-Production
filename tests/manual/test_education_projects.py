#!/usr/bin/env python3
"""
Test script for education and project functionality.
Adds sample education and project data to test the new endpoints.
"""

import asyncio
import sys
from datetime import datetime
from uuid import uuid4

# Add the app directory to Python path
sys.path.insert(0, '/Users/aditya/Documents/Tailer/tailer_v2')

from app.services.database_service import db_service
from app.services.master_dataset_service import master_dataset_service
from app.models.database import UserProfile

async def test_education_and_projects():
    """Test education and project functionality."""
    print("🧪 Testing Education and Project Functionality")
    print("=" * 50)
    
    # Initialize database
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
        
        # Test 1: Add education entry
        print("\n🔸 Test 1: Adding education entry")
        education_data = {
            'institution_name': 'University of Example',
            'degree_type': 'Bachelor of Science',
            'field_of_study': 'Computer Science',
            'start_date': datetime(2016, 8, 15),
            'graduation_date': datetime(2020, 5, 15),  # This will map to end_date
            'gpa': 3.8,
            'gpa_scale': 4.0,
            'location': 'Example City, ST',
            'relevant_coursework': ['Data Structures', 'Algorithms', 'Software Engineering'],
            'academic_achievements': ['Dean\'s List', 'Magna Cum Laude'],
            'honors_awards': ['Summa Cum Laude']
        }
        
        education_entry = await master_dataset_service.add_education_entry(
            user_id=test_user_id,
            education_data=education_data
        )
        print(f"✅ Added education entry: {education_entry.institution_name}")
        
        # Test 2: Add project
        print("\n🔸 Test 2: Adding project")
        project_data = {
            'project_name': 'TailerAI Resume Builder',
            'project_type': 'Web Application',
            'project_description': 'AI-powered resume builder with smart content selection',
            'start_date': datetime(2023, 1, 1),
            'end_date': datetime(2024, 6, 1),
            'technologies_used': 'Python, FastAPI, React, SQLAlchemy',
            'project_url': 'https://tailerai.com',
            'repository_url': 'https://github.com/user/tailerai',
            'role': 'Lead Developer',
            'team_size': 3,
            'key_achievements': 'Built scalable architecture, implemented AI content selection',
            'metrics': '10,000+ users, 95% user satisfaction'
        }
        
        project = await master_dataset_service.add_project(
            user_id=test_user_id,
            project_data=project_data
        )
        print(f"✅ Added project: {project.project_name}")
        
        # Test 3: Retrieve education entries
        print("\n🔸 Test 3: Retrieving education entries")
        education_entries = await master_dataset_service.get_education_entries(test_user_id)
        print(f"✅ Retrieved {len(education_entries)} education entries")
        for edu in education_entries:
            print(f"   - {edu.degree_type} in {edu.field_of_study} from {edu.institution_name}")
        
        # Test 4: Retrieve projects
        print("\n🔸 Test 4: Retrieving projects")
        projects = await master_dataset_service.get_projects(test_user_id)
        print(f"✅ Retrieved {len(projects)} projects")
        for proj in projects:
            print(f"   - {proj.project_name} ({proj.project_type})")
        
        # Cleanup
        print("\n🧹 Cleaning up test data")
        with db_service.get_session() as session:
            # Delete test profile (should cascade delete all related data)
            test_profile = session.query(UserProfile).filter_by(user_id=test_user_id).first()
            if test_profile:
                session.delete(test_profile)
                session.commit()
                print("✅ Cleaned up test data")
        
        print("\n🎉 All tests passed! Education and project functionality is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_education_and_projects())
    sys.exit(0 if result else 1)