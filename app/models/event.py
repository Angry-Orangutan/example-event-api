from pydantic import BaseModel


class EventRequest(BaseModel):
    name: str
