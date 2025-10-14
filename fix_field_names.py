#!/usr/bin/env python3
"""
Quick fix for WorkItemHistory field name mismatches
Replace changed_by with performed_by and add performed_by_name
"""

import re

def fix_workitem_history_fields():
    """Fix WorkItemHistory field names in main.py"""
    
    print("Fixing WorkItemHistory field name mismatches...")
    
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace changed_by="System" with correct fields
    content = re.sub(
        r'changed_by="System"',
        'performed_by="System",\n            performed_by_name="System"',
        content
    )
    
    # Also handle any changed_by variables
    content = re.sub(
        r'changed_by=changed_by',
        'performed_by=changed_by,\n            performed_by_name=changed_by',
        content
    )
    
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fixed WorkItemHistory field names")
    
    # Count how many replacements were made
    with open('main.py', 'r', encoding='utf-8') as f:
        fixed_content = f.read()
    
    performed_by_count = fixed_content.count('performed_by=')
    changed_by_count = fixed_content.count('changed_by=')
    
    print(f"   performed_by instances: {performed_by_count}")
    print(f"   remaining changed_by instances: {changed_by_count}")
    
    if changed_by_count > 0:
        print("⚠️  Some changed_by instances may still need manual fixing")
    else:
        print("✅ All changed_by instances appear to be fixed")

if __name__ == "__main__":
    fix_workitem_history_fields()