#!/usr/bin/env python3

import sys
import os
sys.path.append('/Users/aditya/Documents/Tailer/tailer_v2')

from app.services.latex_generation_service import LaTeXGenerationService
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Test data that matches what the frontend sends
test_data = {
    "work_experiences": [
        {
            "experience_id": "1",
            "company_name": "TechCorp",
            "position_title": "Software Engineer",
            "location": "New York, NY",
            "start_date": "2020-01-01",
            "end_date": "2023-01-01",
            "company_description": "Leading technology company",
            "achievements": [
                "Developed scalable web applications",
                "Improved system performance by 25%"
            ]
        }
    ],
    "education": [
        {
            "institution_name": "University of Technology",
            "degree_type": "Bachelor of Science",
            "field_of_study": "Computer Science",
            "location": "Boston, MA",
            "graduation_date": "2019-05-01",
            "gpa": "3.8",
            "gpa_scale": "4.0",
            "relevant_coursework": "Data Structures, Algorithms",
            "academic_achievements": "Dean's List"
        }
    ],
    "skills": [],
    "projects": [],
    "certifications": [],
    "filename_prefix": "test_resume"
}

print("Testing LaTeX generation with debug data...")

try:
    service = LaTeXGenerationService()
    import asyncio
    
    # Run the async function
    async def test():
        result = await service.generate_resume_pdf(
            user_id="test-user-123",
            selected_content=test_data,
            filename_prefix="test_resume"
        )
        return result
    
    result = asyncio.run(test())
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()