from dotenv import load_dotenv
from typing import List
import re
from langchain_community.vectorstores import Chroma
from langchain_openai.embeddings import OpenAIEmbeddings
import warnings
import os

warnings.filterwarnings("ignore")

load_dotenv()

PATH = os.getcwd()

vector_db_path = os.path.join(PATH,"LLM Project","testing","VectorDB")

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

regular_courses_database = Chroma(collection_name="RegularCourses",embedding_function=embeddings,persist_directory = vector_db_path)
special_topics_database = Chroma(collection_name="SpecialCourses",embedding_function=embeddings,persist_directory= vector_db_path)

regular_retriever_for_search_using_titles_for_n = regular_courses_database.as_retriever(search_kwargs={'k': 3})
regular_retriever_for_search_using_titles_for_1 = regular_courses_database.as_retriever(search_kwargs={'k': 1})

special_retriever_for_search_using_titles = special_topics_database.as_retriever(search_kwargs={'k': 1})

def get_course_by_course_number(course_numbers:List[str]):

    regular_courses = regular_courses_database.get(where={"course_number": {"$in": course_numbers}})
    special_courses = special_topics_database.get(where={"course_number": {"$in": course_numbers}})

    all_documents = regular_courses.get("documents", []) + special_courses.get("documents", [])
    all_metadatas = regular_courses.get("metadatas", []) + special_courses.get("metadatas", [])

    course_docs = []
    for doc, meta in zip(all_documents, all_metadatas):
        lines = doc.split("\n")
        description = lines[1].strip() if len(lines) > 1 else ""
        filtered_meta = {k: v for k, v in meta.items() if k not in ['data_id']}
        
        course_docs.append({
            **filtered_meta,
            "description": description
        })
        
    return course_docs

def get_course_by_course_titles(course_titles: List[str],k=None):

    if k is None:
        regular_retriever_for_search_using_titles = regular_retriever_for_search_using_titles_for_n
    else:
        regular_retriever_for_search_using_titles = regular_retriever_for_search_using_titles_for_1
    course_docs = []

    for title in course_titles:
        if re.match(r"(special|topics)",title.lower()):
            docs = special_retriever_for_search_using_titles.invoke(title)
        else:
            docs = regular_retriever_for_search_using_titles.invoke(title)
        for doc_obj in docs:
            doc = doc_obj.page_content
            meta = doc_obj.metadata
            lines = doc.split("\n")
            description = lines[1].strip() if len(lines) > 1 else ""
            filtered_meta = {k: v for k, v in meta.items() if k not in ['data_id']}
            
            course_docs.append({
                **filtered_meta,
                "description": description
            })

    return course_docs

def query_database(course_numbers: List[str], course_titles: List[str], k = None):
    results = []

    if course_numbers:
        results.extend(get_course_by_course_number(course_numbers))

    if course_titles:
        results.extend(get_course_by_course_titles(course_titles,k=k))

    return results
