# Timeline Event Templates System

## Overview

The Timeline Event Templates system provides a standardized way for modules to define custom timeline event types with their own formatting, validation, and metadata schemas.

## Purpose

- **Extensibility**: Allow future modules to add their own timeline event types
- **Consistency**: Standardize how events are displayed and validated
- **Type Safety**: Define metadata schemas for each event type
- **UI Integration**: Provide icon and color information for frontend rendering

## Architecture

### Base Class: `TimelineEventTemplate`

All event templates inherit from this abstract base class.

```python
from app.modules.timeline import TimelineEventTemplate, register_template

class MyCustomEventTemplate(TimelineEventTemplate):
    event_type = "my_custom_event"
    module_name = "my_module"
    display_name = "My Custom Event"
    description = "Description of what this event represents"
    default_visibility = "family"
    icon_class = "bi-calendar-event"  # Bootstrap Icon class
    color_class = "primary"  # Bootstrap color class
    
    def get_metadata_schema(self):
        return {
            "type": "object",
            "properties": {
                "custom_field": {"type": "string"}
            }
        }
```

### Registration

Templates must be registered to be available in the system:

```python
# Register during module initialization
register_template(MyCustomEventTemplate())
```

## API Endpoints

### List All Templates

```
GET /api/timeline/templates
```

Returns all registered templates with their configurations.

**Query Parameters:**
- `module` (optional): Filter templates by module name

**Response:**
```json
{
  "birth": {
    "event_type": "birth",
    "module_name": "family",
    "display_name": "Birth",
    "description": "Birth date of a family member",
    "default_visibility": "family",
    "icon_class": "bi-gift",
    "color_class": "success",
    "metadata_schema": {
      "type": "object",
      "properties": {
        "birth_place": {"type": "string"}
      }
    }
  }
}
```

### Get Specific Template

```
GET /api/timeline/templates/<event_type>
```

Returns details for a specific event template.

## Built-in Templates

The system comes with three built-in templates for the family module:

### 1. Birth Event Template

- **Event Type**: `birth`
- **Icon**: `bi-gift` (🎁)
- **Color**: `success` (green)
- **Visibility**: `family`
- **Metadata Fields**:
  - `birth_place` (string): Place of birth
  - `birth_weight` (string): Birth weight
  - `birth_time` (string): Time of birth

### 2. Adoption Event Template

- **Event Type**: `adoption`
- **Icon**: `bi-heart` (❤️)
- **Color**: `danger` (red)
- **Visibility**: `family`
- **Metadata Fields**:
  - `adoption_agency` (string): Adoption agency
  - `adoption_location` (string): Location of adoption

### 3. Death Event Template

- **Event Type**: `death`
- **Icon**: `bi-flower1` (🌸)
- **Color**: `secondary` (gray)
- **Visibility**: `family`
- **Metadata Fields**:
  - `death_place` (string): Place of death
  - `cause` (string): Cause of death
  - `burial_location` (string): Burial location

## Creating Custom Templates

### Step 1: Define Your Template Class

Create a new class that inherits from `TimelineEventTemplate`:

```python
from app.modules.timeline import TimelineEventTemplate
from typing import Dict, Any, Optional

class GraduationEventTemplate(TimelineEventTemplate):
    event_type = "graduation"
    module_name = "education"  # Your module name
    display_name = "Graduation"
    description = "Academic graduation event"
    default_visibility = "public"
    icon_class = "bi-mortarboard"
    color_class = "info"
    
    def get_metadata_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "school": {
                    "type": "string",
                    "description": "Name of school"
                },
                "degree": {
                    "type": "string",
                    "description": "Degree earned"
                },
                "honors": {
                    "type": "string",
                    "description": "Academic honors"
                }
            },
            "required": ["school"]
        }
    
    def format_title(self, user_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        if metadata and metadata.get("degree"):
            return f"{user_name} graduated with {metadata['degree']}"
        return f"{user_name} graduated"
    
    def format_description(self, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        if not metadata:
            return None
        
        parts = []
        if metadata.get("school"):
            parts.append(f"From {metadata['school']}")
        if metadata.get("honors"):
            parts.append(f"With {metadata['honors']}")
        
        return " • ".join(parts) if parts else None
```

### Step 2: Register Your Template

In your module's initialization file:

```python
# src/app/modules/education/__init__.py
from app.modules.timeline import register_template
from .timeline_templates import GraduationEventTemplate

# Register during module load
register_template(GraduationEventTemplate())
```

### Step 3: Create Events Using Your Template

```python
from app.modules.timeline.helpers import create_event_for_user

create_event_for_user(
    user_id=user.id,
    event_date=date(2020, 5, 15),
    event_type="graduation",
    module_name="education",
    title="Graduated from University",
    visibility="public",
    metadata={
        "school": "State University",
        "degree": "Bachelor of Science",
        "honors": "Summa Cum Laude"
    },
    session=sess
)
```

## Template Methods Reference

### Required Methods

#### `get_metadata_schema()`

Returns a JSON schema describing the expected metadata structure.

