from langgraph.graph import StateGraph,START,END
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from routers import check_intent,intent_based_router
from planning import (rephrase_query_for_planning_schedule,
                      get_courses_for_building_schedule,
                      check_total_number_of_plans,filter_courses_1,
                      filter_courses_2,
                      get_unique_plans,
                      planning_agent)

from courseExtractor import (extract_course_attributes_from_query,
                             get_course_details,
                             summarize_course_extraction_for_user)

from rescheduling import (extract_plan_index,
                          extract_course_attributes_for_rescheduling,
                          replace_courses,
                          generate_summary_for_rescheduled_plan)

from shortTermPlanning import (get_attributes_for_short_plan,
                               get_course_details_for_short_term_planning,
                               build_short_term_plan)

from greeting import handle_greeting

from states import (get_rescheduling_state,
                    get_plan_state,
                    get_course_fetching_state,
                    get_course_replacement_state,
                    get_short_planning_state)

from pydanticModels import AgentState

import json

load_dotenv()

memory = MemorySaver()

workflow = StateGraph(AgentState)

workflow.add_node("check_intent",check_intent)

workflow.add_node("extract_course_attributes_from_query",extract_course_attributes_from_query)
workflow.add_node("get_course_details",get_course_details)
workflow.add_node("summarize_course_extraction_for_user",summarize_course_extraction_for_user)

workflow.add_node("handle_greeting",handle_greeting)


workflow.add_node("rephrase_query_for_planning_schedule",rephrase_query_for_planning_schedule)
workflow.add_node("get_courses_for_building_schedule",get_courses_for_building_schedule)
workflow.add_node("filter_courses_1",filter_courses_1)
workflow.add_node("get_unique_plans",get_unique_plans)
workflow.add_node("filter_courses_2",filter_courses_2)
workflow.add_node("planning_agent", planning_agent)

workflow.add_node("extract_plan_index",extract_plan_index)
workflow.add_node("extract_course_attributes_for_rescheduling",extract_course_attributes_for_rescheduling)
workflow.add_node("replace_courses",replace_courses)
workflow.add_node("generate_summary_for_rescheduled_plan",generate_summary_for_rescheduled_plan)

workflow.add_node("get_attributes_for_short_plan",get_attributes_for_short_plan)
workflow.add_node("get_course_details_for_short_term_planning",get_course_details_for_short_term_planning)
workflow.add_node("build_short_term_plan",build_short_term_plan)

workflow.add_edge(START,"check_intent")

workflow.add_conditional_edges("check_intent",intent_based_router,{
    "short_term_planning":"get_attributes_for_short_plan",
    "build_schedule":"rephrase_query_for_planning_schedule",
    "course_details":"extract_course_attributes_from_query",
    "greeting":"handle_greeting",
    "reschedule":"extract_plan_index"
})

workflow.add_edge("extract_course_attributes_from_query","get_course_details")
workflow.add_edge("get_course_details","summarize_course_extraction_for_user")
workflow.add_edge("summarize_course_extraction_for_user",END)

workflow.add_edge("rephrase_query_for_planning_schedule","get_courses_for_building_schedule")
workflow.add_edge("get_courses_for_building_schedule","filter_courses_1")
workflow.add_conditional_edges("filter_courses_1",check_total_number_of_plans,{
    "finished":"get_unique_plans",
    "generate_more_plans":"rephrase_query_for_planning_schedule"
})
workflow.add_edge("get_unique_plans","filter_courses_2")
workflow.add_edge("filter_courses_2", "planning_agent")
workflow.add_edge("planning_agent", END)


workflow.add_edge("extract_plan_index","extract_course_attributes_for_rescheduling")
workflow.add_edge("extract_course_attributes_for_rescheduling","replace_courses")
workflow.add_edge("replace_courses","generate_summary_for_rescheduled_plan")
workflow.add_edge("generate_summary_for_rescheduled_plan",END)

workflow.add_edge("get_attributes_for_short_plan","get_course_details_for_short_term_planning")
workflow.add_edge("get_course_details_for_short_term_planning","build_short_term_plan")
workflow.add_edge("build_short_term_plan",END)

workflow.add_edge("handle_greeting",END)

agent = workflow.compile(checkpointer=memory)

config = {"configurable": {"thread_id": "1"}}

# st = get_course_replacement_state()

# st = get_plan_state(index=1)

st = get_short_planning_state()

# st = get_course_fetching_state(query="can u give me course on Blockchain technology in businees?",college="khoury",department= "data science ds" )

# resp = agent.invoke(st,config=config)

# print(json.dumps(resp,indent=2))

# print("="*60)

# print(json.dumps(agent.get_state(config=config),indent=2))

def get_response():
    data = None
    for partial_response in agent.stream(st,config=config):
        for key,val in partial_response.items():
            data = val
            yield f"data: {key}\n\n"
    yield f"data: <FINAL_ANSWER> {json.dumps(val,indent=2)}\n\n"

for val in get_response():
    print(val)