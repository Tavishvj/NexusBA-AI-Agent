import os
from typing import TypedDict
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

# Load API Key
load_dotenv()

# 1. Define the State
class AgentState(TypedDict):
    raw_input: str
    draft_requirements: str
    gap_analysis: str

# 2. Initialize Model
model = ChatGroq(
    model="llama-3.3-70b-versatile", 
    temperature=0.2 # Kept low for consistency in logic
)

# --- NODE 1: SENIOR BA (The Deconstructor) ---
# --- NODE 1: SENIOR BA (The Deconstructor) ---
def drafting_node(state: AgentState):
    prompt = f"""
    You are an expert Senior Business Analyst. 
    Deconstruct the raw notes into multiple, distinct User Stories.

    STRICT FORMATTING RULES:
    1. For the User Story section, you MUST bold the keywords like this: 
       **As a** [role], **I want** [feature], **so that** [value].
    2. The title "**Acceptance Criteria**" must be bold.
    3. Within the Scenarios, you MUST bold the keywords **Given**, **When**, and **Then**.

    RAW NOTES: 
    {state['raw_input']}
    
    Example Output Structure:
    ### [Story Title]
    - **User Story**: **As a** shopper, **I want** a green button, **so that** I can checkout fast.
    - **Acceptance Criteria**:
        - Scenario: Direct Redirect
          **Given** I am on the product page
          **When** I click the Buy Now button
          **Then** I am taken to the checkout page
    ---
    """
    response = model.invoke(prompt)
    return {"draft_requirements": response.content}


    

# --- NODE 2: SENIOR SYSTEMS ANALYST (The Audit) ---
def critic_node(state: AgentState):
    prompt = f"""
    You are a Senior Systems Analyst performing a Technical Audit on the following requirements:
    {state['draft_requirements']}
    
    Evaluate the logic across these 3 pillars:
    1. **Gap Analysis**: For EACH user story above, identify one missing edge case or logical flaw (e.g., "What happens if the API fails?").
    2. **Technical Constraints**: List specific Non-Functional Requirements (Performance, Security, Data Privacy) relevant to these stories.
    3. **Implementation Score**: Rate the 'Definition of Ready' from 1-10 and list what is missing to reach a 10.
    """
    response = model.invoke(prompt)
    return {"gap_analysis": response.content}

# 3. Build Graph
workflow = StateGraph(AgentState)
workflow.add_node("writer", drafting_node)
workflow.add_node("critic", critic_node)
workflow.set_entry_point("writer")
workflow.add_edge("writer", "critic")
workflow.add_edge("critic", END)
app = workflow.compile()