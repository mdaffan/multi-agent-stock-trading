# agents/user_interface_agent.py
from typing import TypedDict
from langchain.prompts import PromptTemplate
from langchain_ollama import ChatOllama
class AgentState(TypedDict):
    user_strategy: str

ollama_llm = ChatOllama(model="gemma3") 

prompt_template = """You are a helpful assistant with knowledge about trading strategies and its basic words. The user has provided the following input:
"{user_input}"

Is this input likely to be a trading strategy for stocks? Please answer with 'yes' or 'no' only."""
prompt = PromptTemplate.from_template(prompt_template)

classification_chain = prompt | ollama_llm

def get_user_strategy(state: AgentState):
    """Node for the User Interface Agent to get the trading strategy with LLM check."""
    strategy = state.get('user_strategy') or input("Please enter your trading strategy: ")

    try:
        response = classification_chain.invoke({"user_input": strategy})
        if "yes" in response.content.lower():
            return {"user_strategy": strategy}
        else:
            print("This doesn't seem like a valid trading strategy. Please try again.")
            return {"invalid_strategy": True, "user_strategy": ""}
    except Exception as e:
        print(f"Error during strategy classification: {e}")
        print("Assuming it's not a valid strategy. Please try again.")
        return {"invalid_strategy": True, "user_strategy": ""}