from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
from agent.agent import get_agent
import json
from agent.actionMap import actionMap
import os
import boto3

load_dotenv()

def create_database():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    local_path = os.path.join(BASE_DIR, "agent", "VectorDB", "chroma.sqlite3")

    if not os.path.exists(local_path):
        print("Database not found locally. Downloading from S3...")
        s3 = boto3.client("s3", region_name="us-east-1")
        bucket_name = "llmproject01"
        s3_key = "VectorDB/chroma.sqlite3"
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        s3.download_file(bucket_name, s3_key, local_path)
        print(f"Downloaded {s3_key} to {local_path}")
    else:
        print(f"Database already exists at {local_path}")

# FastAPI setup
app = FastAPI(debug=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://jayjajoo.github.io",
        "http://localhost:3000"
    ],    
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure DB is created at startup
@app.on_event("startup")
def startup_event():
    create_database()
    global agent
    agent = get_agent()
    print("Agent initialized")

class NecessaryParams(BaseModel):
    query: str
    college: str
    department: str
    min_creds_per_sem: int
    max_creds_per_sem: int
    core_course_numbers: List[str]
    max_credits: int
    thread_id: str
    max_number_of_plans: int

def get_state(params: NecessaryParams):
    return {
        "query": params.query,
        "messages":[["User","Query",params.query]],
        "college": params.college,
        "department": params.department,
        "core_course_numbers": params.core_course_numbers,
        "max_credits": params.max_credits,
        "min_creds_per_sem": params.min_creds_per_sem,
        "max_creds_per_sem": params.max_creds_per_sem,
        "max_number_of_plans": params.max_number_of_plans
    }

@app.get("/")
def read_root():
    return {"status": "ok"}

@app.options("/")
def options_root():
    return {}

@app.post("/get_response")
async def stream_response(params: NecessaryParams):
    st = get_state(params)
    config = {"configurable": {"thread_id": params.thread_id}}
    
    async def event_generator():
        yield f"data: Starting the process.\n\n"
        flag = 0
        try:
            for chunk in agent.stream(st, config=config):
                for key, val in chunk.items():
                    if key=="filter_courses_1":
                        flag = 1
                    yield f"data: {actionMap[key]}\n\n"
                if flag==1:
                    yield f"data: Working on plan {str(agent.get_state(config=config).values['number_of_plans'])}/{str(agent.get_state(config=config).values['max_number_of_plans'])}\n\n"
            yield f"data: [FINAL_OUTPUT] {json.dumps(agent.get_state(config=config).values['messages'], indent=2)}\n\n"
        except Exception as e:
            yield f"data: Error {e}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# from fastapi import FastAPI
# from fastapi.responses import StreamingResponse
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from typing import List
# from dotenv import load_dotenv
# from agent.agent import get_agent
# import json
# from agent.actionMap import actionMap

# load_dotenv()

# def create_database():
#     import boto3
#     import os

#     BASE_DIR = os.path.dirname(os.path.abspath(__file__))

#     local_path = os.path.join(BASE_DIR, "agent", "VectorDB", "chroma.sqlite3")
#     if not os.path.exists(local_path):
#         s3 = boto3.client("s3", region_name="us-east-1")
#         bucket_name = "llmproject01"
#         s3_key = "VectorDB/chroma.sqlite3"
#         os.makedirs(os.path.dirname(local_path), exist_ok=True)
#         s3.download_file(bucket_name, s3_key, local_path)

# class NecessaryParams(BaseModel):
#     query: str
#     college: str
#     department: str
#     min_creds_per_sem: int
#     max_creds_per_sem: int
#     core_course_numbers: List[str]
#     max_credits: int
#     thread_id:str
#     max_number_of_plans:int

# def get_state(params: NecessaryParams):
#     return {
#         "query": params.query,
#         "messages":[["User","Query",params.query]],
#         "college": params.college,
#         "department": params.department,
#         "core_course_numbers": params.core_course_numbers,
#         "max_credits": params.max_credits,
#         "min_creds_per_sem": params.min_creds_per_sem,
#         "max_creds_per_sem": params.max_creds_per_sem,
#         "max_number_of_plans":params.max_number_of_plans
#     }

# app = FastAPI(debug=True)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "https://jayjajoo.github.io",
#         "http://localhost:3000"
#     ],    
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# agent = get_agent()

# @app.get("/")
# def read_root():
#     return {"status": "ok"}

# @app.options("/")
# def options_root():
#     return {}


# @app.post("/get_response")
# async def stream_response(params: NecessaryParams):
#     st = get_state(params)
#     config = {"configurable": {"thread_id": params.thread_id}}
#     async def event_generator():
#         yield f"data: Starting the process.\n\n"
#         flag = 0
#         try:
#             for chunk in agent.stream(st, config=config):
#                 for key, val in chunk.items():
#                     if key=="filter_courses_1":
#                         flag = 1
#                     yield f"data: {actionMap[key]}\n\n"
#                 if flag==1:
#                     yield f"data: Working on plan {str(agent.get_state(config=config).values["number_of_plans"])}/{str(agent.get_state(config=config).values["max_number_of_plans"])}\n\n"
#             # print(json.dumps(agent.get_state(config=config).values["messages"], indent=2))
#             yield f"data: [FINAL_OUTPUT] {json.dumps(agent.get_state(config=config).values["messages"], indent=2)}\n\n"
#         except Exception as e:
#             yield f"data: Error {e}\n\n"

#     return StreamingResponse(event_generator(), media_type="text/event-stream")

