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


@tree_bp.get("")
@api_login_required
def get_family_tree():
    """Get the family tree for the current logged-in user."""
    from flask_login import current_user
    sess = current_app.session
    
    # Get current user info
    user = sess.get(User, current_user.id)
    
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
    }
    
    return jsonify(tree_data)
