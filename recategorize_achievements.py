#!/usr/bin/env python3
"""
Re-categorize existing achievements using semantic tagging.
This script will update achievements that are currently uncategorized or have empty categories.
"""

import asyncio
import sqlite3
import sys
from pathlib import Path
from typing import List, Dict, Any

def get_uncategorized_achievements() -> List[Dict[str, Any]]:
    """Get achievements that need categorization."""
    
    db_path = Path("data/database/tailer_v2.db")
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return []
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get achievements that need category standardization
        cursor.execute("""
            SELECT 
                a.id,
                a.achievement_text,
                a.achievement_category,
                a.business_function,
                w.position_title,
                w.company_name
            FROM achievements a
            JOIN work_experiences w ON a.experience_id = w.id
            WHERE a.achievement_category IS NULL 
               OR a.achievement_category = '' 
               OR a.achievement_category = 'process'  -- Non-standard category
               OR a.business_function IS NULL 
               OR a.business_function = ''
               OR a.business_function IN ('Product Development', 'Operations', 'Research', 'Design', 'Revenue')  -- Non-standard functions
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        achievements = []
        for row in results:
            achievements.append({
                'id': row[0],
                'text': row[1],
                'current_category': row[2] or '',
                'current_function': row[3] or '',
                'context': f"{row[4]} at {row[5]}" if row[4] and row[5] else ''
            })
        
        return achievements
        
    except Exception as e:
        print(f"Error reading achievements: {e}")
        return []

def categorize_achievement_rule_based(text: str, current_category: str = '', current_function: str = '') -> tuple:
    """Standardize and improve categorization."""
    
    text_lower = text.lower()
    
    # Standardize existing categories first
    category_mapping = {
        'process': 'operational',
        'strategic': 'strategic',
        'leadership': 'leadership', 
        'technical': 'technical',
        'financial': 'financial',
        'operational': 'operational'
    }
    
    function_mapping = {
        'Product Development': 'product',
        'Operations': 'operations',
        'Research': 'data_science',
        'Design': 'design',
        'Revenue': 'sales',
        'General': 'general'
    }
    
    # Use current category if it's valid, otherwise classify
    if current_category in category_mapping:
        final_category = category_mapping[current_category]
    else:
        # Technical keywords
        if any(word in text_lower for word in ['developed', 'built', 'implemented', 'coded', 'system', 'api', 'database', 'software', 'dashboard', 'analytics', 'interface']):
            final_category = 'technical'
        # Leadership keywords  
        elif any(word in text_lower for word in ['led', 'managed', 'mentored', 'team', 'supervised', 'directed', 'cross-functional']):
            final_category = 'leadership'
        # Financial keywords
        elif any(word in text_lower for word in ['revenue', 'sales', 'profit', 'cost', 'savings', '$', 'million', 'thousand', 'arr']):
            final_category = 'financial'
        # Strategic keywords
        elif any(word in text_lower for word in ['strategy', 'research', 'roadmap', 'vision', 'planning']):
            final_category = 'strategic'
        # Operational keywords
        elif any(word in text_lower for word in ['improved', 'optimized', 'streamlined', 'efficiency', 'process', 'methodology', 'agile']):
            final_category = 'operational'
        # Customer keywords
        elif any(word in text_lower for word in ['customer', 'client', 'user', 'satisfaction', 'service', 'engagement', 'usability']):
            final_category = 'customer'
        else:
            final_category = 'operational'
    
    # Use current function if it's mappable, otherwise classify
    if current_function in function_mapping:
        final_function = function_mapping[current_function]
    else:
        # Classify based on text
        if any(word in text_lower for word in ['engineering', 'development', 'technical', 'software', 'system', 'api']):
            final_function = 'engineering'
        elif any(word in text_lower for word in ['product', 'feature', 'roadmap', 'user']):
            final_function = 'product'
        elif any(word in text_lower for word in ['design', 'interface', 'user interface', 'ux', 'ui']):
            final_function = 'design'
        elif any(word in text_lower for word in ['revenue', 'sales', 'arr', 'financial']):
            final_function = 'sales'
        elif any(word in text_lower for word in ['research', 'analytics', 'data', 'testing']):
            final_function = 'data_science'
        elif any(word in text_lower for word in ['operations', 'process', 'methodology', 'agile']):
            final_function = 'operations'
        else:
            final_function = 'general'
    
    return final_category, final_function

def update_achievement_categories(categorizations: List[Dict[str, Any]]) -> bool:
    """Update achievements in the database with new categories."""
    
    db_path = Path("data/database/tailer_v2.db")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        updated_count = 0
        
        for item in categorizations:
            cursor.execute("""
                UPDATE achievements 
                SET achievement_category = ?, business_function = ? 
                WHERE id = ?
            """, (item['category'], item['function'], item['id']))
            updated_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"✅ Updated {updated_count} achievements with semantic categorization")
        return True
        
    except Exception as e:
        print(f"Error updating achievements: {e}")
        return False

async def main():
    """Main function to re-categorize achievements."""
    
    print("=== ACHIEVEMENT SEMANTIC CATEGORIZATION ===")
    print("Re-categorizing existing achievements with semantic tags")
    print()
    
    # Get uncategorized achievements
    print("1. 🔍 Finding uncategorized achievements...")
    achievements = get_uncategorized_achievements()
    
    if not achievements:
        print("✅ No uncategorized achievements found!")
        return
    
    print(f"   Found {len(achievements)} achievements needing categorization")
    print()
    
    # Categorize achievements
    print("2. 🏷️ Categorizing achievements...")
    categorizations = []
    
    for i, achievement in enumerate(achievements, 1):
        print(f"   Processing {i}/{len(achievements)}: {achievement['text'][:60]}...")
        
        # Use rule-based categorization with current values for standardization
        category, function = categorize_achievement_rule_based(
            achievement['text'], 
            achievement['current_category'], 
            achievement['current_function']
        )
        
        categorizations.append({
            'id': achievement['id'],
            'text': achievement['text'],
            'category': category,
            'function': function,
            'context': achievement['context']
        })
        
        print(f"     → Category: {category}, Function: {function}")
    
    print()
    
    # Show categorization summary
    print("3. 📊 Categorization Summary:")
    category_counts = {}
    function_counts = {}
    
    for item in categorizations:
        category_counts[item['category']] = category_counts.get(item['category'], 0) + 1
        function_counts[item['function']] = function_counts.get(item['function'], 0) + 1
    
    print("   Categories:")
    for category, count in sorted(category_counts.items()):
        print(f"     • {category}: {count} achievements")
    
    print("   Business Functions:")
    for function, count in sorted(function_counts.items()):
        print(f"     • {function}: {count} achievements")
    
    print()
    
    # Update database
    print("4. 💾 Updating database...")
    success = update_achievement_categories(categorizations)
    
    if success:
        print("✅ Achievement categorization completed successfully!")
        print()
        print("🎉 SEMANTIC TAGGING IMPLEMENTED!")
        print("   • All achievements now have semantic categories")
        print("   • Business functions assigned for better organization")
        print("   • Future achievements will be auto-categorized using AI")
        print()
        print("📝 Next Steps:")
        print("   • Test achievement creation with new categorization")
        print("   • Verify categories appear in resume generation")
        print("   • Consider training custom categorization model")
    else:
        print("❌ Failed to update achievement categories")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())