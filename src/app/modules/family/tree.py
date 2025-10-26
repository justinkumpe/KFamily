"""Routes for family tree visualization."""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify
from sqlalchemy import select, or_

from .models import UserRelationship
from .models_genogram import Partnership, LifeEvent, MedicalCondition
from ..users.models import User
from ...utils.auth import api_login_required


tree_bp = Blueprint("tree", __name__)


def get_ancestors(user_id: int, sess, visited=None, depth=0, max_depth=4):
    """
    Recursively get ancestors (parents, grandparents, etc.) of a user.
    
    Args:
        user_id: User to get ancestors for
        sess: Database session
        visited: Set of visited user IDs to prevent infinite loops
        depth: Current recursion depth
        max_depth: Maximum depth to recurse
    
    Returns:
        List of ancestor user dictionaries with their relationships
    """
    if visited is None:
        visited = set()
    
    if user_id in visited or depth >= max_depth:
        return []
    
    visited.add(user_id)
    ancestors = []
    
    # Get all parent relationships (father, mother, parent, adoptive-*)
    parent_rels = sess.scalars(
        select(UserRelationship).where(
            UserRelationship.user_id == user_id,
            UserRelationship.relationship_type.in_([
                'father', 'mother', 'parent',
                'adoptive-father', 'adoptive-mother', 'adoptive-parent'
            ])
        )
    ).all()
    
    for rel in parent_rels:
        parent = sess.get(User, rel.related_user_id)
        if parent:
            parent_data = {
                'id': parent.id,
                'display_name': parent.display_name,
                'first_name': parent.first_name,
                'last_name': parent.last_name,
                'sex': parent.sex,
                'birthday': parent.birthday.isoformat() if parent.birthday else None,
                'adoption_date': parent.adoption_date.isoformat() if parent.adoption_date else None,
                'death_date': parent.death_date.isoformat() if parent.death_date else None,
                'age': parent.age,
                'gravatar_url': parent.gravatar_url(size=120),
                'relationship_type': rel.relationship_type,
                'generation': -depth - 1,  # Negative for ancestors
                'children': []  # Will be populated later
            }
            
            # Recursively get this parent's parents
            parent_data['parents'] = get_ancestors(parent.id, sess, visited, depth + 1, max_depth)
            ancestors.append(parent_data)
    
    return ancestors


def get_descendants(user_id: int, sess, visited=None, depth=0, max_depth=3):
    """
    Recursively get descendants (children, grandchildren, etc.) of a user.
    
    Args:
        user_id: User to get descendants for
        sess: Database session
        visited: Set of visited user IDs to prevent infinite loops
        depth: Current recursion depth
        max_depth: Maximum depth to recurse
    
    Returns:
        List of descendant user dictionaries with their relationships
    """
    if visited is None:
        visited = set()
    
    if user_id in visited or depth >= max_depth:
        return []
    
    visited.add(user_id)
    descendants = []
    
    # Get all child relationships (son, daughter, child)
    child_rels = sess.scalars(
        select(UserRelationship).where(
            UserRelationship.user_id == user_id,
            UserRelationship.relationship_type.in_(['son', 'daughter', 'child'])
        )
    ).all()
    
    for rel in child_rels:
        child = sess.get(User, rel.related_user_id)
        if child:
            child_data = {
                'id': child.id,
                'display_name': child.display_name,
                'first_name': child.first_name,
                'last_name': child.last_name,
                'sex': child.sex,
                'birthday': child.birthday.isoformat() if child.birthday else None,
                'adoption_date': child.adoption_date.isoformat() if child.adoption_date else None,
                'death_date': child.death_date.isoformat() if child.death_date else None,
                'age': child.age,
                'gravatar_url': child.gravatar_url(size=120),
                'relationship_type': rel.relationship_type,
                'generation': depth + 1,  # Positive for descendants
            }
            
            # Recursively get this child's children
            child_data['children'] = get_descendants(child.id, sess, visited, depth + 1, max_depth)
            descendants.append(child_data)
    
    return descendants


def get_siblings(user_id: int, sess):
    """Get siblings of a user."""
    siblings = []
    
    # Get all sibling relationships
    sibling_rels = sess.scalars(
        select(UserRelationship).where(
            UserRelationship.user_id == user_id,
            UserRelationship.relationship_type.in_(['brother', 'sister', 'sibling'])
        )
    ).all()
    
    for rel in sibling_rels:
        sibling = sess.get(User, rel.related_user_id)
        if sibling:
            siblings.append({
                'id': sibling.id,
                'display_name': sibling.display_name,
                'first_name': sibling.first_name,
                'last_name': sibling.last_name,
                'sex': sibling.sex,
                'birthday': sibling.birthday.isoformat() if sibling.birthday else None,
                'adoption_date': sibling.adoption_date.isoformat() if sibling.adoption_date else None,
                'death_date': sibling.death_date.isoformat() if sibling.death_date else None,
                'age': sibling.age,
                'gravatar_url': sibling.gravatar_url(size=120),
                'relationship_type': rel.relationship_type,
                'generation': 0,
            })
    
    return siblings


