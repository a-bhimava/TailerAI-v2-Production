#!/usr/bin/env python3
"""
Simple test to verify contact header construction logic.
"""

def escape_latex_characters(text):
    """Simple LaTeX character escaping."""
    if not text:
        return ""
    
    # Basic escaping
    replacements = {
        '&': '\\&',
        '%': '\\%',  
        '$': '\\$',
        '#': '\\#',
        '^': '\\textasciicircum{}',
        '_': '\\_',
        '{': '\\{',
        '}': '\\}',
        '~': '\\textasciitilde{}', 
        '\\': '\\textbackslash{}'
    }
    
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    
    return text

def test_header_construction():
    """Test the header line construction logic."""
    
    print("=== TESTING CONTACT HEADER CONSTRUCTION ===")
    
    # Test case 1: All fields present
    test_cases = [
        {
            "name": "All fields present",
            "full_name": "Alex Johnson",
            "email": "alex.johnson@email.com",
            "phone": "+1-555-123-4567",
            "linkedin_url": "https://linkedin.com/in/alexjohnson",
            "location": "San Francisco, CA"
        },
        {
            "name": "Missing phone",
            "full_name": "Jane Doe",
            "email": "jane.doe@email.com", 
            "phone": "",
            "linkedin_url": "https://linkedin.com/in/janedoe",
            "location": "New York, NY"
        },
        {
            "name": "Only email",
            "full_name": "John Smith",
            "email": "john.smith@email.com",
            "phone": "",
            "linkedin_url": "",
            "location": ""
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n=== TEST CASE {i}: {test_case['name']} ===")
        
        # Escape all fields
        full_name = escape_latex_characters(test_case['full_name'] or "Your Name")
        email = escape_latex_characters(test_case['email'])
        phone = escape_latex_characters(test_case['phone'] or "")
        linkedin_url = escape_latex_characters(test_case['linkedin_url'] or "")
        location = escape_latex_characters(test_case['location'] or "")
        
        print(f"Input values:")
        print(f"  Name: '{test_case['full_name']}'")
        print(f"  Email: '{test_case['email']}'")
        print(f"  Phone: '{test_case['phone']}'")
        print(f"  LinkedIn: '{test_case['linkedin_url']}'")
        print(f"  Location: '{test_case['location']}'")
        
        # Build header using the same logic as the service
        header_parts = []
        if phone:
            header_parts.append(phone)
            print(f"✓ Added phone: '{phone}'")
        if email:
            header_parts.append(email)
            print(f"✓ Added email: '{email}'")
        if linkedin_url:
            # Extract just the username part from LinkedIn URL
            linkedin_display = linkedin_url.replace("https://", "").replace("http://", "")
            header_parts.append(linkedin_display)
            print(f"✓ Added LinkedIn: '{linkedin_display}'")
        if location:
            header_parts.append(location)
            print(f"✓ Added location: '{location}'")
        
        header_line = " $|$ ".join(header_parts)
        
        print(f"Final header line: '{header_line}'")
        print(f"LaTeX template line: {{{full_name.upper()}}} \\\\ {header_line}")
        
        # Check if this would show only email (the reported issue)
        if header_line == email:
            print("⚠️  WARNING: Header line is only email - this is the bug!")
        else:
            print("✅ Header line contains multiple fields")

if __name__ == "__main__":
    test_header_construction()