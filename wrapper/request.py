"""
GenAI standardized request encapsulation.
Injects test-run metadata, headers, and synthetic isolation tags into outbound API requests.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from wrapper.context import RequestContext, get_current_context

@dataclass
class GenAIRequest:
    endpoint: str
    method: str = "POST"
    payload: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    timeout: float = 60.0
    context: Optional[RequestContext] = None
    params: Dict[str, Any] = field(default_factory=dict)

    def prepare_headers(self, inject_metadata: bool = True) -> Dict[str, str]:
        """
        Merge explicit headers with request context synthetic metadata headers.
        """
        final_headers = dict(self.headers)
        if "Content-Type" not in final_headers:
            final_headers["Content-Type"] = "application/json"
            
        ctx = self.context or get_current_context()
        if inject_metadata and ctx:
            final_headers.update(ctx.to_headers())
            
        return final_headers
