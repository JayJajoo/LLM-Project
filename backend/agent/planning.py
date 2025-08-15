from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from typing import List
from langchain_core.documents import Document
from .pydanticModels import AgentState, CourseAttributes 
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_openai.embeddings import OpenAIEmbeddings
from .queryDB import get_course_by_course_number
import json
import math
import os
import numpy as np

load_dotenv()

PATH = os.getcwd()

vector_db_path = os.path.join(PATH,"agent","VectorDB")
# print(vector_db_path)

llm = ChatOpenAI(model = "gpt-4.1-nano")

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

regular_courses_database = Chroma(collection_name="RegularCourses",embedding_function=embeddings,persist_directory=vector_db_path)
special_topics_database = Chroma(collection_name="SpecialCourses",embedding_function=embeddings,persist_directory=vector_db_path)

regular_courses_retriver_for_planning = regular_courses_database.as_retriever(search_kwargs={'k': 15})
special_courses_retriver_for_planning = special_topics_database.as_retriever(search_kwargs={'k': 1})


llm_for_course_attributes = llm.with_structured_output(CourseAttributes)

llm_json_for_filter_1 = ChatOpenAI(
    model="gpt-4.1-nano",
    model_kwargs={"response_format": {"type": "json_object"}},
)

llm_json_for_filter_2 = ChatOpenAI(
    model="gpt-4.1-nano",
    model_kwargs={"response_format": {"type": "json_object"}},
    temperature=0.3
)

llm_json_for_planning_agent = ChatOpenAI(
    model="gpt-4.1-nano",
    model_kwargs={"response_format": {"type": "json_object"}},
    temperature=0.4
)


def reset_previous_plans(state:AgentState):
    """
    Reset an AgentState object to its initial planning state.

    This function takes the current `AgentState` and returns a new dictionary 
    with most attributes preserved but all plan-related fields cleared or reset 
    to their default values. Useful for starting a fresh course planning process 
    while retaining general context like query, department, and college.

    Args:
        state (AgentState): The current agent state containing planning and query details.

    Returns:
        dict: A dictionary representing the reset agent state, with:
            - Query-related fields preserved (`query`, `rephrased_query`, `main_query`).
            - Course and planning-related fields emptied or reset (e.g., `final_course_list`, 
              `number_of_plans`, `semester_plans`, `planning_completed`).
            - Messages initialized with a "Reset Previous Details" status entry.
    """
    return {
        "query":state.query,
        "rephrased_query":state.rephrased_query,
        "main_query":state.main_query,
        "messages":[["Tool","Reset Previous Details","Completed"]],
        "college":state.college,
        "department":state.department,
        "intent":state.intent,
        "max_credits":state.max_credits,
        "max_creds_per_sem":state.max_creds_per_sem,
        "min_creds_per_sem":state.min_creds_per_sem,
        "max_number_of_plans":state.max_number_of_plans,
        "final_course_list":[],
        "course_list":[],
        "courses_from_users_query":[],
        "courses_from_users_query_after_summarization":{},
        "core_course_numbers":state.core_course_numbers,
        "core_course":state.core_course,
        "course_numbers":[],
        "course_titles":[],
        "filtered_course_list":[],
        "number_of_plans":0,
        "semester_plans":[],
        "planning_completed":False,
        "short_term_plan":{},
        "plan_number_to_change":1,
        "rescheduling_attributes":{},
        "error":""
    }

