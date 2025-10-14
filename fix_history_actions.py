#!/usr/bin/env python3
"""
Fix HistoryAction enum mismatches by replacing custom action strings with valid enum values
"""

import re

def fix_history_actions():
    """Replace invalid action strings with valid HistoryAction enum values"""
    
    print("Fixing HistoryAction enum mismatches...")
    
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Map custom action strings to valid enum values
    action_mappings = {
        'action="guidewire_submission_created"': 'action=HistoryAction.UPDATED',
        'action="guidewire_submission_failed"': 'action=HistoryAction.UPDATED', 
        'action="guidewire_submission_error"': 'action=HistoryAction.UPDATED',
        'action="submitted_to_guidewire"': 'action=HistoryAction.UPDATED'
    }
    
    replacements_made = 0
    for old_action, new_action in action_mappings.items():
        old_count = content.count(old_action)
        content = content.replace(old_action, new_action)
        new_count = content.count(old_action)
        replaced = old_count - new_count
        if replaced > 0:
            print(f"   Replaced {replaced} instances of {old_action}")
            replacements_made += replaced
    
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fixed {replacements_made} HistoryAction enum mismatches")
    
    # Verify no invalid action strings remain
    with open('main.py', 'r', encoding='utf-8') as f:
        final_content = f.read()
    
    invalid_actions = re.findall(r'action="[^"]+"', final_content)
    if invalid_actions:
        print(f"⚠️  Still found invalid action strings: {invalid_actions}")
    else:
        print("✅ All action strings now use valid enum values")

if __name__ == "__main__":
    fix_history_actions()