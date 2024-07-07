from fastapi import WebSocket

class RoomManager:
    rooms = {}

    async def connect(self, websocket: WebSocket, room_id: str, username: str) -> bool:
        await websocket.accept()
        if not self.rooms.get(room_id):
            print('room not found')
            return False
        
        self.rooms[room_id]['connections'].append((username, websocket))
        return True

    def disconnect(self, websocket: WebSocket, room_id: str):
        self.rooms[room_id]['connections'].remove(websocket)

    async def broadcast_json(self, room_id: str, data: dict):
        for connection in self.rooms[room_id]['connections']:
            await connection[1].send_json(data)

    async def close_room(self, room_id: str):
        for connection in self.rooms[room_id]['connections']:
            await connection[1].close(reason='Room Closed')