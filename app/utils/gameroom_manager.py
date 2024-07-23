from app.utils.room_manager import RoomManager
from app.utils.db import db
from app.utils.gemini import generate_questions

import json


class GameroomManager(RoomManager):
    def __init__(self) -> None:
        super().__init__()

    async def end_game(self, room_id: str):
        """
        ### Remove all users from a room
        (to be initiated when an end game event is propagated)

        #### Params
        - room_id: The id of the room we want to end its game
        """
        room = self.rooms.get(room_id)        
        if room:
            for connection in room:
                await connection.close(reason='Game over')
            
            await db.rooms.update_one(
                {'room_id': room_id, 'game_state': 'game_started'},
                {'$set': {'game_state': 'game_ended'}}
            )
            del self.rooms[room_id]
        print(self.rooms)

    
    async def create_room_questions(self, room_id: str) -> bool:
        room = await db.rooms.find_one(
            {'room_id': room_id},
            {'_id': 0, 'category': 1, 'no_of_questions': 1}
        )
        if not room:
            return False
        
        print(room)
        category = room['category']
        no_of_questions = room['no_of_questions']
        questions = generate_questions(category, no_of_questions)
        questions = json.loads(questions)
        await db.rooms.update_one(
            {'room_id': room_id},
            {'$set': {'questions': questions}}
        )
        return True
        