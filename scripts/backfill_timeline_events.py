#!/usr/bin/env python3
"""
Backfill timeline events for existing users.

This script creates auto-generated timeline events (birth, adoption, death)
for all users who have those dates set but don't yet have timeline events.
"""

import sys
from pathlib import Path

# Add src to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.app import create_app
from app.modules.users.models import User
from app.modules.timeline.helpers import sync_user_life_events
from sqlalchemy import select


def main():
    """Backfill timeline events for all existing users."""
    app = create_app()
    
    # Use app context to access session
    with app.app_context():
        # Create a session using the app's before_request logic
        from app.db import SessionLocal
        session = SessionLocal()
        
        try:
            # Get all users
            users = session.scalars(select(User)).all()
            
            print(f"Found {len(users)} users")
            print("Backfilling timeline events...")
            
            processed = 0
            created_events = 0
            
            for user in users:
                # Count events before sync
                events_before = len(user.timeline_events)
                
                # Sync events for this user
                sync_user_life_events(user, session)
                session.flush()  # Flush to get updated relationships
                
                # Refresh to get updated timeline_events
                session.refresh(user)
                events_after = len(user.timeline_events)
                
                new_events = events_after - events_before
                if new_events > 0:
                    print(f"  User {user.id} ({user.display_name}): created {new_events} event(s)")
                    created_events += new_events
                
                processed += 1
            
            # Commit all changes
            session.commit()
            
            print(f"\n✅ Backfill complete!")
            print(f"   Processed: {processed} users")
            print(f"   Created: {created_events} timeline events")
            
        except Exception as e:
            session.rollback()
            print(f"\n❌ Error during backfill: {e}")
            raise
        finally:
            session.close()


if __name__ == "__main__":
    main()
