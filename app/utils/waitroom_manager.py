from app.utils.room_manager import RoomManager


class WaitroomManager(RoomManager):
    def __init__(self) -> None:
        super().__init__()
    
    async def start_game(self, room_id: str):
        """
        ### Upgrade the state of a game from the waitroom to a gameroom

        #### Params
        - room_id: The id of the room we want to start its game
        """
        room = self.rooms.get(room_id)
        if not room:
            return False
        
        await self.broadcast_json(room_id=room_id,
            data={
                'message': 'Game started',
                'action': 'start_game',
            })