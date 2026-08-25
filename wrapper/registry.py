"""
Application Registry module.
Maintains a dynamic registry of application adapters.
Allows Locust and central wrapper to resolve adapters by application name without hardcoding.
"""

import logging
from typing import Dict, List, Optional
from wrapper.base_adapter import GenAIAdapter

logger = logging.getLogger(__name__)

class ApplicationRegistry:
    def __init__(self):
        self._adapters: Dict[str, GenAIAdapter] = {}

    def register(self, name: str, adapter: GenAIAdapter) -> None:
        """
        Register an application adapter under a given application name.
        """
        if not isinstance(adapter, GenAIAdapter):
            raise TypeError(f"Adapter for '{name}' must inherit from GenAIAdapter")
        self._adapters[name.lower()] = adapter
        logger.info(f"Registered GenAI adapter: {name}")

    def get(self, name: str) -> GenAIAdapter:
        """
        Retrieve adapter by name. Raises KeyError if not registered.
        """
        key = name.lower()
        if key not in self._adapters:
            available = ", ".join(self._adapters.keys())
            raise KeyError(f"No adapter registered for application '{name}'. Registered applications: [{available}]")
        return self._adapters[key]

    def contains(self, name: str) -> bool:
        return name.lower() in self._adapters

    def list_applications(self) -> List[str]:
        return list(self._adapters.keys())

    def unregister(self, name: str) -> None:
        self._adapters.pop(name.lower(), None)


# Global singleton registry instance
registry = ApplicationRegistry()