def rephrase_query_for_planning_schedule(state:AgentState):
    """
    Rephrase a user's course planning query for improved semantic search.

    This function uses a language model to transform a potentially vague or 
    general query into a detailed, curriculum-oriented description. The enriched 
    query explicitly includes the user's department and college to enhance 
    retrieval quality from a course or subject database via similarity search.

    The system message provides explicit instructions to the LLM to:
        - Expand the query with fundamental and advanced topics.
        - Include academic, technical, ethical, and interdisciplinary elements.
        - Use a curriculum-building mindset.
        - Align results with the specified college and department.

    Args:
        state (AgentState): The current agent state containing:
            - query (str): The user's original request.
            - college (str): The user's college name.
            - department (str): The user's department name.

    Returns:
        dict: A dictionary with the key `"rephrased_query"` containing the LLM's 
        enriched version of the user's query.

    Example:
        >>> state = AgentState(query="I want to become a data scientist",
        ...                    college="College of Computing",
        ...                    department="Data Science")
        >>> rephrase_query_for_planning_schedule(state)
        {'rephrased_query': 'Find courses and subjects offered by ...'}
    """
    query = state.query
    college = state.college
    dept = state.department

    sys_msg = """
    You are a specialist in retrieving the most relevant chunks from a vector database using cosine similarity search.

    Your task is to **rephrase vague or general user queries** into **information-rich, semantically detailed prompts** that enhance the quality of similarity-based retrieval from a course or subject database.

    ### Your Goals:
    1. Expand and enrich the user query by including **all subjects, topics, tools, and concepts** that a student would need to **fully master the field** — from foundational principles to advanced applications.
    2. Do **not only list buzzwords or technical tools** — include academic fundamentals, theoretical underpinnings, soft skills (if relevant), real-world applications, ethics, and interdisciplinary connections.
    3. Use a **curriculum-building mindset**: think of what a full academic path (beginner → expert) should include.
    4. You will be given `department` and `college` info — you **must explicitly mention them** in the rephrased query to ensure correct institutional alignment.

    ### Examples:

    1.  
    **User Query:** I want to become a data scientist.  
    **Rephrased Query:** Find courses and subjects offered by the Department of Data Science within the College of Computing and Information Sciences that span the full data science learning path. This should include foundational topics like calculus, linear algebra, probability, and statistics; core programming skills in Python and R; data structures and algorithms; data wrangling and cleaning; data visualization using Tableau, Matplotlib, and Seaborn; database systems and SQL; machine learning (supervised, unsupervised, ensemble methods); deep learning fundamentals (neural networks, CNNs, RNNs); big data processing tools like Apache Spark and Hadoop; cloud computing platforms such as AWS and GCP; model evaluation and deployment; MLOps best practices; and ethical considerations such as fairness, accountability, and bias in AI. The curriculum should also include hands-on projects using real-world datasets and collaborative tools for reproducible research.

    2.  
    **User Query:** I’m interested in law and emerging technologies.  
    **Rephrased Query:** Retrieve interdisciplinary courses offered by the Department of Law and Technology within the College of Legal Studies that comprehensively cover the intersection of law and technology. This should include legal theory, constitutional and administrative law, intellectual property law, contract law, and technology-specific domains such as digital privacy regulation, cybersecurity policy, AI governance frameworks, blockchain legal compliance, smart contracts, data protection regulations (GDPR, CCPA), tech-driven civil and criminal case studies, and the ethical and societal implications of rapid digital transformation. Also include courses on legal research methods, policy analysis, and writing legal memos in a tech context.

    3.  
    **User Query:** I want to study climate change.  
    **Rephrased Query:** Search for courses offered by the Department of Environmental Science within the College of Earth and Atmospheric Sciences that thoroughly cover the science, policy, and technology of climate change. Begin with foundational courses in Earth systems, meteorology, and environmental chemistry. Include advanced topics in greenhouse gas modeling, climate data analysis, remote sensing, and climate forecasting models. Also cover renewable energy technologies (solar, wind, hydro, geothermal), carbon capture and sequestration, global treaties (e.g., the Paris Agreement), climate risk assessment, sustainability metrics, green finance, environmental impact analysis, environmental law and governance, and community-based adaptation strategies. Emphasize real-world case studies, GIS tools, and interdisciplinary collaboration with economics and public policy.

    4.  
    **User Query:** I want to learn about art and design.  
    **Rephrased Query:** Retrieve subjects offered by the Department of Art and Design under the College of Fine Arts that span the entire creative development process. Include fundamentals such as drawing, color theory, visual composition, and art history; digital design tools such as Adobe Photoshop, Illustrator, and Figma; 3D modeling with Blender or Maya; courses in typography, print design, branding, and identity; human-centered design principles; UI/UX and interaction design; design for web and mobile platforms; animation and motion graphics; portfolio development; critique and iterative design process; and electives on cultural and ethical considerations in visual storytelling.

    5.  
    **User Query:** I’m interested in healthcare and medicine.  
    **Rephrased Query:** Find courses provided by the Department of Biomedical Sciences in the College of Health and Life Sciences that cover the entire continuum of healthcare education. Start with core biological sciences (anatomy, physiology, microbiology, and biochemistry), then advance to pathology, pharmacology, clinical diagnosis, patient communication, medical ethics, epidemiology, and public health systems. Also include technology-enabled healthcare like telemedicine, AI in diagnostics, wearable health devices, healthcare informatics, EHR systems, biomedical imaging, and statistical methods for clinical trials. Highlight training in both patient-centered care and data-driven medicine.

    ---

    Now rephrase the following user query and just return the rephrased query:
    """


    prompt = ChatPromptTemplate.from_messages([
        ("system", sys_msg),
        ("user", "User is studying in {dept} department of {college} and wants to {user_query}")
    ])

    prompt = prompt.format_messages(user_query=query,dept=dept,college=college)

    response = llm.invoke(prompt,temperature = 0.5).content

    return {"rephrased_query":response}

def get_courses_for_building_schedule(state: AgentState):
    """
    Retrieve and structure relevant courses for academic schedule building.

    This function searches for both regular and special courses relevant to the 
    user's query, restructures the retrieved documents into standardized course 
    dictionaries, and updates the `final_course_list` with any new courses not 
    already included. Core courses and zero-credit-hour courses are excluded.

    Args:
        state (AgentState): The current state containing query details, 
            previously selected courses, and core course numbers.

    Returns:
        dict: A dictionary containing:
            - "course_list" (list): Newly retrieved and restructured elective courses.
            - "final_course_list" (list): Updated list of all accumulated courses.
    """
    query = state.query
    rephrased_query = state.rephrased_query.strip()
    final_course_list = state.final_course_list
    core_course_numbers = state.core_course_numbers

    core_course_numbers_set = set(core_course_numbers)

    already_present_courses = {crn["course_number"]: True for crn in final_course_list}

    def restructure_retrivals(documents: List[Document]):
        restructured = []
        for doc in documents:
            metadata :str = doc.metadata
            try:
                credits_hours = metadata["credit_hours"]
                if credits_hours=='0' or metadata["course_number"] in core_course_numbers_set:
                    continue
                if metadata["credit_hours"].lower().__contains__("or"):
                    credits_hours = credits_hours.split(" ")[-1]
                lines = doc.page_content.split("\n")
                description = lines[1] if len(lines) > 1 else ""

                data = {
                    "title": metadata["title"],
                    "description": description,
                    "credit_hours": credits_hours,
                    "course_number": metadata["course_number"],
                    "college": metadata["college"],
                    "department": metadata["department"],
                    "dept_code": metadata["dept_code"],
                    "prerequisites": metadata["prerequisites"]
                }

                restructured.append(data)

                if not already_present_courses.get(str(data["course_number"]), False):
                    final_course_list.append(data)
                    already_present_courses[str(data["course_number"])] = True
            except Exception as e:
                pass
                # print(doc)
        return restructured

    restructured_courses = []
    
    regular_courses_1 = restructure_retrivals(regular_courses_retriver_for_planning.get_relevant_documents(query=rephrased_query))
    regular_courses_2 = restructure_retrivals(regular_courses_retriver_for_planning.get_relevant_documents(query=query+f" {state.college} {state.department}."))
    special_courses = restructure_retrivals(special_courses_retriver_for_planning.get_relevant_documents(query=rephrased_query))
    
    restructured_courses.extend(regular_courses_1)
    restructured_courses.extend(regular_courses_2)
    restructured_courses.extend(special_courses)


    return {"course_list": restructured_courses, "final_course_list": final_course_list}

