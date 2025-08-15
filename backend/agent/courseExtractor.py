from .queryDB import query_database
from .pydanticModels import CourseAttributes,AgentState
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
import json
import re

llm = ChatOpenAI(model = "gpt-4.1-nano")

llm_for_course_attributes = llm.with_structured_output(CourseAttributes)

llm_with_json = ChatOpenAI(
    model="gpt-4.1-nano",
    model_kwargs={"response_format": {"type": "json_object"}},
)

def extract_course_attributes_from_query(state: AgentState):
    """
    Extract course numbers and course titles from a user's query using an LLM parser.

    The function parses the user's query for explicit course numbers and general topics,
    expanding vague topics into specific course titles and appending college and department information.

    Parameters
    ----------
    state : AgentState
        The current state containing:
        - query : str, the student's query.
        - college : str, default college name.
        - department : str, default department name.

    Returns
    -------
    dict
        Dictionary containing:
        - "course_numbers": List of extracted course numbers (e.g., ["DS5220"]).
        - "course_titles": List of extracted or expanded course titles with college and department appended.
    """

    query = state.query
    college = state.college
    dept = state.department

    dept_code = dept.strip().split()[-1]

    prompt = f"""
    You are an intelligent parser designed to extract course-related information from user input.

    OBJECTIVE:
    Extract two things from the user's message:
    1. Course numbers — formatted as a department code followed by digits (e.g., "DS5220", "CS6220").
    2. Course titles — subject-based or descriptive names, even vague topics.

    ---

    INSTRUCTIONS:

    - First, check if the user explicitly mentions a college or department in their query.
    - If yes, use those values instead of the default ones.
    - If not, default to:
        - College = "{college}"
        - Department Code = "{dept_code}"

    - Your final output should be a valid JSON object in the exact format:
    {{
    "course_numbers": [list of strings],
    "course_titles": [list of strings]
    }}

    ---

    GUIDELINES:

    1. Course Numbers:
    - Extract all course numbers (e.g., "DS5220", "INPR6000") if they appear.
    - Return in "course_numbers".

    2. Course Titles:
    - If user is asking for substitues of any course then included those generate 2 to 3 versions of that titles and return them also.
    - Extract all specific course titles mentioned.
    - If a topic is vague (like "AI", "biology", "sports", "business", "law", "ML", "research"):
        - Expand it into exactly 3 specific course titles relevant to that topic.
        - If expansion is unclear, use: "Special Topics in {dept_code}"
    - For each course title:
        - Append the college and department code using commas in fromt of course tiltes like below:
        "Course Title, College, Departemnt"

    3. Do not hallucinate course numbers or department codes.
    4. Return empty lists if nothing valid is found.
    5. Do not return explanations, markdown, headings, or extra text — just the JSON.

    ---

    EXAMPLES:

    Input:
    "I'm interested in DS5220 and also want something on gene editing."
    Output:
    {{
    "course_numbers": ["DS5220"],
    "course_titles": ["Gene Editing and Genomics ..."]
    }}

    Input:
    "Tell me about biology or tech courses in CS5200."
    Output:
    {{
    "course_numbers": ["CS5200"],
    "course_titles": [
        "Computational Biology ...",
        "Biomedical Data Analytics ...",
        "Emerging Tech and Innovation ..."
    ]
    }}

    Input:
    "Show me something in AI from DS5220."
    Output:
    {{
    "course_numbers": ["DS5220"],
    "course_titles": [
        "Neural Networks and Deep Learning ...",
        "Ethical AI Systems ...",
        "AI for Decision Making ..."
    ]
    }}

    Input:
    "Tell me about courses on law or legal studies."
    Output:
    {{
    "course_numbers": [],
    "course_titles": [
        "Constitutional Law and Policy ...",
        "Criminal Justice Systems ...",
        "Intellectual Property Law ..."
    ]
    }}

    ---

    ✏️ STUDENT QUERY:
    "{query}"

    """


    response = llm_for_course_attributes.invoke(prompt)

    return {"course_numbers":response.course_numbers,"course_titles":response.course_titles}

