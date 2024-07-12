from app.utils.room_manager import RoomManager


class WaitroomManager(RoomManager):
    def __init__(self) -> None:
        super().__init__()
    
    async def start_game(self, room_id: str):
        room = self.rooms.get(room_id)
        if not room:
            return False
        
        await self.broadcast_json(room_id=room_id,
            data={
                'message': 'Game started',
                'action': 'start_game',
            })