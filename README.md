# NexusBA: Agentic Business Analysis Orchestrator 

NexusBA is an advanced AI-driven platform designed to bridge the gap between messy stakeholder conversations and structured technical documentation. Using a **multi-agent graph architecture**, it automates the extraction of user stories and performs a rigorous technical audit to identify logical gaps before development begins.

## Key Features

* **Multi-Agent Workflow:** Utilizes **LangGraph** to orchestrate a specialized 'Architect' node for drafting requirements and a 'Critic' node for automated gap analysis.
* **Version Control & History:** Integrated **SQLite** backend that tracks every iteration of a project, allowing users to compare versions with a built-in "Git-style" diff engine.
* **Automated Technical Audit:** Identifies missing edge cases, security risks, and logical inconsistencies in stakeholder notes using high-speed inference.
* **Secure Authentication:** Full user registration and login system to ensure project privacy and data persistence.
* **Export Engine:** One-click export of requirements and audits into **Markdown (.md)** format for seamless integration with Jira, Notion, or GitHub.

## Technical Stack

* **Orchestration:** LangGraph, LangChain
* **Inference:** Groq LPU (Llama 3 / Mixtral)
* **Backend:** Python 3.13, SQLite
* **Frontend:** Streamlit
* **Authentication:** Streamlit-Authenticator (BCrypt hashing)

## Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone [https://github.com/Tavishvj/NexusBA-AI-Agent.git](https://github.com/Tavishvj/NexusBA-AI-Agent.git)
   cd NexusBA-AI-Agent
   
2. **Set Up Virtual Environment:**
python -m venv .venv
.venv\Scripts\activate

3.**Install Dependencies:**
pip install -r requirements.txt

4.**Environment Variables:**
Create a .env file in the root directory and add your Groq API Key:
GROQ_API_KEY=your_api_key_here

5.**Run the Application:**
streamlit run main_web.py


 **Why LangGraph?**
Unlike standard linear LLM chains, NexusBA uses a Stateful Graph. This allows the system to:
Generate a requirement draft.
Pass that draft to a Critic node.
Use a conditional edge to decide if the requirements are "complete" or if they need to loop back for further refinement—mimicking a real-world Senior BA's thought process.

 **License**
Distributed under the MIT License. See LICENSE for more information.
Developed by Tavish