def get_course_details(state:AgentState):
    """
    Query the course database for detailed course information based on course numbers or titles.

    Parameters
    ----------
    state : AgentState
        The current state containing:
        - course_numbers : List of course numbers extracted from user query.
        - course_titles : List of course titles extracted from user query.

    Returns
    -------
    dict
        Dictionary containing:
        - "courses_from_users_query": List of course details matching the user's query, including
          course number, title, description, department, college, credit hours, and prerequisites.
    """
    course_numbers = state.course_numbers
    course_titles = state.course_titles
    
    response = query_database(course_numbers=course_numbers,course_titles=course_titles)

    return {
        "courses_from_users_query": response,
    }

# def summarize_course_extraction_for_user(state: AgentState):
#     query = state.query
#     extracted_courses = state.courses_from_users_query

#     prompt =  f"""
#     You are a course selection assistant.

#     A student asked: "{query}"

#     The following is a list of potentially relevant courses extracted based on their query:
#     {json.dumps(extracted_courses, indent=2)}

#     You will also be provided with full course descriptions. Use them to determine which courses best match the student’s intent.

#     Your tasks:
#     - Understand what the student is asking for.
#     - From the extracted list, choose only those courses that best match the student’s query.
#     - Return at least five to eight courses if there are more than five else return the unique courses you get. 
#     - Respect any constraints mentioned, such as department, college, or similarity to another course.
#     - Use the course title, description, department, and college to decide relevance.
#     - At the end, provide a single overall **reason** explaining why the final list of selected courses addresses the user’s query.

#     Return your response in the following strict JSON format (and nothing else):

#     {{
#         "response":{{
#             "matched_courses": [
#                 {{
#                 "course_number": "<e.g., INPR6000>",
#                 "title": "<Full Course Title>",
#                 "description": "<Full course description>",
#                 "department": "<Department Name>",
#                 "college": "<College Name>",
#                 "credit_hours": "<credits_hours>",
#                 "prerequisites": "<Comma-separated list or 'None'>"
#                 }}
#             ],
#             "reason": "<Short explanation of why this list of courses matches the student's query>"
#         }}
#     }}
#     Only return valid JSON. Do not include any other commentary or explanation and remember the number of courses to return and return only unique courses.
#     """
#     response = llm_with_json.invoke(prompt).content
#     response = json.loads(response)

#     return {"courses_from_users_query_after_summarization":response,
#             "messages":[["AI","CourseExtractor",[response]]]
#             }

def summarize_course_extraction_for_user(state: AgentState):
    """
    Deduplicate and rank courses extracted from a user's query, returning a concise list
    of relevant courses along with a reasoning summary.

    The function removes duplicates based on course number and title, and prioritizes courses
    based on department and college relevance.

    Parameters
    ----------
    state : AgentState
        The current state containing:
        - query : str, the user's original query.
        - courses_from_users_query : List of extracted courses from the previous step.
        - college : str, default college name.
        - department : str, default department name.

    Returns
    -------
    dict
        Dictionary containing:
        - "courses_from_users_query_after_summarization": A structured response with:
            - "matched_courses": List of deduplicated, sorted courses relevant to the query.
            - "reason": Explanation of how the list matches the student's query.
        - "messages": Log messages including the structured response for debugging or tracking.
    """
    query = state.query.lower()
    extracted_courses = state.courses_from_users_query
    college = state.college
    department = state.department

    # Step 1: Deduplicate based on (course_number + title)
    unique_courses_dict = {}
    for course in extracted_courses:
        key = (
            course.get("course_number", "").strip().upper(),
            course.get("title", "").strip().lower()
        )
        if key not in unique_courses_dict:
            unique_courses_dict[key] = course
    unique_courses = list(unique_courses_dict.values())

    # Step 2: Matching helper
    def match_score(course):
        dept = course.get("department", "").lower()
        clg = course.get("college", "").lower()

        # Give 0 to department match, 1 to college match, 2 to others
        if dept == department:
            return 0
        elif clg == college:
            return 1
        else:
            return 2

    # Step 3: Sort courses by match score, then dept name, then course number
    sorted_courses = sorted(unique_courses, key=lambda c: (match_score(c), c.get("department", ""), c.get("course_number", "")))

    # Step 4: Return response with explanation
    response = {
        "response": {
            "matched_courses": sorted_courses,
            "reason": f"Here is a list of unique courses provided by Northeastern University based on your query."
        }
    }

    return {
        "courses_from_users_query_after_summarization": response,
        "messages": [["AI", "CourseExtractor", response]]
    }

