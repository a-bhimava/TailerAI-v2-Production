#!/usr/bin/env python3
"""
Debug script to test contact header formatting issue.
Tests the header line construction logic in isolation.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.latex_generation_service import LaTeXGenerationService
from app.models.database import UserProfile

def test_header_construction():
    """Test the header line construction logic."""
    
    # Create a test user profile with all contact information
    test_profile = UserProfile(
        id="test-user-id",
        user_id="test-user",
        full_name="Alex Johnson",
        email="alex.johnson@email.com",
        phone="+1-555-123-4567",
        linkedin_url="https://linkedin.com/in/alexjohnson",
        location="San Francisco, CA"
    )
    
    # Create service instance
    latex_service = LaTeXGenerationService()
    
    # Test the header construction logic manually
    print("=== TESTING CONTACT HEADER CONSTRUCTION ===")
    print(f"User Profile:")
    print(f"  Name: {test_profile.full_name}")
    print(f"  Email: {test_profile.email}")
    print(f"  Phone: {test_profile.phone}")
    print(f"  LinkedIn: {test_profile.linkedin_url}")
    print(f"  Location: {test_profile.location}")
    print()
    
    # Manually replicate the header construction logic
    full_name = latex_service._escape_latex_characters(test_profile.full_name or "Your Name")
    email = latex_service._escape_latex_characters(test_profile.email)
    phone = latex_service._escape_latex_characters(test_profile.phone or "")
    linkedin_url = latex_service._escape_latex_characters(test_profile.linkedin_url or "")
    location = latex_service._escape_latex_characters(test_profile.location or "")
    
    print("=== ESCAPED VALUES ===")
    print(f"  Full Name: '{full_name}'")
    print(f"  Email: '{email}'")
    print(f"  Phone: '{phone}'")
    print(f"  LinkedIn: '{linkedin_url}'")
    print(f"  Location: '{location}'")
    print()
    
    # Build header
    header_parts = []
    if phone:
        header_parts.append(phone)
        print(f"Added phone: '{phone}'")
    if email:
        header_parts.append(email)
        print(f"Added email: '{email}'")
    if linkedin_url:
        # Extract just the username part from LinkedIn URL
        linkedin_display = linkedin_url.replace("https://", "").replace("http://", "")
        header_parts.append(linkedin_display)
        print(f"Added LinkedIn: '{linkedin_display}'")
    if location:
        header_parts.append(location)
        print(f"Added location: '{location}'")
    
    header_line = " $|$ ".join(header_parts)
    
    print("=== FINAL HEADER CONSTRUCTION ===")
    print(f"Header parts: {header_parts}")
    print(f"Header line: '{header_line}'")
    print()
    
    print("=== EXPECTED RESULT ===")
    expected = "+1-555-123-4567 $|$ alex.johnson@email.com $|$ linkedin.com/in/alexjohnson $|$ San Francisco, CA"
    print(f"Expected: '{expected}'")
    print(f"Actual:   '{header_line}'")
    print(f"Match: {header_line == expected}")
    
    # Test with missing fields
    print("\n=== TESTING WITH MISSING PHONE ===")
    test_profile_no_phone = UserProfile(
        id="test-user-id-2",
        user_id="test-user-2",
        full_name="Jane Doe",
        email="jane.doe@email.com",
        phone="",  # Empty phone
        linkedin_url="https://linkedin.com/in/janedoe",
        location="New York, NY"
    )
    
    phone_missing = latex_service._escape_latex_characters(test_profile_no_phone.phone or "")
    email_missing = latex_service._escape_latex_characters(test_profile_no_phone.email)
    linkedin_missing = latex_service._escape_latex_characters(test_profile_no_phone.linkedin_url or "")
    location_missing = latex_service._escape_latex_characters(test_profile_no_phone.location or "")
    
    header_parts_missing = []
    if phone_missing:
        header_parts_missing.append(phone_missing)
    if email_missing:
        header_parts_missing.append(email_missing)
    if linkedin_missing:
        linkedin_display_missing = linkedin_missing.replace("https://", "").replace("http://", "")
        header_parts_missing.append(linkedin_display_missing)
    if location_missing:
        header_parts_missing.append(location_missing)
    
    header_line_missing = " $|$ ".join(header_parts_missing)
    print(f"Header with missing phone: '{header_line_missing}'")
    
    return header_line

if __name__ == "__main__":
    test_header_construction()