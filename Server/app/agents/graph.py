import logging
from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from app.agents.state import AgentState
from app.agents.tools import lookup_ipc_section, perform_legal_web_search, search_legal_precedents
from app.llm.client import get_llm

logger = logging.getLogger(__name__)

# List of tools available to the Legal Agent
tools = [search_legal_precedents, lookup_ipc_section, perform_legal_web_search]
tool_node = ToolNode(tools)


def agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Main LLM reasoning node that binds tools and determines next step.
    """
    logger.info("[Agent] Executing reasoning node...")
    llm = get_llm(temperature=0.1).bind_tools(tools)

    system_prompt = (
        "You are an expert Indian Legal Assistant Agent.\n"
        "Your task is to thoroughly analyze the user's legal question using available tools.\n"
        "You can search internal precedents, lookup IPC/CrPC sections, or perform web searches.\n"
        "Be precise, cite relevant laws and court decisions, and provide clean legal reasoning."
    )

    messages = [SystemMessage(content=system_prompt)] + list(state["messages"])
    response = llm.invoke(messages)
    return {"messages": [response]}


def should_continue(state: AgentState) -> str:
    """
    Conditional router: if the LLM called a tool, route to tool_node, else END.
    """
    messages = state["messages"]
    last_message = messages[-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        logger.info("[Agent] Tool call detected. Routing to tools...")
        return "tools"
    logger.info("[Agent] Reasoning complete. Finishing...")
    return END


def build_legal_agent_graph():
    """
    Construct the multi-agent legal research graph.
    """
    builder = StateGraph(AgentState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", tool_node)

    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", should_continue, ["tools", END])
    builder.add_edge("tools", "agent")

    return builder.compile()


# Lazy singleton
_agent_graph = None


def get_agent_graph():
    global _agent_graph
    if _agent_graph is None:
        _agent_graph = build_legal_agent_graph()
    return _agent_graph


def run_agent(question: str, doc_type: str = None) -> str:
    """
    Execute the legal research agent synchronously on a question.
    """
    graph = get_agent_graph()
    initial_state: AgentState = {
        "messages": [HumanMessage(content=question)],
        "question": question,
        "doc_type": doc_type,
        "context": None,
        "final_answer": None,
    }
    result = graph.invoke(initial_state)
    last_msg = result["messages"][-1]
    return last_msg.content if hasattr(last_msg, "content") else str(last_msg)
