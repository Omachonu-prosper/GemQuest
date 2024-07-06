from pydantic import BaseModel

class RoomDetails(BaseModel):
    category: str
    no_of_questions: int