def get_spouse(user_id: int, sess):
    """Get spouse of a user."""
    spouse_rel = sess.scalar(
        select(UserRelationship).where(
            UserRelationship.user_id == user_id,
            UserRelationship.relationship_type == 'spouse'
        )
    )
    
    if spouse_rel:
        spouse = sess.get(User, spouse_rel.related_user_id)
        if spouse:
            return {
                'id': spouse.id,
                'display_name': spouse.display_name,
                'first_name': spouse.first_name,
                'last_name': spouse.last_name,
                'sex': spouse.sex,
                'birthday': spouse.birthday.isoformat() if spouse.birthday else None,
                'adoption_date': spouse.adoption_date.isoformat() if spouse.adoption_date else None,
                'death_date': spouse.death_date.isoformat() if spouse.death_date else None,
                'age': spouse.age,
                'gravatar_url': spouse.gravatar_url(size=120),
                'relationship_type': 'spouse',
                'generation': 0,
            }
    
    return None


def get_extended_family(user_id: int, sess):
    """
    Get extended family members (aunts, uncles, nieces, nephews, cousins, etc.).
    
    Returns a dictionary with categorized extended family members.
    """
    extended = {
        'aunts_uncles': [],
        'nieces_nephews': [],
        'cousins': [],
        'grandchildren': [],
        'in_laws': [],
    }
    
    # Get all relationships
    all_rels = sess.scalars(
        select(UserRelationship).where(UserRelationship.user_id == user_id)
    ).all()
    
    for rel in all_rels:
        related_user = sess.get(User, rel.related_user_id)
        if not related_user:
            continue
        
        user_data = {
            'id': related_user.id,
            'display_name': related_user.display_name,
            'first_name': related_user.first_name,
            'last_name': related_user.last_name,
            'sex': related_user.sex,
            'birthday': related_user.birthday.isoformat() if related_user.birthday else None,
            'adoption_date': related_user.adoption_date.isoformat() if related_user.adoption_date else None,
            'death_date': related_user.death_date.isoformat() if related_user.death_date else None,
            'age': related_user.age,
            'gravatar_url': related_user.gravatar_url(size=120),
            'relationship_type': rel.relationship_type,
        }
        
        # Categorize by relationship type
        if rel.relationship_type in ['aunt', 'uncle']:
            user_data['generation'] = -1
            extended['aunts_uncles'].append(user_data)
        elif rel.relationship_type in ['niece', 'nephew']:
            user_data['generation'] = 1
            # Find the parent (sibling) who has this niece/nephew as a child
            parent_rel = sess.scalar(
                select(UserRelationship).where(
                    UserRelationship.user_id == rel.related_user_id,
                    UserRelationship.relationship_type.in_(['father', 'mother', 'parent'])
                )
            )
            if parent_rel:
                user_data['parent_id'] = parent_rel.related_user_id
            extended['nieces_nephews'].append(user_data)
        elif rel.relationship_type == 'cousin':
            user_data['generation'] = 0
            extended['cousins'].append(user_data)
        elif rel.relationship_type in ['grandson', 'granddaughter', 'grandchild']:
            user_data['generation'] = 2
            extended['grandchildren'].append(user_data)
        elif rel.relationship_type in ['son-in-law', 'daughter-in-law', 'child-in-law',
                                       'father-in-law', 'mother-in-law', 'parent-in-law',
                                       'brother-in-law', 'sister-in-law', 'sibling-in-law']:
            # Determine generation based on in-law type
            if 'father' in rel.relationship_type or 'mother' in rel.relationship_type or 'parent' in rel.relationship_type:
                user_data['generation'] = -1
            elif 'son' in rel.relationship_type or 'daughter' in rel.relationship_type or 'child' in rel.relationship_type:
                user_data['generation'] = 1
            else:
                user_data['generation'] = 0
            extended['in_laws'].append(user_data)
    
    return extended


