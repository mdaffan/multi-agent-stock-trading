from typing import TypedDict, Dict, Any
from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import Runnable
from langchain_core.output_parsers import StrOutputParser
from langchain_chroma import Chroma # type: ignore
from langchain_huggingface import HuggingFaceEmbeddings
class AgentState(TypedDict):
    user_strategy: str
    interpreted_rules: Dict[str, Any]

ollama_llm = ChatOllama(model="gemma3")

# Initialize ChromaDB and the retriever (adjust parameters as needed)
persist_directory = 'chroma_db'  # Make sure this matches where you stored your DB
embedding = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2') # Or your embeddings
vectordb = Chroma(persist_directory=persist_directory, embedding_function=embedding)
knowledge_retriever = vectordb.as_retriever(search_kwargs={"k": 3})  # Adjust 'k' as needed

prompt_template = """You are a trading strategy interpreter. Based on the user's strategy:
"{user_strategy}"
Use the following relevant knowledge to understand and translate the strategy into actionable trading rules:
"{context}"

Translate this into a structured JSON format that can be directly consumed by a trading agent. Your output must be valid JSON and follow this exact schema:

```json
{{
  "strategy": {{
    "asset": "[ASSET_SYMBOL]",
    "description": "[Brief description of the overall strategy]",
    "entry_condition": {{
      "type": "price_trigger",
      "condition": "[above/below/equal]",
      "price": [NUMERIC_VALUE],
      "description": "[Human-readable description of buy condition]"
    }},
    "exit_condition": {{
      "type": "price_trigger",
      "condition": "[above/below/equal]",
      "price": [NUMERIC_VALUE],
      "description": "[Human-readable description of sell condition]"
    }}
  }}
}}
```

Replace the placeholders with actual values:
- [ASSET_SYMBOL]: The stock symbol (e.g., AAPL, GOOGL, SPY)
- [NUMERIC_VALUE]: A number without the dollar sign (e.g., 150.50)
- Description fields should contain human-readable explanations

Your output must be valid JSON that can be parsed directly. Do not include any text before or after the JSON."""
prompt = PromptTemplate.from_template(prompt_template)
interpretation_chain = prompt | ollama_llm
def interpret_strategy(state: AgentState):
    user_strategy = state.get("user_strategy")
    if not user_strategy:
        print("No user strategy provided.")
        return {"interpreted_rules": {}}

    print(f"Interpreting strategy: {user_strategy}")

    try:
        # Get relevant knowledge
        relevant_knowledge = knowledge_retriever.invoke(user_strategy)
        context = "\n".join([doc.page_content for doc in relevant_knowledge])

        interpreted_output = interpretation_chain.invoke({"user_strategy": user_strategy, "context": context})
        print(f"Raw LLM output: {interpreted_output}")

        # Extract the content from the LLM response
        raw_output = interpreted_output.content # Assuming Ollama returns a ChatResult
        print(f"Content: {raw_output}")

        # Try to extract JSON from the output
        import json
        import re

        # Find JSON content between triple backticks if present
        json_match = re.search(r'```json\s*(.+?)\s*```', raw_output, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # If not in code blocks, try to find JSON directly
            json_str = raw_output.strip()

        try:
            # Parse the JSON
            parsed_json = json.loads(json_str)
            print(f"Successfully parsed JSON: {parsed_json}")

            # Store both the raw output and the parsed JSON
            interpreted_rules = {
                "raw_output": raw_output,
                "strategy": parsed_json.get("strategy", {})
            }

            # For backward compatibility, also extract buy/sell conditions
            strategy_data = parsed_json.get("strategy", {})
            entry_condition = strategy_data.get("entry_condition", {})
            exit_condition = strategy_data.get("exit_condition", {})

            buy_description = entry_condition.get("description", "")
            sell_description = exit_condition.get("description", "")

            interpreted_rules["buy_condition"] = buy_description
            interpreted_rules["sell_condition"] = sell_description

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            # Fallback to the old method if JSON parsing fails
            buy_condition_start = raw_output.find("Buy condition:")
            sell_condition_start = raw_output.find("Sell condition:")

            if buy_condition_start >= 0 and sell_condition_start >= 0:
                buy_condition = raw_output[buy_condition_start + len("Buy condition:"): sell_condition_start].strip()
                sell_condition = raw_output[sell_condition_start + len("Sell condition:"):].strip()

                interpreted_rules = {
                    "raw_output": raw_output,
                    "buy_condition": buy_condition,
                    "sell_condition": sell_condition,
                    "strategy": {}
                }
            else:
                interpreted_rules = {
                    "raw_output": raw_output,
                    "error": "Could not parse strategy output",
                    "strategy": {}
                }

    except Exception as e:
        print(f"Error during LLM interpretation: {e}")
        interpreted_rules = {"error": str(e)}

    print(f"Interpreted rules: {interpreted_rules}")
    return {"interpreted_rules": interpreted_rules}

