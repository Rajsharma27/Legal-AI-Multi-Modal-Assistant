from typing import List, Optional, Sequence
from pydantic import BaseModel
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """
    State representation for multi-agent legal reasoning tasks.
    """
    messages: Sequence[BaseMessage]
    question: str
    doc_type: Optional[str]
    context: Optional[str]
    final_answer: Optional[str]
