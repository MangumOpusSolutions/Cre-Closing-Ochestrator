import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Annotated
from operator import add

# 1. Load Environment
load_dotenv()

# 2. Define State with 'Reducers' to prevent overwrite errors
class ClosingState(TypedDict):
    vdr_path: str
    processed_files: Annotated[List[str], add] 
    alerts: Annotated[List[str], add]
    current_doc_text: str

# 3. Nodes
def scanner(state: ClosingState):
    # Create folder if it doesn't exist to prevent crash
    if not os.path.exists(state['vdr_path']):
        os.makedirs(state['vdr_path'])
        
    files = [f for f in os.listdir(state['vdr_path']) if f.endswith('.txt')]
    new_files = [f for f in files if f not in state['processed_files']]
    
    if not new_files:
        return {"current_doc_text": "STOP_FLOW"}
    
    with open(os.path.join(state['vdr_path'], new_files[0]), "r") as f:
        content = f.read()
    
    return {
        "current_doc_text": content,
        "processed_files": [new_files[0]]
    }

def auditor(state: ClosingState):
    if state['current_doc_text'] == "STOP_FLOW":
        return {"alerts": ["--- All Documents Scanned ---"]}
    
    llm = ChatOpenAI(model="gpt-4o")
    prompt = f"Analyze for CRE risk: {state['current_doc_text']}"
    response = llm.invoke(prompt)
    return {"alerts": [f"FINDING: {response.content}"]}

# 4. Build Graph
builder = StateGraph(ClosingState)
builder.add_node("scanner", scanner)
builder.add_node("auditor", auditor)

builder.add_edge(START, "scanner")
builder.add_edge("scanner", "auditor")
builder.add_edge("auditor", END)

graph = builder.compile()

# 5. Execute
if __name__ == "__main__":
    initial_input = {
        "vdr_path": "./my_deal_folder", 
        "processed_files": [], 
        "alerts": [], 
        "current_doc_text": ""
    }
    final_state = graph.invoke(initial_input)
    print("\n".join(final_state["alerts"]))
    
    
    ## display_disclaimer()
    input("\nExecution finished. Press Enter to Close...") 
