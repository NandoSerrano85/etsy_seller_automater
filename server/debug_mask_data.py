#!/usr/bin/env python3
"""
Debug script to check mask data in the database.
"""

import sys
import os

# Add the server directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from server.api.models import MockupMaskData, User
from server.engine.mask_db_utils import inspect_mask_data

def main():
    """Check mask data in the database."""
    
    # Database connection
    DATABASE_URL = "postgresql://postgres:password@localhost:5432/etsy_automater"
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Get all users
        users = db.query(User).all()
        print(f"Found {len(users)} users in database")
        
        for user in users:
            print(f"\n=== User {user.id} ({user.email}) ===")
            
            # Get all mask data for this user
            mask_data_list = db.query(MockupMaskData).filter(
                MockupMaskData.user_id == user.id
            ).all()
            
            if not mask_data_list:
                print("  No mask data found")
                continue
            
            for mask_data in mask_data_list:
                print(f"\n  Template: {mask_data.template_name}")
                print(f"  Starting name: {mask_data.starting_name}")
                print(f"  Created: {mask_data.created_at}")
                print(f"  Updated: {mask_data.updated_at}")
                print(f"  Masks count: {len(mask_data.masks) if mask_data.masks else 0}")
                print(f"  Points count: {len(mask_data.points) if mask_data.points else 0}")
                
                if mask_data.masks:
                    for i, mask_points in enumerate(mask_data.masks):
                        if mask_points:
                            all_zeros = all(point[0] == 0 and point[1] == 0 for point in mask_points)
                            point_count = len(mask_points)
                            min_x = min(point[0] for point in mask_points) if mask_points else 0
                            max_x = max(point[0] for point in mask_points) if mask_points else 0
                            min_y = min(point[1] for point in mask_points) if mask_points else 0
                            max_y = max(point[1] for point in mask_points) if mask_points else 0
                            
                            print(f"    Mask {i}: {point_count} points, all_zeros={all_zeros}")
                            print(f"      Bounds: x({min_x}-{max_x}), y({min_y}-{max_y})")
                            print(f"      Points: {mask_points[:3]}..." if len(mask_points) > 3 else f"      Points: {mask_points}")
                        else:
                            print(f"    Mask {i}: Empty or None")
                else:
                    print("    No masks data")
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main() 