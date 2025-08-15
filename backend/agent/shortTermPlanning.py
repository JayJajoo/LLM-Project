from .pydanticModels import AgentState
from langchain_openai.chat_models import ChatOpenAI
from dotenv import load_dotenv
import json
from .states import get_short_planning_state
from .queryDB import query_database
load_dotenv()

llm = ChatOpenAI(model = "gpt-4.1-nano")

def get_attributes_for_short_plan(state: AgentState):
    
    """
    Generate a list of new, advanced course titles for a student based on their prior coursework and academic goals.

    Args:
        state (AgentState): The current agent state containing:
            - query (str): Student's completed coursework and/or academic goal.
            - college (str): College name.
            - department (str): Department name.

    Process:
        - Analyzes student's completed subjects.
        - Suggests 5–7 distinct, advanced topics not previously studied.
        - Appends "– {department}, {college}" to each course title.
        - Avoids foundational (5XXX-level) courses, overlapping topics, and redundant suggestions.
        - Ensures only one course is chosen from similar categories (e.g., "Deep Learning" vs "Applied Deep Learning").

    Returns:
        dict: Dictionary containing:
            {"course_titles": [list of new course titles]}
    """

    query = state.query
    college = state.college
    department = state.department

    prompt = f"""
    You are an expert academic advisor in the {department} department at {college}.
    A student is seeking a short academic plan with new subjects they haven't explored yet.
    They will provide their prior coursework and optionally a goal they are working towards.

    Your responsibilities:
    - Analyze the student's completed subjects.
    - If a goal (e.g., PhD in AI, role in cybersecurity, etc.) is mentioned, recommend topics aligned with that goal.
    - If no goal is specified, suggest diverse, relevant, and advanced topics from the department that are different from what the student already knows.
    - Only return titles of new topics that student has not covered — no explanations or descriptions.
    - For each suggested topic, append " – {department}, {college}" at the end of the title.
    - Avoid recommending foundational course which generally means course starting from 5XXX.
    - Avoid recommending anything that overlaps with what they have already studied or what you have already suggested.
    - Make sure you suggest only one course from overlapping or similar course like for eg. Deep Learning and then applied deep learning
    - Suggest atleast 5 courses.

    ---

    Output Format:
    Return a Python list of 5–7 strings.
    Each string should follow this format:
    "Topic Title – {department}, {college}"

    Example Output: (STRICT)
    {{"topics":[
    "Generative AI – {department}, {college}",
    "Secure Federated Learning – {department}, {college}",
    "Advanced Robotics and Perception – {department}, {college}",
    "Causal Inference in Machine Learning – {department}, {college}",
    "Ethics and Policy in Autonomous Systems – {department}, {college}"
    ]}}

    ---

    Example 1 (No Goal):
    Student Query:
    "I’ve completed Data Structures, Algorithms, Operating Systems, and DBMS."

    Output:
    {{"topics":[
    "Machine Learning Foundations – Computer Science, Northeastern University",
    "Cloud Computing and Microservices – Computer Science, Northeastern University",
    "Computer Vision Basics – Computer Science, Northeastern University",
    "Network Security – Computer Science, Northeastern University"
    ]}}

    ---

    Example 2 (With Goal):
    Student Query:
    "I’ve done Deep Learning and Transformers. I want to specialize in NLP for social good."

    Output:
    {{"topics":[
    "Bias and Fairness in NLP – Computer Science, Northeastern University",
    "AI for Humanitarian Applications – Computer Science, Northeastern University",
    "Multilingual Representation Learning – Computer Science, Northeastern University",
    "Low-Resource NLP Techniques – Computer Science, Northeastern University"
    ]}}

    ---

    Now generate a list of new, distinct subject or topic titles for the following student query:

    Student Query:
    \"\"\"{query}\"\"\"

    Return a valid JSON format list with topics that student hasn't covered, no explaination required.
    """
    
    response = llm.invoke(prompt,temperature=0.7).content
    response = json.loads(response)["topics"]
    return {"course_titles":response}

