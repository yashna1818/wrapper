"""
Reusable GenAI Locust TaskSet and task utilities.
Allows testers to compose custom Locust users with specific task sets or application weights.
"""

from locust import TaskSet, task
from wrapper.registry import registry
from wrapper.context import RequestContext

class GenAITaskSet(TaskSet):
    """
    Importable TaskSet for manually authored Locust user scripts.
    """
    @task
    def run_registered_task(self):
        user = self.user
        if hasattr(user, "execute_genai_workload"):
            user.execute_genai_workload()