**Returns**: `Dict[str, Any]` - JSON schema object

### Optional Methods (Override as Needed)

#### `validate_metadata(metadata)`

Validate metadata beyond basic schema validation.

**Parameters**:
- `metadata`: The metadata dictionary to validate

**Returns**: `bool` - True if valid

#### `format_title(user_name, metadata)`

Generate a formatted title for the event.

**Parameters**:
- `user_name`: Display name of the user
- `metadata`: Event metadata

**Returns**: `str` - Formatted title

#### `format_description(metadata)`

Generate a formatted description from metadata.

**Parameters**:
- `metadata`: Event metadata

**Returns**: `Optional[str]` - Formatted description or None

#### `to_dict()`

Serialize template to dictionary (automatically called by API).

**Returns**: `Dict[str, Any]` - Template information

## Class Attributes Reference

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `event_type` | `str` | Yes | Unique identifier for this event type |
| `module_name` | `str` | Yes | Name of the module providing this template |
| `display_name` | `str` | Yes | Human-readable name for the event type |
| `description` | `str` | Yes | Brief description of what this event represents |
| `default_visibility` | `str` | Yes | Default visibility level (`public`, `family`, `household`, `parents`, `private`) |
| `icon_class` | `str` | Yes | Bootstrap Icons class name (e.g., `bi-calendar-event`) |
| `color_class` | `str` | Yes | Bootstrap color class (`primary`, `secondary`, `success`, `danger`, `warning`, `info`) |

## Bootstrap Icon Reference

Common icons for timeline events:

- `bi-gift` - Birth, gifts
- `bi-heart` - Adoption, love, relationships
- `bi-flower1` - Death, memorial
- `bi-mortarboard` - Graduation, education
- `bi-briefcase` - Career, work
- `bi-house` - Home, moving
- `bi-airplane` - Travel
- `bi-trophy` - Achievements
- `bi-calendar-event` - Generic events
- `bi-star` - Special occasions
- `bi-heart-pulse` - Medical events

Full icon list: https://icons.getbootstrap.com/

## Best Practices

1. **Unique Event Types**: Ensure your `event_type` is unique across all modules
2. **Namespace**: Prefix event types with module name if needed (e.g., `education_graduation`)
3. **Metadata Schema**: Keep schemas simple and focused
4. **Validation**: Implement custom validation for complex business rules
5. **Formatting**: Override `format_title` and `format_description` for rich displays
6. **Documentation**: Document your template's metadata fields

## Example: Creating a Work Module with Job Events

```python
# src/app/modules/work/timeline_templates.py
from app.modules.timeline import TimelineEventTemplate
from typing import Dict, Any, Optional

class JobStartTemplate(TimelineEventTemplate):
    event_type = "job_start"
    module_name = "work"
    display_name = "Started Job"
    description = "Started a new job position"
    default_visibility = "public"
    icon_class = "bi-briefcase"
    color_class = "primary"
    
    def get_metadata_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "company": {"type": "string"},
                "position": {"type": "string"},
                "location": {"type": "string"},
                "salary": {"type": "number"}
            },
            "required": ["company", "position"]
        }
    
    def format_title(self, user_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        if metadata:
            position = metadata.get("position", "")
            company = metadata.get("company", "")
            return f"{user_name} started as {position} at {company}"
        return f"{user_name} started a new job"
    
    def format_description(self, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        if not metadata:
            return None
        
        if metadata.get("location"):
            return f"Location: {metadata['location']}"
        return None

class JobEndTemplate(TimelineEventTemplate):
    event_type = "job_end"
    module_name = "work"
    display_name = "Left Job"
    description = "Left a job position"
    default_visibility = "public"
    icon_class = "bi-briefcase-fill"
    color_class = "warning"
    
    def get_metadata_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "company": {"type": "string"},
                "position": {"type": "string"},
                "reason": {"type": "string"}
            },
            "required": ["company"]
        }
    
    def format_title(self, user_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        if metadata and metadata.get("company"):
            return f"{user_name} left {metadata['company']}"
        return f"{user_name} left their job"

# src/app/modules/work/__init__.py
from app.modules.timeline import register_template
from .timeline_templates import JobStartTemplate, JobEndTemplate

register_template(JobStartTemplate())
register_template(JobEndTemplate())
```

## Testing Templates

```python
from app.modules.timeline import get_template

# Get a template
template = get_template("graduation")

# Validate metadata
metadata = {"school": "State University", "degree": "BS"}
is_valid = template.validate_metadata(metadata)

# Format title and description
title = template.format_title("John Doe", metadata)
description = template.format_description(metadata)

# Get template info
info = template.to_dict()
```

## Future Enhancements

Potential future features for the template system:

1. **Field Validation**: More sophisticated validation rules
2. **Conditional Fields**: Show/hide fields based on other field values
3. **Custom Renderers**: Allow templates to provide custom HTML renderers
4. **Event Actions**: Define actions that can be performed on events
5. **Notifications**: Template-defined notification rules
6. **Import/Export**: Templates could define how events are imported/exported
