"""API routes for managing medical conditions."""
from __future__ import annotations

from datetime import date
from flask import Blueprint, current_app, g, jsonify, request
from sqlalchemy import select

from .models_genogram import MedicalCondition
from ..users.models import User
from ...utils.auth import api_login_required


medical_bp = Blueprint("medical", __name__)


@medical_bp.post("")
@api_login_required
def create_medical_condition():
    """Create a new medical condition."""
    data = request.get_json()
    sess = g.db_session
    
    if not all(k in data for k in ['user_id', 'condition_name']):
        return jsonify({"error": "Missing required fields"}), 400
    
    user = sess.get(User, data['user_id'])
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    condition = MedicalCondition(
        user_id=data['user_id'],
        condition_name=data['condition_name'],
        diagnosis_date=date.fromisoformat(data['diagnosis_date']) if data.get('diagnosis_date') else None,
        resolution_date=date.fromisoformat(data['resolution_date']) if data.get('resolution_date') else None,
        is_genetic=data.get('is_genetic', False),
        is_chronic=data.get('is_chronic', False),
        is_terminal=data.get('is_terminal', False),
        is_cause_of_death=data.get('is_cause_of_death', False),
        notes=data.get('notes'),
        is_private=data.get('is_private', True),
    )
    
    sess.add(condition)
    sess.commit()
    
    return jsonify(_condition_to_dict(condition)), 201


@medical_bp.get("/<int:condition_id>")
@api_login_required
def get_medical_condition(condition_id: int):
    """Get a specific medical condition."""
    sess = g.db_session
    condition = sess.get(MedicalCondition, condition_id)
    
    if not condition:
        return jsonify({"error": "Medical condition not found"}), 404
    
    return jsonify(_condition_to_dict(condition))


@medical_bp.put("/<int:condition_id>")
@api_login_required
def update_medical_condition(condition_id: int):
    """Update a medical condition."""
    data = request.get_json()
    sess = g.db_session
    
    condition = sess.get(MedicalCondition, condition_id)
    if not condition:
        return jsonify({"error": "Medical condition not found"}), 404
    
    if 'condition_name' in data:
        condition.condition_name = data['condition_name']
    if 'diagnosis_date' in data:
        condition.diagnosis_date = date.fromisoformat(data['diagnosis_date']) if data['diagnosis_date'] else None
    if 'resolution_date' in data:
        condition.resolution_date = date.fromisoformat(data['resolution_date']) if data['resolution_date'] else None
    if 'is_genetic' in data:
        condition.is_genetic = data['is_genetic']
    if 'is_chronic' in data:
        condition.is_chronic = data['is_chronic']
    if 'is_terminal' in data:
        condition.is_terminal = data['is_terminal']
    if 'is_cause_of_death' in data:
        condition.is_cause_of_death = data['is_cause_of_death']
    if 'notes' in data:
        condition.notes = data['notes']
    if 'is_private' in data:
        condition.is_private = data['is_private']
    
    sess.commit()
    
    return jsonify(_condition_to_dict(condition))


@medical_bp.delete("/<int:condition_id>")
@api_login_required
def delete_medical_condition(condition_id: int):
    """Delete a medical condition."""
    sess = g.db_session
    condition = sess.get(MedicalCondition, condition_id)
    
    if not condition:
        return jsonify({"error": "Medical condition not found"}), 404
    
    sess.delete(condition)
    sess.commit()
    
    return jsonify({"message": "Medical condition deleted"}), 200


@medical_bp.get("/user/<int:user_id>")
@api_login_required
def get_user_medical_conditions(user_id: int):
    """Get all medical conditions for a user."""
    sess = g.db_session
    
    user = sess.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    conditions = sess.scalars(
        select(MedicalCondition).where(
            MedicalCondition.user_id == user_id
        ).order_by(MedicalCondition.diagnosis_date.desc())
    ).all()
    
    return jsonify([_condition_to_dict(c) for c in conditions])


def _condition_to_dict(condition: MedicalCondition) -> dict:
    """Convert medical condition to dictionary."""
    return {
        'id': condition.id,
        'user_id': condition.user_id,
        'condition_name': condition.condition_name,
        'diagnosis_date': condition.diagnosis_date.isoformat() if condition.diagnosis_date else None,
        'resolution_date': condition.resolution_date.isoformat() if condition.resolution_date else None,
        'is_genetic': condition.is_genetic,
        'is_chronic': condition.is_chronic,
        'is_terminal': condition.is_terminal,
        'is_cause_of_death': condition.is_cause_of_death,
        'notes': condition.notes,
        'is_private': condition.is_private,
        'created_at': condition.created_at.isoformat(),
        'updated_at': condition.updated_at.isoformat(),
    }
