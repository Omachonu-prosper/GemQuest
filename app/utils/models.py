from pydantic import BaseModel

class RoomDetails(BaseModel):
    category: str
    no_of_questions: int


class ModeratorDetails(BaseModel):
    moderator_token: str 