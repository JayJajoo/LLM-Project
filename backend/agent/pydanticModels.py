from pydantic import BaseModel,Field
from typing import Annotated,Sequence,List,Dict,Union,Any
import operator

class UserIntent(BaseModel):
    """Users Current Query Intent"""
    intent : str = Field(description="Users Current Query Intent")

class CourseAttributes(BaseModel):
    """
    A Pydantic model for specifying course search attributes.

    Attributes:
        course_numbers (List[str]): A list of course numbers (e.g., ["DS5220", "CS6220"])
            used for querying the course database by course number.
        
        course_titles (List[str]): A list of course titles (e.g., ["Machine Learning", "Data Visualization"])
            used for querying the course database by title.
    """
    course_numbers: List[str] = Field(
        description="Stores list of course numbers as strings for searching in database by course_number"
    )
    course_titles: List[str] = Field(
        description="Stores list of course titles as strings for searching in database by title"
    )    

class AgentState(BaseModel):
    """Full Agent State"""

    query:str = Field(description="Contains user query",default="")
    rephrased_query : str = Field(description="Contains rephrased user query",default="") 
    main_query:str = Field(description="The main query of the user, which will be used in case of plan changes ahead.",default="")

    messages: Annotated[Sequence[list],operator.add] = Field(default_factory=list,description="Contains chat history of the user's interaction with the model and tools.")
    
    college : str = Field(description="Refers to the College of the student in the university.",default="")
    department : str = Field(description="Refers to the College of the student in the college.",default="")
    
    intent:str = Field(description="Users Current Query Intent",default="")
    
    final_course_list: List[Dict[str, str]] = Field(description="Contains the fetched courses from all the plans.",default=[])    
    course_list: List[Dict[str, str]] = Field(description = "Contains the fetched courses for a specific goal for a specific plan.",default=[])
    
    courses_from_users_query : List[Dict[str,str]] = Field(description="Contains courses mentioned in users query by course_numbers or course_titles.",default=[]) 

    courses_from_users_query_after_summarization : Dict[str,Any] = Field(description="containes final list of coures after llm call courses_from_users_query",default={})

    core_course_numbers : List[str] = Field(description="Contains course numbers of Core Courses the student has to do.",default=[])
    core_course: List[Dict[str, str]] = Field(description="Contains Details about Core Courses the student has to do.",default=[])
    
    course_numbers: List[str] = Field(description="Stores list of course numbers as strings for searching in database by course_number",default=[])
    course_titles: List[str] = Field(description="Stores list of course titles as strings for searching in database by title",default=[])
    
    max_credits:int = Field(description="Maximum credits the student can do during their degree",default=0)
    max_creds_per_sem:int = Field(description="Maximum credits the student can do per semester",default=0)
    min_creds_per_sem:int = Field(description="Minimum credits the student needs to do per semester",default=0)
    
    filtered_course_list: list[list[Dict[str,str]]] = Field(description="List containing list of filtered courses in form of dictionary from full course list",default=[])
    
    number_of_plans : int = Field(description="Current Number of plans made",default=0)
    max_number_of_plans: int = Field(description="Total Number of plans to be made",default=1) 

    semester_plans: List[Dict] = Field(description="Contains semester-wise course schedules for each plan", default=[])
    planning_completed: bool = Field(description="Flag indicating if planning is completed", default=False)

    short_term_plan: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contains the course suggestion of what to take next for short term planning with explanation."
    )
    
    plan_number_to_change: int  = Field(description="The plan number to change",default=1)

    rescheduling_attributes: Dict[str,str] = Field(
        default={},
        description="Contains information about the changes to be done in the plan."
    )

    error:str =  Field(description="Error during Execution",default="")