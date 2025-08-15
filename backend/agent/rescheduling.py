from dotenv import load_dotenv
from typing import List
import json
import re
from .pydanticModels import AgentState
from langchain_openai import ChatOpenAI
from .queryDB import query_database
import warnings
from langchain_core.messages import AIMessage

warnings.filterwarnings("ignore")
load_dotenv()

llm = ChatOpenAI(model = "gpt-4.1-nano")

llm_for_rescheduling_agent = ChatOpenAI(    
    model="gpt-4.1-nano",
    model_kwargs={"response_format": {"type": "json_object"}},
)

def extract_plan_index(state:AgentState):
    """
    Extract the numeric plan index from the user's intent string.

    Args:
        state (AgentState): The current agent state containing:
            - intent (str): A string in the format "reschedule_<number>".

    Returns:
        dict: {"plan_number_to_change": int} where the integer is the plan number to modify.
    """

    return {
        "plan_number_to_change":int(state.intent.strip().split("_")[-1])
    }

def get_course_numbers_from_plan(plan: dict) -> List[str]:
    """
    Retrieve all course numbers from a given academic plan.

    Args:
        plan (dict): Academic plan dictionary containing:
            - "semester_schedule" (list): List of semesters, each with "courses" (list of course dicts).

    Returns:
        list[str]: A list of all course numbers found in the plan.
    """
    course_numbers = []
    for semester in plan.get("semester_schedule", []):
        for course in semester.get("courses", []):
            course_number = course.get("course_number", "").strip()
            if course_number:
                course_numbers.append(course_number)
    return course_numbers

def extract_course_attributes_for_rescheduling(state: AgentState):
    """
    Determine which courses in a given plan should be replaced based on the user's rescheduling request.

    Args:
        state (AgentState): The current agent state containing:
            - plan_number_to_change (int): The plan index to modify.
            - semester_plans (list): All academic plans.
            - query (str): User's rescheduling request.
            - college (str), department (str), main_query (str): Additional context for planning.

    Process:
        - Extract valid course numbers from the current plan.
        - Prompt the LLM to map old course numbers to replacement course numbers/titles/null.
        - Filter replacements to ensure only valid courses from the current plan are included.

    Returns:
        dict: {"rescheduling_attributes": {old_course_number: new_course_number/title/null}}
    """
    plan_index = int(state.plan_number_to_change) - 1
    plan = state.semester_plans[plan_index]
    query = re.sub(r"(reschedule|restructure)\s+(plan|schedule)\s+(\d+)", "Reschedule the below plan according to instructions provided:\n", state.query)
    college = state.college
    main_query = state.main_query
    dept = state.department

    valid_course_numbers = get_course_numbers_from_plan(plan)

    prompt = f"""
    TASK:
    You are an academic planning assistant. Return a structured mapping of **course numbers to be removed** and their **intended replacements**, based only on the user's request.

    CURRENT PLAN COURSE NUMBERS:
    {valid_course_numbers}

    USER QUERY:
    "{query}"

    STUDENT INFO:
    - Goal: "{main_query}"
    - College: "{college}"
    - Department: "{dept}"

    RULES:
    1. Only consider course numbers from the CURRENT PLAN for removal.
    2. Ignore and exclude any course numbers **not** in the list above.
    3. The replacement value can be:
    - A natural language string or the user suggested replacement subjects like (e.g., "some AI-related course") if the user doesnt provide you with the new course number.
    - Another course number (e.g., "INPR6000")
    - Or null (if no replacement is given).
    4. Ignore any additions if no removal was mentioned.
    5. Do NOT make up course numbers if they are not explicitly provided.
    6. Follow rule number 3 strictly.

    Output format (return only this JSON):
    {{
    "replacements": {{
        "OLD_COURSE_NUM_1": "NEW_COURSE_NUM or STRING or null",
        "OLD_COURSE_NUM_2": "..."
    }}
    }}
    """

    response = llm_for_rescheduling_agent.invoke(prompt).content

    replacements = json.loads(response)

    replacements = replacements["replacements"]

    current_crns = {}

    for semester in plan["semester_schedule"]:
        for course in semester["courses"]:
            current_crns[course["course_number"]] = True    

    filtered_repl = {}

    for course_number,replc in replacements.items():
        if replc is not None or replc!="null":
            found = current_crns.get(course_number,False)
            if found and filtered_repl.get(course_number) is None:
                filtered_repl[course_number] = replc
    
    return {"rescheduling_attributes": filtered_repl}

