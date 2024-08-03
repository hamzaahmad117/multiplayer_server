import asyncio
import json

class WaitingRoom:
    def __init__(self, game_type, min_players, max_players, wait_time):
        self.game_type = game_type
        self.min_players = min_players
        self.max_players = max_players
        self.wait_time = wait_time
        self.start_the_game = False
        self.players = {}
        self.lock = asyncio.Lock()
        self.timer_task = None

    async def add_player(self, player_id, socket):
        earlier_state = False
        async with self.lock:
            if len(self.players) < self.max_players:
                earlier_state = self.start_the_game
                    # Inform the new player that the game has already started
        

                # Notify other players of the new join
                for conn in self.players.values():
                    await conn.send(json.dumps({"message": "A new player has joined the room!"}))
                
                self.players[player_id] = socket

                if len(self.players) == self.min_players:
                    message = f"Minimum Players have joined the room. Game will start in {self.wait_time} secs."
                    await self.notify_players({"message": message})
                    if self.timer_task is None or self.timer_task.done():
                        self.timer_task = asyncio.create_task(self.start_timer())

                elif len(self.players) == self.max_players:
                    if not self.start_the_game:
                        self.start_the_game = True
                        await self.notify_players({"step": 2.5, "status": "started"})
                        if self.timer_task is not None:
                            self.timer_task.cancel()
                            self.timer_task = None
                    # else:
                    #     await socket.send(json.dumps({"step": 2.5, "status": "started"}))
                if earlier_state:
                    await socket.send(json.dumps({"step": 2.5, "status": "started"}))
                return True
            return False

    async def remove_player(self, player_id):
        async with self.lock:
            if player_id in self.players:
                del self.players[player_id]
                if len(self.players) < self.min_players:
                    self.start_the_game = False
                    if self.timer_task is not None and not self.timer_task.done():
                        self.timer_task.cancel()
                        self.timer_task = None
                for conn in self.players.values():
                    try:
                        await conn.send(json.dumps({"message": "A player has left the room!"}))
                    except Exception as e:
                        print(f"Error sending message: {e}")
                        pass
                return True
            return False

    async def start_timer(self):
        try:
            print(f"Starting timer for {self.wait_time} seconds")
            await asyncio.sleep(self.wait_time)
            async with self.lock:
                if len(self.players) >= self.min_players:
                    self.start_the_game = True
                    await self.notify_players({"step": 2.5, "status": "started"})
            print(f"Timer completed for {self.wait_time} seconds")
        except asyncio.CancelledError:
            print("Timer was cancelled")
            pass

    async def notify_players(self, message):
        for player in self.players.values():
            await player.send(json.dumps(message))

    async def get_players(self):
        async with self.lock:
            return self.players

    async def get_player_ids(self):
        async with self.lock:
            return list(self.players.keys())

    async def reset(self):
        async with self.lock:
            self.players = {}
            if self.timer_task is not None:
                self.timer_task.cancel()
                self.timer_task = None
