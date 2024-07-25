import requests as req
import json
import asyncio
import time
from websockets.sync.client import connect

class TestRoom():
    def __init__(self) -> None:
        self.users = []

    def createWaitRoom(self) -> dict:
        room = req.post(
            url="http://127.0.0.1:8000/gameroom/create",
            headers={
                'X_API_Token': 'TRIV_AI'
            },
            data=json.dumps({
                "category": "Technology",
                "no_of_questions": 3
            })
        )

        self.room = room.json()
        self.room_id = self.room['room_id']
        self.moderator_token = self.room['moderator_token']
        print('Created_room', self.room_id, self.moderator_token)

    def startGame(self):
        game = req.post(
            url=f"http://127.0.0.1:8000/game/{self.room_id}/start",
            headers={
                'X_API_Token': 'TRIV_AI'
            },
            data=json.dumps({
                "moderator_token": self.moderator_token
            })
        )
        if game.status_code == 200:
            print('Game started')
        else:
            print('Could not start game')

    def joinWaitroom(self):
        with connect(f"ws://localhost:8000/waitroom/{self.room_id}") as websocket:
            message = json.loads(websocket.recv())
            if message.get('current_user'):
                self.users.append(message['current_user'])
            print(message)

    def joinGameRoom(self, moderator, user_index):
        uri = f"ws://localhost:8000/gameroom/{self.room_id}/{self.users[user_index]}"
        if moderator:
            uri + f"?moderator_token={self.moderator_token}"

        with connect(uri) as websocket:
            message = websocket.recv()
            print(f"Received: {message}")

tr = TestRoom()
tr.createWaitRoom()
tr.joinWaitroom()
time.sleep(3)
tr.joinWaitroom()
print(tr.users)
tr.startGame()
# tr.joinGameRoom(True, 0)
# tr.joinGameRoom(True, 1)