def replace_courses(state:AgentState):
    """
    Apply course replacements in the target plan and update total credits.

    Args:
        state (AgentState): The current agent state containing:
            - rescheduling_attributes (dict): Mapping of old course numbers to replacement values.
            - plan_number_to_change (int): Index of the plan to modify.
            - semester_plans (list): All academic plans.

    Process:
        - For each course in the specified plan, check if a replacement is required.
        - If a replacement is a valid course number, query the DB by course number.
        - If a replacement is a title/description, query the DB by course title.
        - Update the course in the plan, adjust semester and total credits.
        - Track old→new course mappings for reporting.

    Returns:
        dict: {
            "semester_plans": [updated plans],
            "rescheduling_attributes": {old_course_title: new_course_title}
        }
    """

    replacements = state.rescheduling_attributes
    plan_number = state.plan_number_to_change
    plans = state.semester_plans
    plan = state.semester_plans[plan_number-1]
    new_mapping = {}
    new_total_credits = 0
    for semester_idx,semester in enumerate(plan["semester_schedule"]):
        semester_credits = 0
        for course_idx,course in enumerate(semester["courses"]):
            course_number = course["course_number"].strip()
            replacement_value = replacements.get(course_number,None)
            if replacement_value:
                replacement_value = replacement_value.strip()
                match = re.search(r"(^[A-Z]+\d{4})",replacement_value)
                if match:
                    replacement = query_database(course_numbers=[replacement_value],course_titles=[])[0]
                else:
                    replacement = query_database(course_numbers=[],course_titles=[replacement_value],k=1)[0]
                new_mapping[f"{course_number} - {course["title"]}"] = f"{replacement["course_number"]} - {replacement["title"]}"
                
                plan["semester_schedule"][semester_idx]["courses"][course_idx] = replacement            
            
            semester_credits += int(plan["semester_schedule"][semester_idx]["courses"][course_idx]["credit_hours"].split(" ")[-1])
        
        plan["semester_schedule"][semester_idx]["total_credits"] = semester_credits
        
        new_total_credits+=semester_credits
    
    plan["total_credits"] = new_total_credits
    
    plans[plan_number-1] = plan


    return {
            "semester_plans":plans,
            "rescheduling_attributes":new_mapping
    }

def generate_summary_for_rescheduled_plan(state: "AgentState"):
    """
    Create a short summary explaining changes in the rescheduled plan.

    Args:
        state (AgentState): The current agent state containing:
            - main_query (str): Student's academic goal.
            - semester_plans (list): All academic plans (including updated one).
            - plan_number_to_change (int): Index of the updated plan.
            - rescheduling_attributes (dict): Mapping of replaced courses.

    Process:
        - Generate a text prefix listing all replaced courses.
        - Ask the LLM to summarize the updated plan in 2–3 lines:
            - What the plan now emphasizes.
            - How it supports the goal.
        - Append this reasoning to the updated plan.

    Returns:
        dict: {
            "semester_plans": [updated plans with reasoning],
            "messages": [["AI", "Rescheduling", [updated_plan]]]
        }
    """

    goal = state.main_query
    plans = state.semester_plans
    update_index = state.plan_number_to_change - 1
    updated_plan = state.semester_plans[update_index]
    replacements = state.rescheduling_attributes 

    prefix = f"Here's you updated Plan {update_index+1}:<br/>Successfully Replaced:<br/>"

    for idx,(k,v) in enumerate(replacements.items()):
        prefix+=f"{idx+1}. {k} ---> {v}<br/>"

    prompt = f"""
    You are an academic advisor. Given the student's goal and their updated academic plan, write ONLY a 2–3 line summary describing:

    - What the new plan emphasizes
    - How it supports the student's goal

    Do NOT include headings, lists, or anything other than the summary itself.

    Goal:
    {goal}

    Updated Plan:
    {updated_plan}
    """

    response = llm.invoke(prompt).content.strip()

    updated_plan["reason_behind_planning"] = prefix +"\n"+response

    plans[update_index] = updated_plan

    return {
        "semester_plans":plans,
        "messages": [["AI","Rescheduling",[updated_plan]]]
    }
    
