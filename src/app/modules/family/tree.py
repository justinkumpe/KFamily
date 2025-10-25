"""Routes for family tree visualization."""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify
from sqlalchemy import select

from .models import UserRelationship
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


@tree_bp.get("")
@api_login_required
def get_family_tree():
    """Get the comprehensive family tree for the current logged-in user."""
    from flask_login import current_user
    sess = current_app.session
    
    # Get current user info
    user = sess.get(User, current_user.id)
    
    # Get extended family
    extended = get_extended_family(user.id, sess)
    
    tree_data = {
        'root': {
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
            'generation': 0,
        },
        'ancestors': get_ancestors(user.id, sess),
        'descendants': get_descendants(user.id, sess),
        'siblings': get_siblings(user.id, sess),
        'spouse': get_spouse(user.id, sess),
        'aunts_uncles': extended['aunts_uncles'],
        'nieces_nephews': extended['nieces_nephews'],
        'cousins': extended['cousins'],
        'grandchildren': extended['grandchildren'],
        'in_laws': extended['in_laws'],
    }
    
    return jsonify(tree_data)
