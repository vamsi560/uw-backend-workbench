#!/usr/bin/env python3
"""
Emergency fix for orphaned submissions in production
Creates work items directly in database for submissions that don't have them
"""

from sqlalchemy import create_engine, text
from config import settings
from datetime import datetime
import json

def fix_orphaned_submissions():
    """Create work items for orphaned submissions directly in database"""
    
    print("🚨 Emergency Fix: Creating work items for orphaned submissions")
    print("=" * 60)
    
    try:
        engine = create_engine(settings.database_url)
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Find orphaned submissions
                result = conn.execute(text("""
                    SELECT s.id, s.submission_id, s.subject, s.sender_email, 
                           s.extracted_fields, s.created_at
                    FROM submissions s
                    LEFT JOIN work_items w ON w.submission_id = s.id
                    WHERE w.id IS NULL
                    ORDER BY s.created_at DESC
                """))
                
                orphaned = result.fetchall()
                
                if not orphaned:
                    print("✅ No orphaned submissions found!")
                    return True
                
                print(f"Found {len(orphaned)} orphaned submissions:")
                
                created_count = 0
                for submission in orphaned:
                    sub_id, submission_id, subject, sender_email, extracted_fields, created_at = submission
                    
                    print(f"\n📧 Processing submission {sub_id}:")
                    print(f"   Subject: {subject}")
                    print(f"   From: {sender_email}")
                    print(f"   Created: {created_at}")
                    
                    # Create work item
                    work_item_data = {
                        'submission_id': sub_id,
                        'title': subject or "Email Submission",
                        'description': f"Email from {sender_email}",
                        'status': 'PENDING',
                        'priority': 'MEDIUM',
                        'created_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    }
                    
                    # Try to extract additional fields from extracted_fields JSON
                    if extracted_fields:
                        try:
                            fields = extracted_fields if isinstance(extracted_fields, dict) else json.loads(extracted_fields)
                            
                            # Set industry if available
                            if fields.get('industry'):
                                work_item_data['industry'] = fields['industry'][:100]  # Limit length
                            
                            # Set policy type if available  
                            policy_type = fields.get('policy_type') or fields.get('coverage_type')
                            if policy_type:
                                work_item_data['policy_type'] = str(policy_type)[:100]
                            
                            # Set coverage amount if available
                            coverage = fields.get('coverage_amount') or fields.get('policy_limit')
                            if coverage:
                                try:
                                    coverage_clean = str(coverage).replace('$', '').replace(',', '')
                                    work_item_data['coverage_amount'] = float(coverage_clean)
                                except:
                                    pass
                                    
                        except Exception as e:
                            print(f"   ⚠️  Could not parse extracted fields: {e}")
                    
                    # Insert work item
                    insert_sql = text("""
                        INSERT INTO work_items (
                            submission_id, title, description, status, priority, 
                            industry, policy_type, coverage_amount, created_at, updated_at
                        ) VALUES (
                            :submission_id, :title, :description, :status, :priority,
                            :industry, :policy_type, :coverage_amount, :created_at, :updated_at
                        ) RETURNING id
                    """)
                    
                    result = conn.execute(insert_sql, work_item_data)
                    work_item_id = result.scalar()
                    
                    # Create history entry
                    history_sql = text("""
                        INSERT INTO work_item_history (
                            work_item_id, action, changed_by, timestamp, details
                        ) VALUES (
                            :work_item_id, 'created', 'Emergency-Fix', :timestamp, :details
                        )
                    """)
                    
                    conn.execute(history_sql, {
                        'work_item_id': work_item_id,
                        'timestamp': datetime.utcnow(),
                        'details': json.dumps({
                            'repair_action': 'Emergency fix for orphaned submission',
                            'submission_ref': submission_id,
                            'original_created_at': created_at.isoformat() if created_at else None
                        })
                    })
                    
                    print(f"   ✅ Created work item {work_item_id}")
                    created_count += 1
                
                # Commit all changes
                trans.commit()
                
                print(f"\n🎉 Successfully created {created_count} work items!")
                
                # Verify the fix
                print("\n📊 Verification:")
                submissions_count = conn.execute(text("SELECT COUNT(*) FROM submissions")).scalar()
                work_items_count = conn.execute(text("SELECT COUNT(*) FROM work_items")).scalar()
                
                print(f"   Submissions: {submissions_count}")
                print(f"   Work items:  {work_items_count}")
                
                if submissions_count == work_items_count:
                    print("   ✅ All submissions now have work items!")
                else:
                    print(f"   ⚠️  Still {submissions_count - work_items_count} orphaned")
                
                return True
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Error during fix: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

if __name__ == "__main__":
    print("Emergency Orphaned Submissions Fix")
    print("This will create work items for submissions without them")
    
    success = fix_orphaned_submissions()
    
    if success:
        print("\n✅ Emergency fix completed successfully!")
        print("\n⚠️  IMPORTANT: Deploy the updated code to prevent future issues!")
    else:
        print("\n❌ Emergency fix failed!")