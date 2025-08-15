from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from typing import List
from langchain_core.documents import Document
from pydanticModels import AgentState, CourseAttributes 
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_openai.embeddings import OpenAIEmbeddings
from queryDB import get_course_by_course_number
import json
import math
import os
load_dotenv()

PATH = os.getcwd()

vector_db_path = os.path.join(PATH,"LLM Project","testing","VectorDB")

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



def rephrase_query_for_planning_schedule(state:AgentState):
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
    num_plans = state.number_of_plans
    if num_plans >= state.max_number_of_plans:
        return "finished"
    else:
        return "generate_more_plans"

def filter_courses_1(state: AgentState):
    import json

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

    variety_instructions = {
        1: "Focus on the most essential and core courses for this goal.",
        2: "Consider alternative courses that provide different perspectives or approaches.",
        3: "Include courses that might be interdisciplinary or from other departments.",
        4: "Prioritize advanced or specialized courses that others might overlook."
    }
    
    variety_instruction = variety_instructions.get(current_plan, "Create a unique combination different from typical recommendations.")

    prompt = f"""You are an intelligent academic course planning assistant but for that you need to carefully filter and select the most suitable elective courses from the course list.

    ---

    🎯 Objective:
    Based on the student's career or academic goal, recommend a list of elective **course numbers** from the available courses that best support their goal — without EXCEEDING THEIR REMAINING CREDIT ALLOWANCE.

    🎲 Plan Variety Instruction (Plan #{current_plan}):
    {variety_instruction}

    ---

    🧠 Student Goal (Original Query):
    "{query}"

    💬 LLM-Interpreted Goal (Rephrased for clarity):
    "{rephrased_query}"

    ---

    📘 Constraints and Logic:

    1. 💳 Credit Limit  
    - You need to **add atleast {num_subjects_to_add} number of elective subjects to the list** even if it might get over the Remaining Credits limit mentioned below.
    - ✅ Remaining Credits: **{remaining_credits}**  
    - You must select elective courses such that their **total credit hours are at least {remaining_credits}**.  
    - ⚠️ Do NOT return fewer total credits than this.  
    - If necessary, it is allowed to slightly exceed this credit count — but keep the total as **close as possible** to {remaining_credits} without going far beyond.  


    2. 🏫 Department & College Priority  
    - First prefer courses from the same department (**{department}**) and same college (**{college}**).  
    - If additional beneficial courses exist in other departments or colleges, they MUST be DEFINITELY included.  
    - Prioritize internal courses whenever multiple options exist.

    3. ❌ Exclusions & Deduplication  
    - Do NOT include any course with course numbers: {core_course_numbers}  
    - Do NOT include any course that has the **same title** as a core course.  
    - Do NOT include courses that are **very similar in title or content** to any core course.  
    - If you select a course covering a topic (e.g., "Deep Learning"), avoid selecting another course that covers **substantially the same topic** (e.g., "Neural Networks" or "DL Fundamentals").  
    - Only choose courses from the provided elective course list.  
    - DO NOT MAKE UP YOUR OWN COURSES, COURSE TITLES OR COURSE NUMBERS  
    - STRICTLY SELECT FROM WHAT IS PROVIEDED TO YOU BASED ON THE STUDENTS AIM AND ITS RELATION WITH THE PROVIDED COURSES.

    4. 🎓 Student Context & Difficulty Level  
    - The student is a **graduate-level** student and is assumed to have already completed **introductory and foundational courses**.  
    - Therefore, prioritize **medium to advanced level** electives.  
    - Avoid recommending basic or beginner-level courses unless they are clearly required for the student's goal.

    5. ✅ Relevance & Usefulness  
    - All selected electives must align with the student's academic or professional goal.  

    ---

    🧑‍🎓 Student Profile:
    - College: {college}
    - Department: {department}
    - Maximum Credits Allowed: {max_creds}
    - Core Courses Taken: {core_courses_credits}
    - ✅ Remaining Credits: {remaining_credits}

    ---

    📘 Selected Core Courses:
    (Already completed — do not include again)

    {json.dumps(core_courses, indent=2)}

    ---

    📘 Available Elective Courses:
    (Use this list only — recommend relevant electives from here)

    {json.dumps(course_list, indent=2)}

    ---

    Output checks:
        - The sum of selected course credit hours must be **≥ {remaining_credits}**.  
        - Slightly exceeding is permitted but not encouraged — do so only if necessary to create a valid, high-quality plan.  
    
    ---
        
    ✅ Output Format (Very Important):  
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
    import json

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

        🎯 Student Goal: {query}  
        🏛️ Department: {department}  
        🏫 College: {college}  

        🔧 ACTION: {action}  
        {instruction}

        📘 CURRENT PLAN (Electives Only):  
        {current_plan_courses}

        📚 AVAILABLE COURSES (Excludes core and current plan):  
        {available_courses_json}

        ⚖️ RULES:  
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

        ✅ Output Format:
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

        CORE COURSES (must be included):
        {core_courses_json}

        ELECTIVE COURSES (must be included):
        {elective_courses_json}

        RULES:
        1. Yo need to add atleast minimum {subs_to_add}+ subjects approximately from the elective courses to comleted the total plan credits.
        2. Every course in the list must be scheduled exactly once
        3. Respect prerequisite relationships (schedule prerequisites before dependent courses)
        4. Each semester must have between {min_creds_per_sem} and {max_creds_per_sem} credits
        5. Try to balance the workload across semesters
        6. Assume all courses are available every semester unless blocked by prerequisites
        7. Do not calculate total credits — simply break the course list into valid semesters
        8. DO NOT INCLUDE FOUNDATIONAL COURSES IN FINAL SEMESTERS AND ALSO TRY TO PLACE THEM AS SOON AS POSSIBLE 

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
        "messages": [["AI","Planning",semester_plans]],
        "main_query":state.query,
        "semester_plans": semester_plans,
        "filtered_course_list": new_filtered_course_list,
        "planning_completed": True
    }