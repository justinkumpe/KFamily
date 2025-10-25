#!/usr/bin/env python3
"""
Automatic Family Relationship Inference Script

This script analyzes existing family relationships and automatically infers
and creates additional relationships based on family tree logic.

Examples:
- If A has B as father, and B has C as mother, then A should have C as grandmother
- If A has B as sibling, and B has C as child, then A should have C as niece/nephew
- If A has B as spouse, and B has C as parent, then A should have C as parent-in-law

This should be run periodically (e.g., via cron) to keep relationships up-to-date.
"""

import sys
from pathlib import Path
from typing import Set, Tuple, Optional

# Add src to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.app import create_app
from app.modules.users.models import User
from app.modules.family.models import UserRelationship
from app.modules.family.relationships import get_reciprocal_relationship
from sqlalchemy import select


# Relationship inference rules
# Format: (rel1_type, rel2_type) -> inferred_relationship_for_first_user
INFERENCE_RULES = {
    # Parent -> Grandparent relationships
    ("father", "father"): "grandfather",
    ("father", "mother"): "grandmother",
    ("mother", "father"): "grandfather",
    ("mother", "mother"): "grandmother",
    ("parent", "father"): "grandfather",
    ("parent", "mother"): "grandmother",
    ("parent", "parent"): "grandparent",
    
    # Adoptive parent -> Grandparent relationships
    ("adoptive-father", "father"): "grandfather",
    ("adoptive-father", "mother"): "grandmother",
    ("adoptive-mother", "father"): "grandfather",
    ("adoptive-mother", "mother"): "grandmother",
    
    # Parent -> Sibling = Aunt/Uncle relationships
    ("father", "brother"): "uncle",
    ("father", "sister"): "aunt",
    ("father", "sibling"): "aunt-uncle",
    ("mother", "brother"): "uncle",
    ("mother", "sister"): "aunt",
    ("mother", "sibling"): "aunt-uncle",
    ("parent", "brother"): "uncle",
    ("parent", "sister"): "aunt",
    ("parent", "sibling"): "aunt-uncle",
    
    # Sibling -> Child = Niece/Nephew relationships
    ("brother", "son"): "nephew",
    ("brother", "daughter"): "niece",
    ("brother", "child"): "niece-nephew",
    ("sister", "son"): "nephew",
    ("sister", "daughter"): "niece",
    ("sister", "child"): "niece-nephew",
    ("sibling", "son"): "nephew",
    ("sibling", "daughter"): "niece",
    ("sibling", "child"): "niece-nephew",
    
    # Grandparent -> Great-grandparent relationships
    ("grandfather", "father"): "great-grandfather",
    ("grandfather", "mother"): "great-grandmother",
    ("grandmother", "father"): "great-grandfather",
    ("grandmother", "mother"): "great-grandmother",
    ("grandparent", "father"): "great-grandfather",
    ("grandparent", "mother"): "great-grandmother",
    ("grandparent", "parent"): "great-grandparent",
    
    # Spouse -> Parent = Parent-in-law relationships
    ("spouse", "father"): "father-in-law",
    ("spouse", "mother"): "mother-in-law",
    ("spouse", "parent"): "parent-in-law",
    ("husband", "father"): "father-in-law",
    ("husband", "mother"): "mother-in-law",
    ("wife", "father"): "father-in-law",
    ("wife", "mother"): "mother-in-law",
    
    # Spouse -> Child = Step-child relationships
    ("spouse", "son"): "stepson",
    ("spouse", "daughter"): "stepdaughter",
    ("spouse", "child"): "stepchild",
    ("husband", "son"): "stepson",
    ("husband", "daughter"): "stepdaughter",
    ("wife", "son"): "stepson",
    ("wife", "daughter"): "stepdaughter",
    
    # Child -> Spouse = Child-in-law relationships
    ("son", "spouse"): "daughter-in-law",  # son's spouse is daughter-in-law
    ("daughter", "spouse"): "son-in-law",  # daughter's spouse is son-in-law
    ("son", "wife"): "daughter-in-law",
    ("daughter", "husband"): "son-in-law",
    
    # Sibling -> Spouse = Sibling-in-law relationships
    ("brother", "spouse"): "sister-in-law",
    ("sister", "spouse"): "brother-in-law",
    ("brother", "wife"): "sister-in-law",
    ("sister", "husband"): "brother-in-law",
    
    # Spouse -> Sibling = Sibling-in-law relationships
    ("spouse", "brother"): "brother-in-law",
    ("spouse", "sister"): "sister-in-law",
    ("spouse", "sibling"): "sibling-in-law",
    ("husband", "brother"): "brother-in-law",
    ("husband", "sister"): "sister-in-law",
    ("wife", "brother"): "brother-in-law",
    ("wife", "sister"): "sister-in-law",
    
    # Cousin relationships (sibling's children = cousins to my children)
    ("son", "nephew"): "cousin",
    ("son", "niece"): "cousin",
    ("daughter", "nephew"): "cousin",
    ("daughter", "niece"): "cousin",
    ("child", "nephew"): "cousin",
    ("child", "niece"): "cousin",
}


def get_all_relationships(session, user_id: int) -> dict:
    """
    Get all relationships for a user, organized by relationship type.
    
    Returns:
        Dict mapping relationship_type to list of related_user_ids
    """
    relationships = session.scalars(
        select(UserRelationship).where(UserRelationship.user_id == user_id)
    ).all()
    
    result = {}
    for rel in relationships:
        rel_type = rel.relationship_type
        if rel_type not in result:
            result[rel_type] = []
        result[rel_type].append(rel.related_user_id)
    
    return result


