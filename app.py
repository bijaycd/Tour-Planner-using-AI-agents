from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from memory_agent import MemoryAgent
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize FastAPI
app = FastAPI()



memory_agent = MemoryAgent()




# Define data models for API requests
class MemoryRequest(BaseModel):
    user_id: str
    memory: str

class PreferenceRequest(BaseModel):
    user_id: str
    preference: str



# Endpoints for user preferences
@app.get("/user/preferences/{user_id}")
def get_preferences(user_id: str):
    try:
        preferences = memory_agent.get_user_preferences(user_id)
        return preferences
    except Exception as e:
        return {"error": f"Failed to fetch preferences: {e}"}

@app.post("/user/preferences/")
def add_preference(request: PreferenceRequest):
    try:
        memory_agent.add_user_preference(request.user_id, request.preference)
        return {"message": "Preference added successfully"}
    except Exception as e:
        return {"error": f"Failed to add preference: {e}"}




# Endpoints for user memories
@app.get("/user/memories/{user_id}")
def get_memories(user_id: str):
    try:
        memories = memory_agent.retrieve_memories(user_id)
        return memories
    except Exception as e:
        return {"error": f"Failed to fetch memories: {e}"}



@app.post("/user/memories/")
def add_memory(request: MemoryRequest):
    try:
        memory_agent.add_memory(request.user_id, request.memory)
        return {"message": "Memory added successfully"}
    except Exception as e:
        return {"error": f"Failed to add memory: {e}"}
