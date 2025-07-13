#!/usr/bin/env python3

import sys
import os
sys.path.append('/Users/aditya/Documents/Tailer/tailer_v2')

from app.services.latex_generation_service import LaTeXGenerationService
import tempfile
import subprocess

# Mock user profile that matches what the API would send
class MockUserProfile:
    def __init__(self):
        self.full_name = "Test User"
        self.email = "test@example.com"
        self.phone = "123-456-7890"
        self.linkedin_url = "https://linkedin.com/in/testuser"
        self.location = "Test City, State"

# Test data that matches frontend format
selected_content = {
    "work_experiences": [
        {
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
    "certifications": []
}

print("Testing LaTeX template generation...")

try:
    service = LaTeXGenerationService()
    user_profile = MockUserProfile()
    
    # Generate the LaTeX template
    latex_content = service._create_dynamic_template(user_profile, selected_content)
    
    print(f"Generated LaTeX content ({len(latex_content)} characters):")
    print("="*50)
    print(latex_content)
    print("="*50)
    
    # Try to compile it
    print("\nTesting LaTeX compilation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        tex_file = os.path.join(temp_dir, "test.tex")
        
        # Write LaTeX content
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        
        # Try to compile
        result = subprocess.run(
            ['/Library/TeX/texbin/pdflatex', '-interaction=nonstopmode', 'test.tex'],
            cwd=temp_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(f"Return code: {result.returncode}")
        
        if result.returncode != 0:
            print("COMPILATION FAILED!")
            print(f"STDERR: {result.stderr}")
            print(f"STDOUT: {result.stdout}")
            
            # Look for specific errors
            lines = result.stderr.split('\n') + result.stdout.split('\n')
            for line in lines:
                if "LaTeX Error:" in line or "!" in line:
                    print(f"ERROR: {line}")
        else:
            # Check if PDF was created
            pdf_file = os.path.join(temp_dir, "test.pdf")
            if os.path.exists(pdf_file):
                print(f"✅ PDF created successfully!")
                print(f"PDF size: {os.path.getsize(pdf_file)} bytes")
            else:
                print("❌ PDF was not created despite return code 0")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()