from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class EventRequest(BaseModel):
    name: str

@app.get("/health_check")
async def health_check():
    return {"status": "OK"}

@app.post("/event")
async def event(request: EventRequest):
    return {"hello": request.name}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 