def get_unique_dicts(courses_list):
    """
    Remove duplicate course dictionaries based on course_number.

    Args:
        courses_list (list[dict]): List of course dictionaries, each containing a "course_number" key.

    Process:
        - Tracks unique course_numbers.
        - Keeps the first occurrence of each unique course_number.

    Returns:
        list[dict]: List of unique course dictionaries.
    """
    unique_dicts = []
    seen_keys = set()

    for d in courses_list:
        key = d["course_number"]
        if key not in seen_keys:
            seen_keys.add(key)
            unique_dicts.append(d)
    
    return unique_dicts

def get_course_details_for_short_term_planning(state:AgentState):
    """
    Retrieve detailed course information for a given list of course titles.

    Args:
        state (AgentState): The current agent state containing:
            - course_titles (list[str]): Course titles to look up.

    Process:
        - Queries the course database using course titles (no course numbers).
        - Removes duplicates using get_unique_dicts.

    Returns:
        dict: Dictionary containing:
            {"courses_from_users_query": [list of unique course dictionaries]}
    """
    courses_titles = state.course_titles
    courses_list = query_database(course_numbers=[],course_titles=courses_titles)
    return {"courses_from_users_query":get_unique_dicts(courses_list)}

def build_short_term_plan(state:AgentState):
    """
    Generate a tailored short-term academic plan for the student.

    Args:
        state (AgentState): The current agent state containing:
            - query (str): Student's academic goal or prior coursework description.
            - college (str): College name.
            - department (str): Department name.
            - courses_from_users_query (list[dict]): Detailed available course info.

    Process:
        - Selects up to 6 relevant courses aligned with the student’s goal.
        - Prefers courses from the same department or college.
        - Avoids overlap with previously studied topics.
        - Orders results from easiest to hardest (based on prerequisites).
        - Generates a brief, original (≤2 lines) summary of each course description.

    Returns:
        dict: Dictionary containing:
            {
                "short_term_plan": {
                    "content": {
                        "suggestions": [list of course dicts],
                        "explaination": str
                    }
                },
                "messages": [["AI", "ShortTermPlan", response_object]]
            }
    """
    goal = state.query
    college = state.college
    department  = state.department
    courses_list = state.courses_from_users_query
    courses_list_json = json.dumps(courses_list,indent=5)
    
    prompt = f"""
    You are an academic advisor at the {department} department of {college}.

    A student has shared their academic goal, and you are provided with a list of course options, each including:
    - title
    - course_number
    - description
    - college
    - department
    - prerequisites
    - credit_hours

    Student Goal:
    {goal}

    Preferred Context:
    Department: {department}
    College: {college}

    Your task:
    Return list of the course that student hasn't studied in the below specified JSON list format.

    From the given list of course dictionaries:
    - Suggest courses based on students previous coursework.
    - Select the most relevant courses (maximum 6)
    - Prioritize courses that align closely with the student's goal
    - Prefer courses from the same department or college
    - Avoid any course that overlaps with what the student likely already knows (based on title or description)
    - Sort the selected courses in increasing order of difficulty based on prerequisites
    - For each selected course, return a **brief and original summary** of its description (max 2 lines), NOT a copy of the original description
    - Do not return any course that student has already studied or has told you that he already has studied or completed this courses.

    ❗ Output format must be valid JSON ONLY — no extra text, no comments, no headings.

    Output Format (Strict JSON):
    {{
    "content": {{
        "suggestions": [
        {{
            "course_number": "string",
            "college": "string",
            "department": "string",
            "title": "string",
            "description": "Brief summary in your own words",
            "credit_hours": "string or int",
            "prerequisites": "string or list"
        }}
        ],
        "explaination": "1–2 lines on why this selection supports the goal."
    }}
    }}
    ---

    Available Courses:
    {courses_list_json}

    NOW RETURN A VALID JSON OBJECT ONLY. DO NOT COPY THE ORIGINAL DESCRIPTION. SUMMARIZE IT IN NEW WORDS IN UNDER 2 LINES.
    """

    response = llm.invoke(prompt).content
    response = json.loads(response)
    
    # print(json.dumps(response,indent=2))

    return {
        "short_term_plan":response,
        "messages":[["AI","ShortTermPlan",response]]
    }





