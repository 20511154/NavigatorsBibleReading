#!/usr/bin/env python3
"""
Script to seed the plan table with reading data from CSV
Usage: python scripts/seed_plan.py path/to/plan.csv
"""

import csv
import sys
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert

from app.config import settings
from app.models import Plan, Base

def seed_plan_from_csv(csv_file_path: str):
    """Seed plan table from CSV file with upsert functionality"""
    
    # Create database connection
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Read CSV and prepare data for upsert
        plan_data = []
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                plan_data.append({
                    'month': int(row['Month']),
                    'day': int(row['Day']),
                    'nt1_book': row['NT1_Book'],
                    'nt1_chapter': row['NT1_Chapter'],
                    'nt2_book': row['NT2_Book'],
                    'nt2_chapter': row['NT2_Chapter'],
                    'ot1_book': row['OT1_Book'],
                    'ot1_chapter': row['OT1_Chapter'],
                    'ot2_book': row['OT2_Book'],
                    'ot2_chapter': row['OT2_Chapter']
                })
        
        # Upsert data using PostgreSQL's ON CONFLICT
        stmt = insert(Plan).values(plan_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=['month', 'day'],
            set_={
                'nt1_book': stmt.excluded.nt1_book,
                'nt1_chapter': stmt.excluded.nt1_chapter,
                'nt2_book': stmt.excluded.nt2_book,
                'nt2_chapter': stmt.excluded.nt2_chapter,
                'ot1_book': stmt.excluded.ot1_book,
                'ot1_chapter': stmt.excluded.ot1_chapter,
                'ot2_book': stmt.excluded.ot2_book,
                'ot2_chapter': stmt.excluded.ot2_chapter
            }
        )
        
        db.execute(stmt)
        db.commit()
        print(f"Successfully seeded plan table with {len(plan_data)} entries from {csv_file_path}")
        
    except Exception as e:
        print(f"Error seeding plan: {e}")
        db.rollback()
        sys.exit(1)
        
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/seed_plan.py path/to/plan.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    seed_plan_from_csv(csv_file)