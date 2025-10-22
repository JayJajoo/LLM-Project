# AI Powered NEU Course Planner

An intelligent academic planning assistant that leverages Large Language Models (LLMs) and multi-agent frameworks to automate course selection, schedule generation, and academic planning for university students.

[![Demo](https://img.shields.io/badge/Demo-Watch%20Video-blue)](https://drive.google.com/file/d/1X7VfZkQ-t0LlTREotseXJpb9ZeZMvxSE/view?usp=drive_link)

## 📋 Overview

This project addresses the challenges students face in academic course planning by developing an AI-powered assistant that automates the creation, modification, and suggestion of academic schedules. Built with a multi-agent framework using LangGraph, the system provides personalized, constraint-aware academic plans while significantly reducing manual effort.

### Key Achievements
- **100% Course Retrieval Accuracy**: Precise course matching using semantic search
- **95-96% Time Reduction**: Compared to manual course planning
- **92% Topic Coverage**: When generating multiple plan variations
- **Constraint-Aware Planning**: Respects prerequisites, credit limits, and degree requirements

## ✨ Features

### 🎯 Intent Recognition (`routers.py`)
- Automatically classifies user queries into distinct categories
- Supports greetings, course details, schedule building, and short-term planning
- Pattern matching for rescheduling requests

### 📚 Course Information Retrieval (`courseExtractor.py`, `queryDB.py`)
- Semantic search using OpenAI embeddings and Chroma vector database
- Expands vague topics (e.g., "AI") into specific course recommendations
- Retrieves comprehensive course details including prerequisites, credits, and descriptions

### 🗓️ Multi-Semester Schedule Planning (`planning.py`)
- Generates diverse, complete academic plans across multiple semesters
- Respects prerequisites, credit constraints (min/max per semester)
- Places capstone projects appropriately in final semesters
- Creates multiple plan variations for different academic pathways

### 🔄 Dynamic Rescheduling (`rescheduling.py`)
- Modify existing plans by replacing specific courses
- Maintains credit balance and prerequisite requirements
- Supports substitution with specific courses or topic-based alternatives

### 🎓 Short-Term Planning (`shortTermPlanning.py`)
- Recommends next 5-7 courses based on completed coursework
- Prioritizes advanced topics aligned with career goals
- Sorts suggestions by difficulty and prerequisites

## 🏗️ Architecture

The system is built using a graph-based multi-agent architecture powered by LangGraph. The workflow orchestrates multiple specialized agents that handle different aspects of course planning, all coordinated through `backend/agent/agent.py`.

<img width="1431" height="765" alt="image" src="https://github.com/user-attachments/assets/467175b2-1b51-4a3a-b035-0ebf539cac83" />


### Workflow Overview

```
START → check_intent → [Route to appropriate workflow]
                              ↓
        ┌─────────────────────┼─────────────────────────────┐
        ↓                     ↓                             ↓
  build_schedule     course_details              short_term_planning
  reschedule              greeting               generate_more_plans
        ↓                     ↓                             ↓
   [Processing]        [Processing]                  [Processing]
        ↓                     ↓                             ↓
        └─────────────────────┴─────────────────────────────┘
                              ↓
                          FINISHED
```

### Detailed Agent Workflows

#### 1. **Schedule Building Pipeline**
```
reset_previous_plans
    ↓
rephrase_query_for_planning_schedule
    ↓
get_courses_for_building_schedule
    ↓
filter_courses_1 (Initial filtering + diversity)
    ↓
get_unique_plans (Eliminate duplicates)
    ↓
filter_courses_2 (Credit constraint refinement)
    ↓
planning_agent (Multi-semester distribution)
    ↓
final_duplicate_check (Cross-plan validation)
    ↓
final_course_addition_check (Credit completion)
```

#### 2. **Course Details Pipeline**
```
extract_course_attributes_from_query
    ↓
get_course_details
    ↓
summarize_course_extraction_for_user
```

#### 3. **Rescheduling Pipeline**
```
extract_plan_index
    ↓
extract_course_attributes_for_rescheduling
    ↓
replace_courses
    ↓
generate_summary_for_rescheduled_plan
```

#### 4. **Short-Term Planning Pipeline**
```
get_attributes_for_short_plan
    ↓
get_course_details_for_short_term_planning
    ↓
build_short_term_plan
```

### Core Components

1. **StateGraph (agent.py)**: Orchestrates workflow and manages conversation state using LangGraph
2. **AgentState (states.py)**: Pydantic-based state object that maintains context across conversation turns
3. **Data Models (pydanticModels.py)**: Structured schemas for user intents, course attributes, and planning parameters
4. **LLM (GPT-4.1-nano)**: Handles natural language understanding and generation
5. **Vector Database (queryDB.py → Chroma)**: Stores course embeddings for semantic search
6. **OpenAI Embeddings (text-embedding-3-large)**: Converts text to high-dimensional vectors
7. **Action Mapping (actionMap.py)**: Maps intents to appropriate workflow functions

### Key Design Principles

- **Modularity**: Each node is a specialized function with a single responsibility
- **State Management**: AgentState carries information across all nodes
- **Conditional Routing**: Intent-based routing ensures appropriate workflow execution
- **Error Handling**: Validation and fallback mechanisms at each stage
- **Iterative Refinement**: Multi-stage filtering and checking for plan quality

## 🛠️ Technologies Used

- **Python**: Core programming language
- **LangGraph**: Multi-agent orchestration and state management
- **LangChain**: LLM integration and tooling
- **OpenAI GPT-4.1-nano**: Large language model for reasoning
- **OpenAI Embeddings (text-embedding-3-large)**: Semantic text representations
- **Chroma DB**: Vector database for course storage and retrieval
- **Pydantic**: Data validation and schema definition

## 📦 Installation

### Prerequisites
- Python 3.9+
- OpenAI API key
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/JayJajoo/LLM-Project.git
cd LLM-Project

# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export OPENAI_API_KEY='your-api-key-here'
```

### Database Setup

Initialize the Chroma vector database with course data (if not already set up):

```bash
cd backend
python -c "from agent.queryDB import initialize_database; initialize_database()"
```

## 🚀 Usage

### Running the Assistant

```bash
cd backend
python app.py
```

The assistant will start and you can interact with it through the command line interface.

### Testing

The project includes testing utilities:

```bash
# Run the Jupyter notebook for interactive testing
cd backend
jupyter notebook planTester.ipynb
```

Test results and LLM responses are logged in:
- `llmResponses.json`: General LLM interaction logs
- `llmResponses4plans.json`: Planning-specific response logs
- `planTesting.json`: Test cases and results

### Example Queries

**Course Details:**
```
"Tell me about DS5220"
"What machine learning courses are available?"
```

**Schedule Planning:**
```
"I want to become a data scientist. Create a course plan."
"Build me a schedule for specialization in AI/ML"
```

**Short-Term Planning:**
```
"I've completed DS5010 and DS5020. What should I take next to become an ML engineer?"
```

**Rescheduling:**
```
"Reschedule plan 3 - replace DS5220 with a deep learning course"
```

## 📁 Project Structure

```
LLM-Project/
├── backend/
│   ├── agent/
│   │   ├── .gitignore
│   │   ├── actionMap.py              # Action mapping for workflow
│   │   ├── agent.py                  # Main StateGraph orchestration
│   │   ├── courseExtractor.py        # Course extraction and summarization
│   │   ├── greeting.py               # Greeting handler
│   │   ├── planning.py               # Multi-semester schedule generation
│   │   ├── pydanticModels.py         # Data models and schemas
│   │   ├── queryDB.py                # Vector database interactions
│   │   ├── rescheduling.py          # Plan modification logic
│   │   ├── routers.py               # Intent recognition and routing
│   │   ├── shortTermPlanning.py     # Next-step course recommendations
│   │   └── states.py                # AgentState definition
│   ├── app.py                       # Main application entry point
│   ├── llmResponses.json            # LLM response logs
│   ├── llmResponses4plans.json      # Planning response logs
│   ├── planTester.ipynb             # Testing notebook
│   ├── planTesting.json             # Test cases and results
│   └── requirements.txt             # Python dependencies
└── README.md
```

## 📊 Performance Results

### Course Retrieval
- **Accuracy**: 100% for both course numbers and semantic topics

### Topic Coverage
- **Single Plan**: 83% per query, 85% overall
- **Four Plans**: 90% per query, 92% overall

### Credit Matching
- **Single Plan**: 62.5% exact match, 37.5% exceeded
- **Four Plans**: 66.7% exact match, 33.3% exceeded

### Time Efficiency
- **95-96% reduction** compared to manual planning

## 🔮 Future Directions

- **Real-time University System Integration**: Connect with live course catalogs and enrollment systems
- **Advanced User Profiles**: Store detailed academic history, grades, and preferences
- **Feedback Loop**: Implement reinforcement learning from user feedback
- **Performance Optimization**: Caching strategies and batching for LLM calls
- **Mobile Application**: Develop iOS/Android apps for on-the-go planning

## ⚠️ Known Limitations

- **LLM Hallucinations**: Occasional generation of non-existent courses (mitigated by database validation)
- **Prerequisite Data Dependency**: Accuracy relies on complete prerequisite information
- **Credit Balancing**: Rare edge cases with slight credit deviations
- **Context Window**: May struggle with very long, complex conversations
- **Unforeseen Constraints**: Limited handling of highly specific preferences (e.g., time-based constraints)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is available for educational and research purposes.

## 👤 Author

**Jay Vipin Jajoo**
- Email: jajoo.jay@northeastern.edu
- GitHub: [@JayJajoo](https://github.com/JayJajoo)

## 📚 References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/tutorials/plan-and-execute/plan-and-execute/)
- [LangSmith Docs](https://docs.smith.langchain.com/)
- [OpenAI Platform](https://platform.openai.com/docs/overview)
- [Chroma Documentation](https://docs.trychroma.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

## 🎥 Demo

Watch the full project demo: [Course Planner Demo Video](https://drive.google.com/file/d/1X7VfZkQt0LlTREotseXJpb9ZeZMvxSE/view?usp=drive_link)

---

**Note**: This project was developed as part of academic research into AI-powered educational tools and multi-agent systems.
