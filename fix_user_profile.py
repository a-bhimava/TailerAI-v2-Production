#!/usr/bin/env python3
"""
Fix the current user's profile to include complete contact information.
This demonstrates the contact header fix by ensuring the user has all required fields.
"""

import sqlite3
import sys
from pathlib import Path

def update_user_profile():
    """Update the user profile with complete contact information."""
    
    # Database path
    db_path = Path("data/database/tailer_v2.db")
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current user profile
        cursor.execute("SELECT id, full_name, email, phone, linkedin_url, location FROM user_profiles LIMIT 1")
        current_user = cursor.fetchone()
        
        if not current_user:
            print("No user profile found in database")
            return False
        
        user_id, full_name, email, phone, linkedin_url, location = current_user
        
        print("=== CURRENT USER PROFILE ===")
        print(f"ID: {user_id}")
        print(f"Name: {full_name}")
        print(f"Email: {email}")
        print(f"Phone: {phone or 'NOT SET'}")
        print(f"LinkedIn: {linkedin_url or 'NOT SET'}")
        print(f"Location: {location or 'NOT SET'}")
        print()
        
        # Update with complete contact information
        updated_phone = phone or "+1-412-287-1018"
        updated_linkedin = linkedin_url or "https://linkedin.com/in/aditya-teja"
        updated_location = location or "Pittsburgh, PA"
        
        # Update the user profile
        cursor.execute("""
            UPDATE user_profiles 
            SET phone = ?, linkedin_url = ?, location = ?
            WHERE id = ?
        """, (updated_phone, updated_linkedin, updated_location, user_id))
        
        conn.commit()
        
        # Verify the update
        cursor.execute("SELECT full_name, email, phone, linkedin_url, location FROM user_profiles WHERE id = ?", (user_id,))
        updated_user = cursor.fetchone()
        
        print("=== UPDATED USER PROFILE ===")
        print(f"Name: {updated_user[0]}")
        print(f"Email: {updated_user[1]}")
        print(f"Phone: {updated_user[2]}")
        print(f"LinkedIn: {updated_user[3]}")
        print(f"Location: {updated_user[4]}")
        print()
        
        # Simulate header construction
        header_parts = []
        if updated_user[2]:  # phone
            header_parts.append(updated_user[2])
        if updated_user[1]:  # email
            header_parts.append(updated_user[1])
        if updated_user[3]:  # linkedin
            linkedin_display = updated_user[3].replace("https://", "").replace("http://", "")
            header_parts.append(linkedin_display)
        if updated_user[4]:  # location
            header_parts.append(updated_user[4])
        
        header_line = " $|$ ".join(header_parts)
        
        print("=== EXPECTED RESUME HEADER ===")
        print(f"{updated_user[0].upper()}")
        print(f"{header_line}")
        print()
        print("✅ User profile updated successfully!")
        print("✅ Header should now display all contact information")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error updating user profile: {e}")
        return False

if __name__ == "__main__":
    success = update_user_profile()
    if success:
        print("\n🎉 Contact header fix applied!")
        print("Generate a resume to see the complete contact header.")
    else:
        print("\n❌ Failed to apply contact header fix.")
        sys.exit(1)