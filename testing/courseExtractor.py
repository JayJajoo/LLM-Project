from queryDB import query_database
from pydanticModels import CourseAttributes,AgentState
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
import json

llm = ChatOpenAI(model = "gpt-4.1-nano")
llm_for_course_attributes = llm.with_structured_output(CourseAttributes)
llm_with_json = ChatOpenAI(
    model="gpt-4.1-nano",
    model_kwargs={"response_format": {"type": "json_object"}},
)

def extract_course_attributes_from_query(state: AgentState):
    query = state.query
    college = state.college
    dept = state.department

    dept_code = dept.strip().split()[-1]

    prompt = f"""
    You are an intelligent parser designed to extract course-related information from user input.

    🎯 OBJECTIVE:
    Extract two things from the user's message:
    1. Course numbers — formatted as a department code followed by digits (e.g., "DS5220", "CS6220").
    2. Course titles — subject-based or descriptive names, even vague topics.

    ---

    🧠 INSTRUCTIONS:

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

    📋 GUIDELINES:

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

    📚 EXAMPLES:

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
    course_numbers = state.course_numbers
    course_titles = state.course_titles
    
    response = query_database(course_numbers=course_numbers,course_titles=course_titles)

    return {
        "courses_from_users_query": response,
    }

def summarize_course_extraction_for_user(state: AgentState):
    query = state.query
    extracted_courses = state.courses_from_users_query

    prompt =  f"""
    You are a course selection assistant.

    A student asked: "{query}"

    The following is a list of potentially relevant courses extracted based on their query:
    {json.dumps(extracted_courses, indent=2)}

    You will also be provided with full course descriptions. Use them to determine which courses best match the student’s intent.

    Your tasks:
    - Understand what the student is asking for.
    - From the extracted list, choose only those courses that best match the student’s query.
    - Respect any constraints mentioned, such as department, college, or similarity to another course.
    - Use the course title, description, department, and college to decide relevance.
    - At the end, provide a single overall **reason** explaining why the final list of selected courses addresses the user’s query.

    Return your response in the following strict JSON format (and nothing else):

    {{
        "response":{{
            "matched_courses": [
                {{
                "course_number": "<e.g., INPR6000>",
                "title": "<Full Course Title>",
                "description": "<Full course description>",
                "department": "<Department Name>",
                "college": "<College Name>",
                "credit_hours": "<credits_hours>",
                "prerequisites": "<Comma-separated list or 'None'>"
                }}
            ],
            "reason": "<Short explanation of why this list of courses matches the student's query>"
        }}
    }}
    Only return valid JSON. Do not include any other commentary or explanation.
    """
    response = llm_with_json.invoke(prompt).content
    response = json.loads(response)

    return {"courses_from_users_query_after_summarization":response,
            "messages":[["AI","CourseExtractor",[response]]]
            }


