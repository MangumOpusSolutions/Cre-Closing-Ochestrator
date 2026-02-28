import os
from typing import TypedDict, List, Annotated
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

load_dotenv()

# 1. Define the Shared State
class ClosingState(TypedDict):
    vdr_path: str
    processed_files: List[str]
    checklist_status: dict
    alerts: List[str]
    current_doc_text: str

# 2. Node: Document Discovery (Scan Folder)
def scan_vdr(state: ClosingState):
    all_files = os.listdir(state['vdr_path'])
    new_files = [f for f in all_files if f not in state['processed_files']]
    
    if not new_files:
        return {"current_doc_text": "None", "processed_files": state['processed_files']}
    
    target = new_files[0]
    # In production, use a PDF parser here. For now, we simulate reading:
    with open(f"{state['vdr_path']}/{target}", "r") as f:
        content = f.read()
        
    return {
        "current_doc_text": content, 
        "processed_files": state['processed_files'] + [target]
    }

# 3. Node: The Auditor (OpenAI Logic)
def audit_document(state: ClosingState):
    if state['current_doc_text'] == "None":
        return {"alerts": []}
    
    llm = ChatOpenAI(model="gpt-4o")
    # Using the refined prompt from above
    response = llm.invoke(f"Analyze this CRE doc: {state['current_doc_text']}")
    
    # logic to parse response and update checklist
    return {"alerts": [response.content]}

# 4. Node: Communicator (Human Notification)
def send_notifications(state: ClosingState):
    for alert in state['alerts']:
        print(f"🚀 [AGENT ALERT]: {alert}")
    return {"alerts": []}

# 5. Build the Graph
builder = StateGraph(ClosingState)

builder.add_node("scanner", scan_vdr)
builder.add_node("auditor", audit_document)
builder.add_node("notifier", send_notifications)

builder.add_edge(START, "scanner")
builder.add_edge("scanner", "auditor")
builder.add_edge("auditor", "notifier")
builder.add_edge("notifier", "scanner") # Loop back to check for more files

# 6. Execution Loop with a Break Condition
graph = builder.compile()

initial_state = {
    "vdr_path": "./my_deal_folder",
    "processed_files": [],
    "checklist_status": {},
    "alerts": [],
    "current_doc_text": ""
}

# Run the agent
# Note: In production, you would use a 'condition' to stop the loop when no files remain.