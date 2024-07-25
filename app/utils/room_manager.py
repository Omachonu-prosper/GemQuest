from fastapi import WebSocket
from app.utils.db import db
from uuid import uuid4


class RoomManager:
    def __init__(self) -> None:
        self.rooms: dict[list] = dict()


    async def connect(
            self, 
            websocket: WebSocket,
            room_id: str, 
            username: str,
            game_started: bool
        ) -> bool:
        """
        ### Initiate a client connect to a room

        #### Params
        - websocket: The socket connection instance
        - room_id: The id of the room the user wants to join
        - username: The username generated for the client
        - game_started: Boolean value that will be True if the game has started 
            (If this is false the client is added to a wait room and if true the client is added to a game room)

        #### Return
        - True if the operation is successful
        - False otherwise        
        """
        await websocket.accept()
        room_in_memory = self.rooms.get(room_id)
        if room_in_memory is None:
            return False
        
        room_in_memory.append(websocket)
        if not game_started:
            # The game hasn't started and the client is joining a waitroom
            # Add them to the database 
            room_in_db = await db.rooms.find_one_and_update(
                {'room_id': room_id, 'game_started': game_started},
                {
                    '$set': {f'users.{username}': {'status': 'connected'}}
                }
            )
            if not room_in_db:
                return False
        else:
            # The game has started and the client is joining a gameroom
            # Verify that they are members of the room already
            client_exists = await db.rooms.find_one_and_update(
                {'room_id': room_id, 'game_started': game_started, f'users.{username}': {'$exists': True}},
                {
                    '$set': {f'users.{username}': {'status': 'connected'}}
                }
            )
            if not client_exists:
                return False
        return True


    async def disconnect(self, websocket: WebSocket, room_id: str, username: str):
        """
        ### Set the state of a client in a room to disconected

        #### Params
        - websocket: The client connection we want to disconnect from the room
        - room_id: The id of the room we want to disconnect the client from
        - username: The username of the client we want to disconnect
        """
        self.rooms.get(room_id).remove(websocket)
        await db.rooms.update_one(
            {'room_id': room_id},
            {'$set': {f'users.{username}.status': "disconnected"}}
        )


    async def broadcast_json(self, room_id: str, data: dict, exclude: WebSocket = None):
        """
        ### Braodcast json data to all members of a room

        #### Params
        - room_id: The id of the room we want to broadcast to
        - data: The data we want to braodcast
        - exclude: Optional clients we do not want to broadcast to
        """
        for connection in self.rooms.get(room_id):
            if exclude != connection:
                await connection.send_json(data)


    async def send_json(self, websocket: WebSocket, data: dict):
        """
        ### Send personalized json messages to only one client

        #### Params
        - websocket: The client we want to send data to
        - data: The data er want to send
        """
        await websocket.send_json(data)

    
    def gen_moderator_token(self) -> str:
        """
        ### Generate a moderator token

        #### Return
        - token: The moderator token that would be used to authenticate requests
        """
        return str(uuid4())


    async def verify_moderator_token(self, token: str, room_id: str) -> bool:
        """
        ### Verify that a client is the moderator of a room

        #### Params
        - token: The moderator token to be verified
        - room_id: The id of the room we want to verify it's moderator

        #### Return
        - True if the token is valid and False otherwise
        """
        room = await db.rooms.find_one(
            {'room_id': room_id, 'moderator_token': token}
        )
        if room:
            return True
        return False