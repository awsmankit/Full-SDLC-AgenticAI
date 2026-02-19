# 🤖 Multi-Agent QA System

A fully offline, autonomous multi-agent system that simulates a complete **Software Development Life Cycle (SDLC)** organization using **Ollama + Qwen** and **Python**.

This system orchestrates a team of specialized AI agents to take a product idea from concept to code, including testing and bug reporting.

## 🔄 The Workflow

The system follows a strict linear workflow mimicking a real-world software team:

1.  **Product Manager (PM)**
    - **Input**: User's Product Idea
    - **Output**: Market Requirements (MRS) & Software Requirements (SRS)
    - **Goal**: Define *what* to build.

2.  **Senior Developer**
    - **Input**: SRS
    - **Output**: Source Code (`src/`) & Unit Tests (`tests/test_unit.py`)
    - **Goal**: Implement the requirements.

3.  **Code Reviewer**
    - **Input**: Source Code & SRS
    - **Output**: Code Review Report & Approval Status
    - **Goal**: Ensure code quality and requirements coverage. *If rejected, the Developer iterates.*

4.  **Test Manager**
    - **Input**: SRS
    - **Output**: System Test Specification (STS)
    - **Goal**: Define the high-level test strategy.

5.  **Test Lead**
    - **Input**: STS
    - **Output**: System Test Execution Plan (STEP)
    - **Goal**: Plan specific test cases and environments.

6.  **Automation QA**
    - **Input**: STEP
    - **Output**: Python Automation Scripts (`tests/test_app.py`)
    - **Goal**: Write end-to-end automation tests.

7.  **Manual QA**
    - **Input**: STEP
    - **Output**: Manual Test Cases & Bug Reports
    - **Goal**: Simulate manual testing and find bugs.

## 🚀 Getting Started

Follow these steps to set up and run the system on your local machine.

### Prerequisites

1.  **Ollama**: Install from [ollama.com](https://ollama.com) and ensure it's running (`ollama serve`).
2.  **Python 3.10+**: Ensure Python is installed.
3.  **uv**: An extremely fast Python package installer.
    ```bash
    pip install uv
    ```
4.  **Qwen Models**: Pull the required models.
    ```bash
    ollama pull qwen2.5:7b
    ollama pull qwen2.5-coder:7b
    ```

### Installation

1.  **Fork & Clone the Repository**
    ```bash
    git clone https://github.com/YOUR_USERNAME/Full-SDLC-AgenticAI.git
    cd Full-SDLC-AgenticAI
    ```

2.  **Install Dependencies**
    The system uses `uv` for dependency management.
    ```bash
    uv sync
    ```

### Running the Application

To start the agentic workflow, run the `src.main` module with your product idea.

```bash
uv run python -m src.main "Build a simple To-Do List app with Streamlit" --personality software
```

**Options:**
- `product_idea`: The description of the app you want to build.
- `--personality`: Choose between `software` (default) or `medical` (for regulated environments).

## 📂 Output Artifacts

All generated files are saved in the `artifacts/<app_name>/` directory:

- `src/`: Generated source code and unit tests.
- `requirements/`: MRS and SRS documents.
- `testing/`: Test Plans, Strategies, and Automation Scripts.
- `bugs/`: Manual bug reports.

## 🛠️ Tech Stack

- **LLM Engine**: Ollama (Local Inference)
- **Models**: `qwen2.5:7b` (Logic), `qwen2.5-coder:7b` (Coding)
- **Orchestration**: LangGraph (State Machine)
- **Language**: Python
- **UI**: Rich (Console Interface)

## 📜 License

MIT License
