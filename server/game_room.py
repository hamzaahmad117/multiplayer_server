class GameRoom:
    def __init__(self, game_type, players):
        self.game_type = game_type
        self.players = players

    async def start(self):
        # Start the game logic
        print(f"Game {self.game_type} started with players: {self.players}")
        # Implement the game logic here