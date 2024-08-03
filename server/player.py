import asyncio

class PlayerManager:
    def __init__(self, max_players=10):
        self.players = {}
        self.lock = asyncio.Lock()
        self.next_player_id = 0
        self.max_players = max_players

    async def add_player(self):
        async with self.lock:
            if len(self.players) < self.max_players:
                player_id = self.next_player_id
                self.players[player_id] = {"transform": [0.0] * 12, "state": 0, "room": None}
                self.next_player_id += 1
                return player_id
            return None
        
    async def remove_player(self, player_id):
        if player_id in self.players:
            del self.players[player_id]

    async def update_transform(self, player_id, transform):
        async with self.lock:
            if player_id in self.players:
                self.players[player_id]['transform'] = transform

    async def get_transforms(self, player_ids=None):
        async with self.lock:
            if not player_ids:
                return {player_id: self.players[player_id]['transform'] for player_id in self.players}
            return {player_id: self.players[player_id]['transform'] for player_id in player_ids if player_id in self.players}
        
