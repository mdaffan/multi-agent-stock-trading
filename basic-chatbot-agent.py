from langchain_core.runnables import RunnableLambda
from langgraph.graph import StateGraph, END
from typing import Dict, Any, TypedDict
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
# 1. Define the state
class AgentState(TypedDict):
    """State for the agent."""
    messages: list[Dict[str, Any]]
# 2. Create a simple function for our first step (a node)
def ollama_chatbot(state):
    print("Ollama Chatbot is streaming...")
    llm = ChatOllama(model="gemma3")  # Replace with your desired model if needed
    prompt = ""
    message = HumanMessage(content=prompt)

    full_response = ""
    for chunk in llm.stream([message]):
        content = chunk.content
        print(content, end="", flush=True)
        full_response += content
    print("\nStreaming complete.")

    return {"messages": state["messages"] + [{"role": "agent", "content": full_response}]}


# 3. Initialize the LangGraph
workflow = StateGraph(AgentState)

# 4. Add the 'greet' function as a node named "greet_node"
workflow.add_node("ollama_node", ollama_chatbot)

# 5. Set the entry point of the graph (where the workflow begins)
workflow.set_entry_point("ollama_node")

# 6. Define the end of the graph
workflow.add_edge("ollama_node", END)

# 7. Compile the graph
app = workflow.compile()

# 8. Run the graph
if __name__ == "__main__":
    inputs = {"messages": []}
    result = app.invoke(inputs)
    print(result)