def check_total_number_of_plans(state:AgentState):
    """
    Check if the maximum number of academic plans has been reached.

    This function compares the current number of generated plans with the 
    allowed maximum and returns a status indicating whether to continue 
    generating plans or stop.

    Args:
        state (AgentState): The current agent state containing the number of 
            generated plans and the maximum allowed plans.

    Returns:
        str: 
            - "finished" if the number of plans has reached or exceeded the limit.
            - "generate_more_plans" if more plans can still be created.
    """
    num_plans = state.number_of_plans
    if num_plans >= state.max_number_of_plans:
        return "finished"
    else:
        return "generate_more_plans"

def filter_courses_1(state: AgentState):
    """
    Filter and select elective courses to create a unique academic plan.

    This function uses an LLM to choose a set of elective courses that fit the 
    student's academic or career goals, while following constraints such as 
    credit limits, course uniqueness, difficulty level, and relevance. Each 
    invocation generates a distinct plan variation based on pre-defined 
    variety instructions.

    Args:
        state (AgentState): The current agent state containing query details, 
            course lists, credit limits, core course data, and planning context.

    Returns:
        dict: A dictionary with:
            - "filtered_course_list" (list): Updated list of course plan variations.
            - "number_of_plans" (int): Incremented count of generated plans.
    """

    query = state.query
    rephrased_query = state.rephrased_query
    course_list = state.course_list
    college = state.college
    department = state.department
    core_courses = get_course_by_course_number(state.core_course_numbers)
    core_courses_credits = sum([int(course["credit_hours"].split(" ")[-1]) for course in core_courses])
    max_creds = state.max_credits
    remaining_credits = max_creds - core_courses_credits
    prev_filtered_course_list = state.filtered_course_list
    core_course_numbers = state.core_course_numbers
    
    average_creds = sum([int(course["credit_hours"].split(" ")[-1]) for course in course_list])//len(course_list)
    num_subjects_to_add = max(1,int(remaining_credits//average_creds))

    current_plan = state.number_of_plans + 1

    # variety_instructions = {
    #     1: "Prioritize advanced or specialized courses that others might overlook.",
    #     2: "Focus on the most essential and core courses for this goal.",
    #     3: "Consider alternative courses that provide different perspectives or approaches.",
    #     4: "Include courses that might be interdisciplinary or from other departments.",
    # }
    
    variety_instructions = {
        1: "Maximize specialization — select courses that dive deep into one area to build expert-level mastery.",
        2: "Optimize versatility — choose a wide range of topics across subfields to prepare for multiple career paths or interests.",
        3: "Target outcomes — pick courses based on concrete goals like job readiness, portfolio building, or research publication.",
        4: "Follow curiosity — let personal interest or passion drive the selection, even if it doesn't align directly with formal goals.",
    }


    variety_instruction = variety_instructions.get(current_plan, "Create a unique combination different from typical recommendations.")

    prompt = f"""You are an intelligent academic course planning assistant but for that you need to carefully filter and select the most suitable elective courses from the course list.

    ---

    Objective:
    Based on the student's career or academic goal, recommend a list of elective **course numbers** from the available courses that best support their goal — without EXCEEDING THEIR REMAINING CREDIT ALLOWANCE.

    Plan Variety Instruction (Plan #{current_plan}):
    {variety_instruction}

    ---

    Student Goal (Original Query):
    "{query}"

    LLM-Interpreted Goal (Rephrased for clarity):
    "{rephrased_query}"

    ---

    Constraints and Logic:

    1. Credit Limit  
    - You need to **add atleast {num_subjects_to_add} number of elective subjects to the list** even if it might get over the Remaining Credits limit mentioned below.
    - Remaining Credits: **{remaining_credits}**  
    - You must select elective courses such that their **total credit hours are at least {remaining_credits}**.  
    - Do NOT return fewer total credits than this.  
    - If necessary, it is allowed to slightly exceed this credit count — but keep the total as **close as possible** to {remaining_credits} without going far beyond.  


    2. Department & College Priority  
    - First prefer courses from the same department (**{department}**) and same college (**{college}**).  
    - If additional beneficial courses exist in other departments or colleges, they MUST be DEFINITELY included.  
    - Prioritize internal courses whenever multiple options exist.

    3. Exclusions & Deduplication  
    - Do NOT include any course with course numbers: {core_course_numbers}  
    - Do NOT include any course that has the **same title** as a core course.  
    - Do NOT include courses that are **very similar in title or content** to any core course.  
    - If you select a course covering a topic (e.g., "Deep Learning"), avoid selecting another course that covers **substantially the same topic** (e.g., "Neural Networks" or "DL Fundamentals").  
    - Only choose courses from the provided elective course list.  
    - DO NOT MAKE UP YOUR OWN COURSES, COURSE TITLES OR COURSE NUMBERS  
    - STRICTLY SELECT FROM WHAT IS PROVIEDED TO YOU BASED ON THE STUDENTS AIM AND ITS RELATION WITH THE PROVIDED COURSES.

    4. Student Context & Difficulty Level  
    - The student is a **graduate-level** student and is assumed to have already completed **introductory and foundational courses**.  
    - Therefore, prioritize **medium to advanced level** electives.  
    - Avoid recommending basic or beginner-level courses unless they are clearly required for the student's goal.

    5. Relevance & Usefulness  
    - All selected electives must align with the student's academic or professional goal.  

    ---

    Student Profile:
    - College: {college}
    - Department: {department}
    - Maximum Credits Allowed: {max_creds}
    - Core Courses Taken: {core_courses_credits}
    - Remaining Credits: {remaining_credits}

    ---

    Selected Core Courses:
    (Already completed — do not include again)

    {json.dumps(core_courses, indent=2)}

    ---

    Available Elective Courses:
    (Use this list only — recommend relevant electives from here)

    {json.dumps(course_list, indent=2)}

    ---

    Output checks:
        - The sum of selected course credit hours must be **≥ {remaining_credits}**.  
        - Slightly exceeding is permitted but not encouraged — do so only if necessary to create a valid, high-quality plan.  
    
    ---
        
    Output Format (Very Important):  
    Return your response as a JSON object with this exact structure:
    {{
        "courses": [
            {{
                "title": "string",
                "description": "string",
                "credit_hours": "string",
                "course_number": "string",
                "college": "string",
                "department":"string",
                "dept_code": "string",
                "prerequisites": "string"
            }}
        ]
    }}

    - Do NOT include any other text, explanation, or formatting.  
    - Each course must come from the provided elective course list.  
    - The total credit hours of your selection must be equal to {remaining_credits}.  
    - Do not include courses with duplicate, identical, or very similar titles to any core course.  
    - Do not include courses that overlap substantially in topic with other selected electives.  
    - Prioritize medium to advanced graduate-level electives.
    - CREATE A UNIQUE COMBINATION FOR THIS PLAN #{current_plan}.

    """

    response_content = llm_json_for_filter_1.invoke(prompt).content
    response_json = json.loads(response_content)
    
    response = response_json["courses"] 
    

    already_suggested = {}
    unique_new_filtered_course = []
    core_course_numbers_set = set(core_course_numbers)

    for course in response:
        course_num = course["course_number"]
        if course_num in core_course_numbers_set:
            continue
        if already_suggested.get(course_num, False):
            continue
        already_suggested[course_num] = True
        unique_new_filtered_course.append(course)  

    return {
        "filtered_course_list": prev_filtered_course_list + [unique_new_filtered_course],
        "number_of_plans": state.number_of_plans + 1,
    }

def get_unique_plans(state: AgentState):
    """
    Remove duplicate course plans based on course numbers.

    This function ensures that only unique academic plans remain by comparing 
    the sorted list of course numbers for each plan. Duplicate plans (with the 
    same set of course numbers) are removed.

    Parameters
    ----------
    state : AgentState
        The current agent state containing `filtered_course_list` with course plans.

    Returns
    -------
    dict
        A dictionary with:
        - "filtered_course_list" (list): Unique course plans.
        - "number_of_plans" (int): The total count of unique plans.
    """

    filtered_course_list = state.filtered_course_list

    seen = set()
    unique_plans = []

    for plan in filtered_course_list:
        
        course_nums = tuple(sorted(course["course_number"] for course in plan))  
        
        if course_nums not in seen:
            seen.add(course_nums)
            unique_plans.append(plan)

    return {
        "filtered_course_list": unique_plans,
        "number_of_plans": len(unique_plans)
    }

def filter_courses_2(state: AgentState):
    """
    Adjust course plans to meet a specific credit requirement.

    This function iterates through each filtered course plan and uses an LLM 
    to either add or remove electives so that the total credits (core + electives) 
    meet the maximum allowed credits. The LLM receives detailed instructions 
    including available courses, current plan, student goal, and adjustment rules.

    Parameters
    ----------
    state : AgentState
        The current agent state containing:
        - query (str): Student’s academic or career goal.
        - college (str): Name of the college.
        - department (str): Department name.
        - core_course_numbers (list): List of core course numbers.
        - max_credits (int): Maximum allowed total credits.
        - filtered_course_list (list): List of current elective plans.
        - final_course_list (list): Full list of available courses.

    Returns
    -------
    dict
        A dictionary containing:
        - "filtered_course_list" (list): Updated list of course plans with 
          credits matching the requirement.
    """

    query = state.query
    college = state.college
    department = state.department

    core_courses = get_course_by_course_number(state.core_course_numbers)
    core_courses_credits = sum([int(course["credit_hours"].split(" ")[-1]) for course in core_courses])

    max_creds = state.max_credits
    remaining_credits = max_creds - core_courses_credits

    filtered_course_list = state.filtered_course_list
    final_course_list = state.final_course_list

    optimized_plans = []

    for plan_idx, plan in enumerate(filtered_course_list):
        current_credits = sum([int(course["credit_hours"].split(" ")[-1]) for course in plan])
        credit_difference = remaining_credits - current_credits

        if credit_difference == 0:
            optimized_plans.append(plan)
            continue

        average_credit = (
            sum([int(course["credit_hours"].split(" ")[-1]) for course in plan]) // len(plan)
            if plan else 3
        )

        action = "ADD" if credit_difference > 0 else "REMOVE"
        abs_credit_diff = abs(credit_difference)

        # If removing, calculate how many courses can be safely removed (max)
        if action == "REMOVE":
            max_courses_to_remove = abs_credit_diff // average_credit if average_credit else 1
            if max_courses_to_remove == 0:
                max_courses_to_remove = 1  # Ensure model doesn't remove everything

        current_course_numbers = {c["course_number"] for c in plan}
        available_courses = [
            c for c in final_course_list if c["course_number"] not in current_course_numbers
        ]

        current_plan_courses = json.dumps(plan, indent=2)
        available_courses_json = json.dumps(available_courses, indent=2)

        instruction_lines = [
            f"You need to **{action.lower()} approximately {abs_credit_diff} credits worth of electives**."
            f"For you information the avaliable list of electives have average credits = {average_credit}",
        ]

        if action == "REMOVE":
            instruction_lines += [
                f"- Try to remove **no more than {max_courses_to_remove} course(s)** unless strictly necessary.",
                "- Prefer removing **fewer higher-credit electives** than many small ones.",
                "- Keep the overall direction of the plan intact."
            ]

        elif action == "ADD":
            courses_to_add = max(1,(abs(credit_difference)//average_credit))

            instruction_lines += [
                f"- You must add between {courses_to_add} and {courses_to_add + 2} subjects (inclusive range) to the current plan below.",
                f"- Strictly avoid adding fewer than the minimum or more than the maximum number of courses indicated above."
                f"- If there are (x) numbers of courses are in current plan then return at least (x+{courses_to_add}) number of courses"
                "- Select electives that best enhance the plan and align with the student's goal.",
            ]

        instruction = "\n".join(instruction_lines)


        prompt = f"""You are an academic advisor helping optimize a graduate student's course plan.

        Student Goal: {query}  
        Department: {department}  
        College: {college}  

        ACTION: {action}  
        {instruction}

        CURRENT PLAN (Electives Only):  
        {current_plan_courses}

        AVAILABLE COURSES (Excludes core and current plan):  
        **Rember this instruction\n\n{instruction_lines}**
        {available_courses_json}

        RULES:  
        1. Final plan must include all core courses and have **core + electives ≥ {max_creds} credits**.  
        2. Modify only from the "AVAILABLE COURSES" list.  
        3. Prioritize electives that align with the goal: **"{query}"**.  
        4. Avoid filler or unrelated courses.  
        5. Only include valid, properly credited graduate-level courses.  
        6. Do not duplicate any course.  
        7. Do not overshoot the target credits significantly.  
        8. If a valid adjustment is not possible, return the current plan unchanged and explain why.  
        9. Prefer **6000-level (intermediate)** and **7000-level (advanced)** courses.  
           - 5000-level: Foundational / prerequisites  
           - 6000-level: Intermediate graduate core  
           - 7000-level: Advanced or research-focused  

        Output Format:
        {{
          "action_taken": "{action}",
          "courses_modified": ["course_number1", "course_number2"],
          "final_plan": [
            {{
              "title": "string",
              "description": "string",
              "credit_hours": "string",
              "course_number": "string",
              "college": "string",
              "department": "string",
              "dept_code": "string",
              "prerequisites": "string",
              "term": "string"
            }}
          ],
          "reasoning": "Brief explanation of the decisions made"
        }}


        Ensure the final elective plan supports the student’s goal and credit requirement.
        FOLLOW THE GIVEN INSTRUCTIONS STRICTLY.
        
        Now {action} course as per instructions.

        Return answer in JSON format only.
        
        """

        response_content = llm_json_for_filter_2.invoke(prompt).content
        response_json = json.loads(response_content)
        optimized_plan = response_json["final_plan"]

        optimized_credits = sum([int(course["credit_hours"].split(" ")[-1]) for course in optimized_plan])
        total_credits_with_core = optimized_credits + core_courses_credits

        if total_credits_with_core >= max_creds:
            optimized_plans.append(optimized_plan)
        else:
            print(
                f"Plan {plan_idx + 1}: Credit mismatch! Core + electives = {total_credits_with_core} < {max_creds}. Using original plan."
            )
            optimized_plans.append(plan)

    return {
        "filtered_course_list": optimized_plans
    }

def parse_credit_hours(credit_str):
    """
    Parse the numeric value of credit hours from a credit string.

    If the string contains a "TO" (credit range), the function returns the 
    upper bound. Otherwise, it attempts to parse the numeric value directly.

    Parameters
    ----------
    credit_str : str
        Credit hours string, e.g., "3", "2 TO 4", "4".

    Returns
    -------
    int
        The parsed integer credit value, or 0 if parsing fails.
    """
    if "TO" in credit_str:
        parts = credit_str.split("TO")
        try:
            return int(parts[1].strip())
        except:
            return 0
    else:
        try:
            return int(credit_str.strip())
        except:
            return 0
        
def planning_agent(state: AgentState):
    """
    Generate semester-by-semester course schedules for a graduate student.

    This function takes a set of core and elective courses and uses an LLM 
    to create semester-wise plans that respect prerequisites, credit limits, 
    and course priorities. Core courses are scheduled first, electives are 
    distributed, and the plan adheres to minimum and maximum credits per semester.

    Parameters
    ----------
    state : AgentState
        The current agent state containing:
        - query (str): The student's academic or career goal.
        - college (str): College name.
        - department (str): Department name.
        - filtered_course_list (list): List of elective course plans.
        - core_course_numbers (list): List of required core course numbers.
        - max_creds_per_sem (int): Maximum credits allowed per semester.
        - min_creds_per_sem (int): Minimum credits required per semester.
        - max_credits (int): Maximum total credits allowed.

    Returns
    -------
    dict
        A dictionary containing:
        - "semester_plans" (list): A list of JSON objects, each representing a plan with semester-wise schedules.
        - "filtered_course_list" (list): Updated elective plans filtered according to the courses actually used in the semester schedules.
    """
    query = state.query
    college = state.college
    department = state.department
    filtered_course_list = state.filtered_course_list
    core_courses = get_course_by_course_number(state.core_course_numbers)

    core_courses_credits = sum([int(course["credit_hours"].split(" ")[-1]) for course in core_courses])


    max_creds_per_sem = state.max_creds_per_sem
    min_creds_per_sem = state.min_creds_per_sem
    max_total_credits = state.max_credits
    max_allowed_credits = max_total_credits

    min_number_of_terms = max(1, math.ceil(max_total_credits / max_creds_per_sem))
    max_number_of_terms = max(2, math.ceil(max_total_credits / min_creds_per_sem))

    remaining_credits = max_total_credits - core_courses_credits

    semester_plans = []

    for plan_idx, elective_plan in enumerate(filtered_course_list):
        core_courses_json = json.dumps(core_courses, indent=2)
        elective_courses_json = json.dumps(elective_plan, indent=2)

        average_credit = (
            sum([int(course["credit_hours"].split(" ")[-1]) for course in elective_plan]) // len(elective_plan)
            if elective_plan else 3
        )

        subs_to_add = math.ceil(remaining_credits/average_credit)


        prompt = f"""You are an academic advisor creating a semester-by-semester course schedule for a graduate student.

        Student Goal: {query}
        Department: {department}
        College: {college}

        FOR REFERENCE:

        Graduate course numbers generally follow this pattern:  
           - 5000-level courses (5XXX) are foundational and may serve as prerequisites.  
           - 6000-level courses (6XXX) are intermediate or core graduate topics.  
           - 7000-level courses (7XXX) are advanced or research-focused graduate courses generally during last semesters.  
        
        Use this to guide your selections toward deeper learning.
        
        SCHEDULING CONSTRAINTS:
        - Credits per semester: {min_creds_per_sem} to {max_creds_per_sem}
        - The number of semesters (terms) can be between {min_number_of_terms} and {max_number_of_terms} both INCLUSIVE
        - Total credits required (core + electives): at least {max_total_credits} but not more than {max_allowed_credits+1} both INCLUSIVE
        - Must respect course prerequisites
        - Core courses and foundational should be prioritized and scheduled early when possible.

        CORE COURSES (must all be strictly included — including Capstone or Project-based courses such as Data Science Capstone):
        {core_courses_json}

        ELECTIVE COURSES (add **atleast {subs_to_add-1} OR MORE subjects from below list**):
        {elective_courses_json}

        RULES:
        1. You need to add **atleast minimum {subs_to_add-1} OR MORE subjects approximately** from the elective courses to comleted the total plan credits.
        2. Every course in the list must be scheduled exactly once
        3. Respect prerequisite relationships (schedule prerequisites before dependent courses)
        4. Each semester must have between {min_creds_per_sem} and {max_creds_per_sem} credits
        5. Try to balance the workload across semesters
        6. Assume all courses are available every semester unless blocked by prerequisites
        7. Do not calculate total credits — simply break the course list into valid semesters
        8. DO NOT INCLUDE FOUNDATIONAL COURSES IN FINAL SEMESTERS AND ALSO TRY TO PLACE THEM AS SOON AS POSSIBLE 
        9. EVERY core course listed (including capstone/project courses like "Data Science Capstone") MUST be included exactly once. DO NOT skip any core course — failure to include even one is invalid.
        10. CAPSTONE or final projects if present in the core courses should be included in final stages of the plan
        11. **Do not make up course Numbers by yourself.**
        12. If you fall short of elective course to complete the credits return all the re arranged electives. 
        
        Return your response as a JSON object with this exact structure:
        {{
        "plan_number": {plan_idx + 1},
        "total_semesters": "Number of semesters included in the plan",
        "semester_schedule": [
            {{
            "semester": 1,
            "courses": [
                {{
                "course_number": "DS5110",
                "title": "Course Title",
                "description": "Summarised Course Description...",
                "reason": "Brief reason how this course will help the student according to this plan .....",
                "credit_hours": "4",
                "type": "core or elective",
                }}
            ],
            "total_credits": 12,
            }}
        ],
        "reason_behind_planning": "Detailed reason why this plan was structured in this way, including how prerequisites were respected, why courses were grouped in specific semesters, how workload was balanced, and any trade-offs made to meet credit or term constraints."
        }}

        PLEASE DO NOT REPEAT COURSES NOT MATTER WHAT BUT PLEASE DON'T REPEAT COURSES. 
        **INCLUDE ALL THE COURE COURSES PROVIDED STRICTLY.**
        **Do not make up course numbers.**
        Do not hardcode the number of semesters. Instead, use as many semesters as needed within the allowed range. Ensure course credits match and all constraints are satisfied."""


        response_content = llm_json_for_planning_agent.invoke(prompt).content
        response_json = json.loads(response_content)

        # Recalculate total credits per semester
        for semester in response_json.get("semester_schedule", []):
            recalculated = sum(parse_credit_hours(c["credit_hours"]) for c in semester["courses"])
            if "total_credits" not in semester or int(semester["total_credits"]) != recalculated:
                semester["total_credits"] = recalculated

        # Recalculate total credits for the entire plan
        calculated_total_credits = sum(
            semester["total_credits"] for semester in response_json["semester_schedule"]
        )
        response_json["total_credits"] = calculated_total_credits

        semester_plans.append(response_json)

    filtered_course_numbers_per_plan = []

    for sem_plan in semester_plans:
        used_courses = {}
        for semester in sem_plan["semester_schedule"]:
            for course in semester["courses"]:
                used_courses[course["course_number"]] = True
        filtered_course_numbers_per_plan.append(used_courses)

    new_filtered_course_list = []

    for idx, original_elective_plan in enumerate(filtered_course_list):
        used = filtered_course_numbers_per_plan[idx]
        filtered = [course for course in original_elective_plan if used.get(course["course_number"], False)]
        new_filtered_course_list.append(filtered)

    return {
        "semester_plans": semester_plans,
        "filtered_course_list": new_filtered_course_list,
    }

def get_unique_courses(all_courses, current_courses):
    """
    Filter out courses that are already included in the current course list.

    Parameters
    ----------
    all_courses : list
        List of all available courses (each course is a dictionary with a "course_number").
    current_courses : list
        List of courses already included in the student's plan.

    Returns
    -------
    list
        Courses from `all_courses` that are not present in `current_courses`.
    """
    current_set = {course["course_number"] for course in current_courses}
    return [course for course in all_courses if course["course_number"] not in current_set]

def get_unique_courses_with_credit_matching(all_courses, current_courses, req_credits):
    """
    Filter courses to get only unique courses matching a specific credit value.

    Parameters
    ----------
    all_courses : list
        List of all available courses (each course is a dictionary with "course_number" and "credit_hours").
    current_courses : list
        List of courses already included in the student's plan.
    req_credits : int
        Required credit hours to match.

    Returns
    -------
    list
        Courses that are not in `current_courses` and have `credit_hours` equal to `req_credits`.
    """
    current_set = {course["course_number"] for course in current_courses}
    filtered_courses = []

    for course in all_courses:
        crn = course["course_number"]
        if crn not in current_set:
            course_credits = parse_credit_hours(str(course["credit_hours"]))
            if course_credits == req_credits:
                filtered_courses.append(course)
    
    return filtered_courses

def cosine_similarity(a, b):
    """
    Compute the cosine similarity between two vectors.

    Parameters
    ----------
    a : np.ndarray
        First vector.
    b : np.ndarray
        Second vector.

    Returns
    -------
    float
        Cosine similarity value between vectors `a` and `b`.
    """
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    return dot_product / (norm_a * norm_b + 1e-10)

def get_best_similar_option_by_course(current_course, all_courses):
    """
    Find the most semantically similar course from a list based on an existing course.

    Parameters
    ----------
    current_course : dict
        A course dictionary containing "course_number", "title", and "description".
    all_courses : list
        A list of course dictionaries to compare against.

    Returns
    -------
    tuple
        A tuple containing:
        - best_match (dict): The course from `all_courses` most similar to `current_course`.
        - best_index (int): Index of the best matching course in `all_courses`.
    """
    curr_str = f"{current_course['course_number']} - {current_course['title']} - {current_course['description']}"
    embd1 = embeddings.embed_query(curr_str)

    best_score, best_index = -1, 0

    for idx, course in enumerate(all_courses):
        new_str = f"{course['course_number']} - {course['title']} - {course['description']}"
        embd2 = embeddings.embed_query(new_str)
        
        similarity = cosine_similarity(embd1, embd2)
        
        if similarity > best_score:
            best_score = similarity
            best_index = idx
    
    return all_courses[best_index], best_index

def get_best_similar_option_by_query(user_query , rephrased_query , all_courses):
    """
    Find the course most semantically similar to a user query from a list of courses.

    Parameters
    ----------
    user_query : str
        The original user query describing their goal.
    rephrased_query : str
        The LLM-rephrased version of the user query.
    all_courses : list
        A list of course dictionaries to compare against.

    Returns
    -------
    dict
        The course from `all_courses` that is most semantically similar to the combined query.
    """
    curr_str = f"{user_query}\n{rephrased_query}"
    embd1 = embeddings.embed_query(curr_str)

    best_score, best_index = -1, 0

    for idx, course in enumerate(all_courses):
        new_str = f"{course['course_number']} - {course['title']} - {course['description']}"
        embd2 = embeddings.embed_query(new_str)
        
        similarity = cosine_similarity(embd1, embd2)
        
        if similarity > best_score:
            best_score = similarity
            best_index = idx
    
    return all_courses[best_index]

def final_duplicate_check(state: AgentState):
    """
    Ensure there are no duplicate courses across semester plans by replacing duplicates 
    with the most similar available alternative courses.

    Parameters
    ----------
    state : AgentState
        The current agent state containing:
        - final_course_list: List of all possible courses.
        - filtered_course_list: List of elective course plans.
        - semester_plans: List of semester schedules.

    Returns
    -------
    dict
        A dictionary containing:
        - "semester_plans": Updated semester plans with duplicates resolved.
        - "filtered_course_list": Updated elective course lists reflecting replacements.
    """
    all_courses = state.final_course_list
    filtered_course_list = state.filtered_course_list
    plans = state.semester_plans
    final_filtered_course_list = []

    for plan_idx, plan in enumerate(plans):
        # Courses in this plan's filtered list
        current_filtered = filtered_course_list[plan_idx]
        # Find all valid options to replace with
        courses_not_included = get_unique_courses(all_courses, current_courses=current_filtered)
        # To track duplicates
        courses_already_present = {}
        # Build updated filtered list
        new_filtered_course_list = []

        for semester_index, semester in enumerate(plan["semester_schedule"]):
            for course_index, course in enumerate(semester["courses"]):
                crn = course["course_number"]
                found = courses_already_present.get(crn, False)

                if found:
                    # Replace duplicate
                    replacement, repl_index = get_best_similar_option_by_course(
                        current_course=course,
                        all_courses=courses_not_included
                    )

                    plan["semester_schedule"][semester_index]["courses"][course_index] = replacement

                    credits_diff = (
                        parse_credit_hours(str(replacement["credit_hours"])) -
                        parse_credit_hours(str(course["credit_hours"]))
                    )

                    plan["semester_schedule"][semester_index]["total_credits"] += credits_diff
                    plan["total_credits"] += credits_diff

                    del courses_not_included[repl_index]
                    new_filtered_course_list.append(replacement)
                else:
                    courses_already_present[crn] = True
                    new_filtered_course_list.append(course)

        final_filtered_course_list.append(new_filtered_course_list)

    return {
        "semester_plans": plans,
        "filtered_course_list": final_filtered_course_list
    }

def final_course_addition_check(state: AgentState):
    """
    Ensure each semester plan meets the total credit requirements by adding additional
    elective courses if needed, prioritizing courses semantically similar to the student's goal.

    Parameters
    ----------
    state : AgentState
        The current agent state containing:
        - semester_plans: List of semester-wise course schedules.
        - filtered_course_list: Current elective courses selected per plan.
        - final_course_list: All available courses.
        - max_credits: Maximum total credits allowed.
        - max_creds_per_sem: Maximum credits allowed per semester.
        - query: Original user query.
        - rephrased_query: LLM-rephrased user query.

    Returns
    -------
    dict
        A dictionary containing:
        - "planning_completed": Boolean indicating completion of the planning process.
        - "main_query": Original user query.
        - "semester_plans": Updated semester schedules including any added courses.
        - "messages": Logging messages or plan data.
        - "filtered_course_list": Updated list of electives reflecting any additions.
    """
    plans = state.semester_plans
    max_creds = state.max_credits
    filtered_course_list = state.filtered_course_list
    all_courses = state.final_course_list
    max_credits_per_sem = state.max_creds_per_sem        

    for plan_idx, plan in enumerate(plans):
        if plan["total_credits"] >= max_creds:
            continue

        current_filtered = filtered_course_list[plan_idx]
        dummy_all_courses = all_courses[:]  # shallow copy, OK since we only filter

        for semester in plan["semester_schedule"]:
            sem_credits = semester["total_credits"]
            if sem_credits >= max_credits_per_sem:
                continue

            remaining_credits = max_credits_per_sem - sem_credits

            # Try to find a course matching exact credits, or decrement if not found
            temp_credits = remaining_credits
            courses_not_included = []

            while temp_credits > 0:
                courses_not_included = get_unique_courses_with_credit_matching(
                    dummy_all_courses,
                    current_courses=current_filtered,
                    req_credits=temp_credits
                )
                if courses_not_included:
                    break
                temp_credits -= 1

            if not courses_not_included:
                continue

            course_to_add = get_best_similar_option_by_query(
                state.query,
                state.rephrased_query,
                all_courses=courses_not_included
            )

            if not course_to_add:
                continue

            # Add course to semester
            semester["courses"].append(course_to_add)
            credits_to_add = parse_credit_hours(str(course_to_add["credit_hours"]))
            semester["total_credits"] += credits_to_add
            plan["total_credits"] += credits_to_add

            current_filtered.append(course_to_add)

            # Remove added course from dummy_all_courses
            dummy_all_courses = get_unique_courses(
                all_courses=dummy_all_courses,
                current_courses=current_filtered
            )

    return {
        "planning_completed": True,
        "main_query":state.query,
        "semester_plans": plans,
        "messages": [["AI","Planning",plans]],
        "filtered_course_list": filtered_course_list
    }