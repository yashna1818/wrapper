"""
Locust CLI options parser.
Extends Locust CLI with custom parameters: --application, --profile, --scenario, --config-file.
"""

from locust import events

@events.init_command_line_parser.add_listener
def add_genai_args(parser):
    genai_group = parser.add_argument_group("GenAI Load Testing Framework Options")
    
    genai_group.add_argument(
        "--application",
        type=str,
        default="chatbot",
        help="Target GenAI application name (e.g., chatbot, rag, image_generation, ppt_generation, document_generation)"
    )
    
    genai_group.add_argument(
        "--profile",
        type=str,
        default="normal",
        help="Workload profile to run (e.g., normal, peak, stress, spike, endurance)"
    )
    
    genai_group.add_argument(
        "--scenario",
        type=str,
        default=None,
        help="Mixed workload scenario profile file or name (e.g., naval_operational_load)"
    )

    genai_group.add_argument(
        "--config-file",
        type=str,
        default="config/test.yaml",
        help="Path to GenAI test YAML configuration file"
    )
