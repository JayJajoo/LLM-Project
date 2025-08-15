from .pydanticModels import AgentState

def handle_greeting(state:AgentState):
    return {"messages":[["AI","Greeting","Hi! I’m here if you need anything."]]}