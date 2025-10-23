#!/usr/bin/env python3
"""
Create and populate underwriters table with default Senior/Junior underwriters
"""

import sys
sys.path.append('.')
from database import get_db, Underwriter, UnderwriterLevel
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from config import settings

def setup_underwriters_table():
    """Create underwriters table and populate with default data"""
    
    print("🔧 Setting up underwriters table with default data")
    print("=" * 60)
    
    try:
        # Create database connection
        engine = create_engine(settings.database_url)
        db = Session(engine)
        
        # Check if we already have underwriters
        existing_count = db.query(Underwriter).count()
        print(f"Existing underwriters in database: {existing_count}")
        
        if existing_count > 0:
            print("✅ Underwriters table already populated")
            
            # Show existing underwriters
            underwriters = db.query(Underwriter).all()
            print("\nCurrent underwriters:")
            for uw in underwriters:
                print(f"  - {uw.name} ({uw.level.value}) - {uw.email}")
            
            db.close()
            return
        
        # Create default underwriters
        default_underwriters = [
            {
                "name": "Sarah Johnson",
                "email": "sarah.johnson@company.com", 
                "level": UnderwriterLevel.SENIOR,
                "specializations": ["cyber", "technology", "professional_liability"],
                "max_coverage_limit": 10000000.0,  # $10M
                "department": "Cyber Insurance"
            },
            {
                "name": "Michael Chen",
                "email": "michael.chen@company.com",
                "level": UnderwriterLevel.SENIOR, 
                "specializations": ["cyber", "data_breach", "business_interruption"],
                "max_coverage_limit": 15000000.0,  # $15M
                "department": "Cyber Insurance"
            },
            {
                "name": "Emma Wilson",
                "email": "emma.wilson@company.com",
                "level": UnderwriterLevel.JUNIOR,
                "specializations": ["cyber", "small_business"],
                "max_coverage_limit": 2000000.0,  # $2M
                "department": "Cyber Insurance"
            },
            {
                "name": "David Rodriguez", 
                "email": "david.rodriguez@company.com",
                "level": UnderwriterLevel.JUNIOR,
                "specializations": ["cyber", "technology"],
                "max_coverage_limit": 3000000.0,  # $3M
                "department": "Cyber Insurance"
            },
            {
                "name": "Jennifer Liu",
                "email": "jennifer.liu@company.com",
                "level": UnderwriterLevel.PRINCIPAL,
                "specializations": ["cyber", "enterprise", "complex_risks"],
                "max_coverage_limit": 50000000.0,  # $50M
                "department": "Cyber Insurance"
            },
            {
                "name": "Robert Taylor",
                "email": "robert.taylor@company.com",
                "level": UnderwriterLevel.MANAGER,
                "specializations": ["cyber", "management", "escalation"],
                "max_coverage_limit": 100000000.0,  # $100M
                "department": "Cyber Insurance"
            }
        ]
        
        print(f"\n📋 Creating {len(default_underwriters)} default underwriters...")
        
        created_count = 0
        for uw_data in default_underwriters:
            try:
                underwriter = Underwriter(
                    name=uw_data["name"],
                    email=uw_data["email"],
                    level=uw_data["level"],
                    specializations=uw_data["specializations"],
                    max_coverage_limit=uw_data["max_coverage_limit"],
                    department=uw_data["department"],
                    current_workload=0,
                    is_active=True
                )
                
                db.add(underwriter)
                created_count += 1
                print(f"  ✅ Created: {uw_data['name']} ({uw_data['level'].value})")
                
            except Exception as uw_error:
                print(f"  ❌ Failed to create {uw_data['name']}: {uw_error}")
        
        # Commit all changes
        db.commit()
        print(f"\n✅ Successfully created {created_count} underwriters")
        
        # Verify creation
        final_count = db.query(Underwriter).count()
        print(f"Total underwriters in database: {final_count}")
        
        # Show breakdown by level
        levels = db.query(Underwriter.level, Underwriter.name).all()
        level_counts = {}
        for level, name in levels:
            level_key = level.value
            if level_key not in level_counts:
                level_counts[level_key] = []
            level_counts[level_key].append(name)
        
        print("\n📊 Underwriters by level:")
        for level, names in level_counts.items():
            print(f"  {level.upper()}: {len(names)} underwriters")
            for name in names:
                print(f"    - {name}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error setting up underwriters: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = setup_underwriters_table()
    
    if success:
        print("\n🎉 Underwriters setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Deploy the updated database schema")
        print("2. Add underwriter assignment API endpoints") 
        print("3. Update UI to show underwriter selection")
    else:
        print("\n❌ Underwriters setup failed!")
        exit(1)