"""Timeline event templates system for module integration.

This module provides a registry and base class system for modules to define
their timeline event types with standardized formatting, icons, and metadata.
"""

from __future__ import annotations
from typing import Dict, Optional, Any, List
from abc import ABC, abstractmethod


class TimelineEventTemplate(ABC):
    """
    Base class for timeline event templates.
    
    Modules can subclass this to define their event types with custom
    rendering, validation, and metadata schemas.
    """
    
    # Override these in subclasses
    event_type: str = ""
    module_name: str = ""
    display_name: str = ""
    description: str = ""
    default_visibility: str = "private"
    
    # Icon and color for UI display (Bootstrap Icons and colors)
    icon_class: str = "bi-calendar-event"  # Bootstrap icon class
    color_class: str = "primary"  # Bootstrap color class
    
    @abstractmethod
    def get_metadata_schema(self) -> Dict[str, Any]:
        """
        Return JSON schema for this event type's metadata field.
        
        This allows modules to define custom data fields specific to their events.
        
        Returns:
            Dict describing the expected metadata structure
            
        Example:
            {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                    "participants": {"type": "array", "items": {"type": "string"}}
                }
            }
        """
        pass
    
    def validate_metadata(self, metadata: Optional[Dict[str, Any]]) -> bool:
        """
        Validate metadata against this template's schema.
        
        Override this for custom validation logic beyond schema validation.
        
        Args:
            metadata: The metadata to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Basic implementation - can be overridden
        if metadata is None:
            return True
        
        schema = self.get_metadata_schema()
        required_fields = schema.get("required", [])
        
        for field in required_fields:
            if field not in metadata:
                return False
        
        return True
    
    def format_title(self, user_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate event title based on user and metadata.
        
        Override this to customize title generation.
        
        Args:
            user_name: Display name of the user
            metadata: Event-specific metadata
            
        Returns:
            Formatted title string
        """
        return f"{user_name}: {self.display_name}"
    
    def format_description(self, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Generate event description from metadata.
        
        Override this to create rich descriptions from metadata.
        
        Args:
            metadata: Event-specific metadata
            
        Returns:
            Formatted description string or None
        """
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize template information for API responses.
        
        Returns:
            Dictionary representation of the template
        """
        return {
            "event_type": self.event_type,
            "module_name": self.module_name,
            "display_name": self.display_name,
            "description": self.description,
            "default_visibility": self.default_visibility,
            "icon_class": self.icon_class,
            "color_class": self.color_class,
            "metadata_schema": self.get_metadata_schema(),
        }


# Global registry for timeline event templates
_template_registry: Dict[str, TimelineEventTemplate] = {}


def register_template(template: TimelineEventTemplate) -> None:
    """
    Register a timeline event template.
    
    Args:
        template: The template instance to register
        
    Raises:
        ValueError: If event_type is already registered
    """
    if not template.event_type:
        raise ValueError("Template must have an event_type defined")
    
    if template.event_type in _template_registry:
        raise ValueError(f"Template for event_type '{template.event_type}' already registered")
    
    _template_registry[template.event_type] = template


def get_template(event_type: str) -> Optional[TimelineEventTemplate]:
    """
    Get a registered template by event type.
    
    Args:
        event_type: The event type to look up
        
    Returns:
        The template instance or None if not found
    """
    return _template_registry.get(event_type)


def get_all_templates() -> Dict[str, TimelineEventTemplate]:
    """
    Get all registered templates.
    
    Returns:
        Dictionary mapping event_type to template instance
    """
    return _template_registry.copy()


def list_templates_for_module(module_name: str) -> List[TimelineEventTemplate]:
    """
    Get all templates for a specific module.
    
    Args:
        module_name: Name of the module
        
    Returns:
        List of template instances for that module
    """
    return [
        template for template in _template_registry.values()
        if template.module_name == module_name
    ]


def unregister_template(event_type: str) -> None:
    """
    Unregister a template (mainly for testing).
    
    Args:
        event_type: The event type to unregister
    """
    _template_registry.pop(event_type, None)


# Built-in templates for family module
class BirthEventTemplate(TimelineEventTemplate):
    """Template for birth events."""
    
    event_type = "birth"
    module_name = "family"
    display_name = "Birth"
    description = "Birth date of a family member"
    default_visibility = "family"
    icon_class = "bi-gift"
    color_class = "success"
    
    def get_metadata_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "birth_place": {"type": "string", "description": "Place of birth"},
                "birth_weight": {"type": "string", "description": "Birth weight"},
                "birth_time": {"type": "string", "description": "Time of birth"},
            },
            "required": []
        }
    
    def format_title(self, user_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        return f"{user_name} was born"
    
    def format_description(self, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        if not metadata:
            return None
        
        parts = []
        if metadata.get("birth_place"):
            parts.append(f"Born in {metadata['birth_place']}")
        if metadata.get("birth_weight"):
            parts.append(f"Weight: {metadata['birth_weight']}")
        if metadata.get("birth_time"):
            parts.append(f"Time: {metadata['birth_time']}")
        
        return " • ".join(parts) if parts else None


class AdoptionEventTemplate(TimelineEventTemplate):
    """Template for adoption events."""
    
    event_type = "adoption"
    module_name = "family"
    display_name = "Adoption"
    description = "Adoption date of a family member"
    default_visibility = "family"
    icon_class = "bi-heart"
    color_class = "danger"
    
    def get_metadata_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "adoption_agency": {"type": "string", "description": "Adoption agency"},
                "adoption_location": {"type": "string", "description": "Location of adoption"},
            },
            "required": []
        }
    
    def format_title(self, user_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        return f"{user_name} was adopted"
    
    def format_description(self, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        if not metadata:
            return None
        
        parts = []
        if metadata.get("adoption_agency"):
            parts.append(f"Agency: {metadata['adoption_agency']}")
        if metadata.get("adoption_location"):
            parts.append(f"Location: {metadata['adoption_location']}")
        
        return " • ".join(parts) if parts else None


class DeathEventTemplate(TimelineEventTemplate):
    """Template for death events."""
    
    event_type = "death"
    module_name = "family"
    display_name = "Death"
    description = "Death date of a family member"
    default_visibility = "family"
    icon_class = "bi-flower1"
    color_class = "secondary"
    
    def get_metadata_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "death_place": {"type": "string", "description": "Place of death"},
                "cause": {"type": "string", "description": "Cause of death"},
                "burial_location": {"type": "string", "description": "Burial location"},
            },
            "required": []
        }
    
    def format_title(self, user_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        return f"{user_name} passed away"
    
    def format_description(self, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        if not metadata:
            return None
        
        parts = []
        if metadata.get("death_place"):
            parts.append(f"Location: {metadata['death_place']}")
        if metadata.get("cause"):
            parts.append(f"Cause: {metadata['cause']}")
        if metadata.get("burial_location"):
            parts.append(f"Buried: {metadata['burial_location']}")
        
        return " • ".join(parts) if parts else None


# Register built-in templates
register_template(BirthEventTemplate())
register_template(AdoptionEventTemplate())
register_template(DeathEventTemplate())
