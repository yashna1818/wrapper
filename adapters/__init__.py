from adapters.chatbot import ChatbotAdapter
from adapters.rag import RAGAdapter
from adapters.image_generation import ImageGenerationAdapter
from adapters.ppt_generation import PPTGenerationAdapter
from adapters.document_generation import DocumentGenerationAdapter
from wrapper.registry import registry

def register_default_adapters():
    """
    Registers standard built-in GenAI adapters into global registry.
    """
    registry.register("chatbot", ChatbotAdapter())
    registry.register("rag", RAGAdapter())
    registry.register("image_generation", ImageGenerationAdapter())
    registry.register("ppt_generation", PPTGenerationAdapter())
    registry.register("document_generation", DocumentGenerationAdapter())

__all__ = [
    "ChatbotAdapter",
    "RAGAdapter",
    "ImageGenerationAdapter",
    "PPTGenerationAdapter",
    "DocumentGenerationAdapter",
    "register_default_adapters",
]
