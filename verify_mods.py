import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

try:
    print("Importing config...")
    from src.core.config import AGENT_CONFIG
    print("Config imported. ProductManager name:", AGENT_CONFIG["ProductManager"]["name"])

    print("Importing schemas...")
    from src.core.schemas import TestLeadOutput
    
    # Check if task_assignments field is gone
    if "task_assignments" not in TestLeadOutput.model_fields:
        print("Confirmed: task_assignments removed from TestLeadOutput.")
    else:
        print("ERROR: task_assignments still in TestLeadOutput!")

    print("Importing New Agent Classes...")
    from src.agents import TestLeadAgent
    
    print("Successfully imported all new agent classes.")
    
    agent = TestLeadAgent()
    if "task_assignments.md" not in agent.allowed_outputs:
        print("Confirmed: task_assignments.md removed from allowed_outputs.")
    else:
        print("ERROR: task_assignments.md still in allowed_outputs!")
       
    print("Checking Workflow Construction...") 
    from src.workflow.graph import create_qa_graph
    app = create_qa_graph()
    print("Graph compiled successfully.")

    print("Verification Successful!")

except Exception as e:
    print(f"Verification Failed: {e}")
    sys.exit(1)
