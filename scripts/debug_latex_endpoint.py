#!/usr/bin/env python3

import requests
import json

# Test the actual API endpoint with the data format it expects
test_data = {
    "work_experiences": [
        {
            "experience_id": "1",
            "company_name": "TechCorp",
            "position_title": "Software Engineer",
            "location": "New York, NY",
            "start_date": "2020-01-01T00:00:00",
            "end_date": "2023-01-01T00:00:00",
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
            "graduation_date": "2019-05-01T00:00:00",
            "gpa": "3.8",
            "gpa_scale": "4.0",
            "relevant_coursework": "Data Structures, Algorithms",
            "academic_achievements": "Dean's List"
        }
    ],
    "skills": [],
    "projects": [],
    "certifications": [],
    "filename_prefix": "debug_resume"
}

print("Testing LaTeX API endpoint...")

try:
    # First get auth token (you'll need to replace this with a valid token)
    # For now, let's just see what happens without auth
    
    url = "http://localhost:8002/api/v2/latex/generate"
    headers = {
        "Content-Type": "application/json",
        # "Authorization": "Bearer YOUR_TOKEN_HERE"  # You'll need to add this
    }
    
    response = requests.post(url, json=test_data, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

except Exception as e:
    print(f"Error making request: {e}")
    import traceback
    traceback.print_exc()