def build_complete_family_network(root_user_id: int, sess):
    """
    Build a complete family network starting from a root user.
    Returns all people in the network with their actual parent-child relationships,
    partnerships, and life events.
    """
    visited = set()
    people = {}
    relationships = []  # List of (parent_id, child_id, relationship_type) tuples
    partnerships = []  # List of partnership data
    
    def get_person_data(user):
        """Convert user to dictionary format."""
        return {
            'id': user.id,
            'display_name': user.display_name,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'sex': user.sex,
            'birthday': user.birthday.isoformat() if user.birthday else None,
            'adoption_date': user.adoption_date.isoformat() if user.adoption_date else None,
            'death_date': user.death_date.isoformat() if user.death_date else None,
            'age': user.age,
            'gravatar_url': user.gravatar_url(size=120),
        }
    
    def explore_network(user_id, depth=0, max_depth=5):
        """Recursively explore the family network."""
        if user_id in visited or depth > max_depth:
            return
        
        visited.add(user_id)
        user = sess.get(User, user_id)
        if not user:
            return
        
        # Add this person to our people dict
        people[user_id] = get_person_data(user)
        
        # Get all relationships for this user
        all_rels = sess.scalars(
            select(UserRelationship).where(UserRelationship.user_id == user_id)
        ).all()
        
        for rel in all_rels:
            related_id = rel.related_user_id
            
            # Track parent-child relationships
            if rel.relationship_type in ['father', 'mother', 'parent', 
                                         'adoptive-father', 'adoptive-mother', 'adoptive-parent']:
                # This person's parent
                relationships.append((related_id, user_id, rel.relationship_type))
                explore_network(related_id, depth + 1, max_depth)
            
            elif rel.relationship_type in ['son', 'daughter', 'child']:
                # This person's child
                relationships.append((user_id, related_id, rel.relationship_type))
                explore_network(related_id, depth + 1, max_depth)
            
            # Also explore siblings, spouses to get complete network
            elif rel.relationship_type in ['brother', 'sister', 'sibling', 
                                          'husband', 'wife', 'spouse',
                                          'aunt', 'uncle', 'niece', 'nephew', 'cousin']:
                explore_network(related_id, depth + 1, max_depth)
    
    # Start exploration from root user
    explore_network(root_user_id)
    
    # Get all partnerships involving people in our network
    if people:
        all_partnerships = sess.scalars(
            select(Partnership).where(
                or_(
                    Partnership.person1_id.in_(people.keys()),
                    Partnership.person2_id.in_(people.keys())
                )
            )
        ).all()
        
        for partnership in all_partnerships:
            partnerships.append({
                'id': partnership.id,
                'person1_id': partnership.person1_id,
                'person2_id': partnership.person2_id,
                'relationship_type': partnership.relationship_type.value,
                'relationship_quality': partnership.relationship_quality.value if partnership.relationship_quality else None,
                'start_date': partnership.start_date.isoformat() if partnership.start_date else None,
                'end_date': partnership.end_date.isoformat() if partnership.end_date else None,
                'has_children': partnership.has_children,
                'custody_type': partnership.custody_type.value if partnership.custody_type else None,
            })
    
    return {
        'people': people,
        'relationships': relationships,  # List of (parent_id, child_id) tuples
        'partnerships': partnerships,  # List of partnership dictionaries
        'root_id': root_user_id
    }


@tree_bp.get("/test")
def test_endpoint():
    """Simple test endpoint to verify blueprint is working."""
    return jsonify({"status": "ok", "message": "Tree blueprint is working"})


@tree_bp.get("")
@api_login_required
def get_family_tree():
    """Get the comprehensive family tree for the current logged-in user."""
    try:
        print("=== get_family_tree called ===")
        from flask_login import current_user
        print(f"Current user ID: {current_user.id}")
        sess = current_app.session
        
        # Get current user info
        user = sess.get(User, current_user.id)
        print(f"User found: {user is not None}")
        
        if not user:
            print("ERROR: User not found")
            return jsonify({"error": "User not found"}), 404
        
        print("Building complete family network...")
        # Build complete family network
        network = build_complete_family_network(user.id, sess)
        
        print(f"Network built: {len(network['people'])} people, {len(network['relationships'])} parent-child relationships, {len(network['partnerships'])} partnerships")
        
        tree_data = {
            'root_id': user.id,
            'people': network['people'],
            'relationships': network['relationships'],  # List of [parent_id, child_id, relationship_type] arrays
            'partnerships': network['partnerships'],  # List of partnership objects
        }
        
        print("Returning tree data as JSON...")
        return jsonify(tree_data)
    except Exception as e:
        import traceback
        print(f"=== ERROR in get_family_tree ===")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception message: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e), "type": type(e).__name__}), 500
