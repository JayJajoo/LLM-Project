from pydanticModels import AgentState,UserIntent
import re
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

llm = ChatOpenAI(model = "gpt-4.1-nano")

llm_for_intent_check = llm.with_structured_output(UserIntent)

def check_intent(state: AgentState):
    message: str = state.query.strip()

    match = re.search(r"(reschedule|restructure)\s+(plan|schedule)\s+(\d+)", message, re.IGNORECASE)
    if match:
        plan_number = match.group(3)
        return {"intent": f"reschedule_{plan_number}"}

    prompt = """
    You are a classification agent. Classify the user's query into one of these intent classes:
    ["greeting", "course_details", "build_schedule", "short_term_planning"]

    Respond with ONLY the class name. Do not explain.

    Intent meanings:
    - "greeting" → when the user is simply greeting the assistant.
    - "course_details" → when the user is asking for course names, descriptions, or prerequisites.
    - "build_schedule" → when the user is asking for help building or modifying a course schedule, study plan, or alternative paths for a broad career goal.
    - "short_term_planning" → when the user provides a specific goal and tells what they’ve already studied, then asks what they should take next. This is typically a short-horizon request like “next semester” or “next courses,” but includes clear context of their background.

    Examples:

    User: Hi, how are you?
    Intent: greeting

    User: Hello there!
    Intent: greeting

    User: Can you give me details about the Data Science and AI courses?
    Intent: course_details

    User: I want to know about the DS2500 course.
    Intent: course_details

    User: Can you build a schedule for me to become a lawyer?
    Intent: build_schedule

    User: Help me create a study plan to become a certified dietician.
    Intent: build_schedule

    User: I can't take this NLP course. Can you tell me some other courses?
    Intent: build_schedule

    User: My college doesn't allow courses from CPS. Can you tell me what else I can take?
    Intent: build_schedule

    User: I've done OOP, Data Structures, and DBMS. I want to get into Machine Learning. What should I take next?
    Intent: short_term_planning

    User: I completed Deep Learning and NLP. I want to become an ML Engineer — suggest my next 5 courses.
    Intent: short_term_planning

    User: Taken Stats, Python, and Intro to AI. What are some advanced courses I can do this fall to specialize in NLP?
    Intent: short_term_planning

    Now classify:
    User: {user_query}
    Intent:

    """
    
    prompt_template = ChatPromptTemplate.from_template(prompt)
    formatted_prompt = prompt_template.format_messages(user_query=message)
    response = llm_for_intent_check.invoke(formatted_prompt).intent
    return {"intent": str(response)}

def intent_based_router(state:AgentState):
    intent = state.intent
    if intent=="build_schedule":
        return "build_schedule"
    elif intent=="course_details":
        return "course_details"
    elif intent=="greeting":
        return "greeting"
    elif intent=="short_term_planning":
        return "short_term_planning"
    elif intent.split("_")[0]=="reschedule":
        return "reschedule"
