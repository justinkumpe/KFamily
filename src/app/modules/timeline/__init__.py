"""Timeline module for tracking user life events."""

from .models import TimelineEvent
from .templates import (
    TimelineEventTemplate,
    register_template,
    get_template,
    get_all_templates,
    list_templates_for_module,
)

__all__ = [
    "TimelineEvent",
    "TimelineEventTemplate",
    "register_template",
    "get_template",
    "get_all_templates",
    "list_templates_for_module",
]