def relationship_exists(session, user_id: int, related_user_id: int, rel_type: str) -> bool:
    """Check if a specific relationship already exists."""
    existing = session.scalar(
        select(UserRelationship).where(
            UserRelationship.user_id == user_id,
            UserRelationship.related_user_id == related_user_id,
            UserRelationship.relationship_type == rel_type
        )
    )
    return existing is not None


def create_relationship(session, user_id: int, related_user_id: int, rel_type: str, auto_inferred: bool = True):
    """Create a new relationship if it doesn't exist."""
    if relationship_exists(session, user_id, related_user_id, rel_type):
        return None
    
    # Don't create self-relationships
    if user_id == related_user_id:
        return None
    
    relationship = UserRelationship(
        user_id=user_id,
        related_user_id=related_user_id,
        relationship_type=rel_type,
        notes=f"Auto-inferred relationship" if auto_inferred else None
    )
    session.add(relationship)
    return relationship


def infer_relationships_for_user(session, user: User) -> Set[Tuple[int, int, str]]:
    """
    Infer new relationships for a specific user based on existing relationships.
    
    Returns:
        Set of tuples (user_id, related_user_id, relationship_type) for new relationships
    """
    new_relationships = set()
    
    # Get all relationships where this user is the subject
    my_relationships = get_all_relationships(session, user.id)
    
    # For each of my relationships, check if they have relationships that create inferred ones
    for my_rel_type, my_related_ids in my_relationships.items():
        for my_related_id in my_related_ids:
            # Get relationships of the person I'm related to
            their_relationships = get_all_relationships(session, my_related_id)
            
            # Check each of their relationships against inference rules
            for their_rel_type, their_related_ids in their_relationships.items():
                # Look up inference rule
                rule_key = (my_rel_type, their_rel_type)
                if rule_key in INFERENCE_RULES:
                    inferred_rel_type = INFERENCE_RULES[rule_key]
                    
                    # Create inferred relationships to all of their related people
                    for their_related_id in their_related_ids:
                        # Don't create self-relationships
                        if their_related_id != user.id:
                            # Check if this relationship already exists
                            if not relationship_exists(session, user.id, their_related_id, inferred_rel_type):
                                new_relationships.add((user.id, their_related_id, inferred_rel_type))
    
    return new_relationships


def create_reciprocal_relationship(session, user_id: int, related_user_id: int, 
                                   original_rel_type: str, user: User, related_user: User):
    """Create the reciprocal relationship for an inferred relationship."""
    # The reciprocal should be gendered based on the ORIGINAL user's sex, not the related user's sex
    # Example: If Waylon (male) has grandmother Cindy, then Cindy has grandson Waylon
    reciprocal_type = get_reciprocal_relationship(original_rel_type, user.sex)
    
    if not relationship_exists(session, related_user_id, user_id, reciprocal_type):
        return create_relationship(session, related_user_id, user_id, reciprocal_type, auto_inferred=True)
    
    return None


def run_inference(dry_run: bool = False, verbose: bool = True):
    """
    Run relationship inference for all users.
    
    Args:
        dry_run: If True, don't commit changes (just report what would be done)
        verbose: If True, print detailed progress
    """
    app = create_app()
    
    with app.app_context():
        from app.db import SessionLocal
        session = SessionLocal()
        
        try:
            # Get all users
            users = session.scalars(select(User)).all()
            
            if verbose:
                print(f"Analyzing {len(users)} users for relationship inference...")
                print()
            
            total_inferred = 0
            users_affected = 0
            
            # Collect all new relationships first
            all_new_relationships = set()
            
            for user in users:
                new_rels = infer_relationships_for_user(session, user)
                if new_rels:
                    all_new_relationships.update(new_rels)
                    users_affected += 1
            
            if verbose:
                print(f"Found {len(all_new_relationships)} new relationships to create")
                print()
            
            # Create all inferred relationships
            for user_id, related_user_id, rel_type in sorted(all_new_relationships):
                user = session.get(User, user_id)
                related_user = session.get(User, related_user_id)
                
                if not user or not related_user:
                    continue
                
                if verbose:
                    print(f"  {user.display_name} -> {rel_type} -> {related_user.display_name}")
                
                # Create the relationship
                rel = create_relationship(session, user_id, related_user_id, rel_type)
                if rel:
                    total_inferred += 1
                    
                    # Create reciprocal relationship
                    reciprocal = create_reciprocal_relationship(
                        session, user_id, related_user_id, rel_type, user, related_user
                    )
                    if reciprocal and verbose:
                        reciprocal_type = reciprocal.relationship_type
                        print(f"    (reciprocal: {related_user.display_name} -> {reciprocal_type} -> {user.display_name})")
                    
                    if reciprocal:
                        total_inferred += 1
                    
                    # Commit after each relationship to avoid duplicates in batch insert
                    if not dry_run:
                        session.commit()
            
            if dry_run:
                session.rollback()
                if verbose:
                    print()
                    print(f"DRY RUN: Would have created {total_inferred} new relationships for {users_affected} users")
            else:
                # Final commit already done per-relationship
                if verbose:
                    print()
                    print(f"✅ Successfully created {total_inferred} new relationships for {users_affected} users")
            
            return total_inferred
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error during relationship inference: {e}")
            raise
        finally:
            session.close()


def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Infer and create automatic family relationships"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress detailed output"
    )
    
    args = parser.parse_args()
    
    try:
        count = run_inference(dry_run=args.dry_run, verbose=not args.quiet)
        
        if not args.quiet:
            print()
            if args.dry_run:
                print(f"Dry run complete. {count} relationships would be created.")
            else:
                print(f"Inference complete. {count} relationships created.")
        
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
