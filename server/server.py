import asyncio
import websockets
import json
from player import PlayerManager
from waiting_room import WaitingRoom
from game_room import GameRoom

connected = set() #all players that are connected

waiting_rooms = {
    "Room1": WaitingRoom("Room1", 1, 2, 5),
    "Room2": WaitingRoom("Room2", 2, 4, 20),
    "Room3": WaitingRoom("Room3", 2, 4, 10),
    # Add other game types similarly
}

async def receive_data(websocket, player_manager, player_id):
    print('Receive data function called')
    
    chosen_room = None
    
    try:
        async for message in websocket:
            data = json.loads(message)
            print(f'Message arrived from player {player_id}, {data}')
            step = data.get('step')
            current_state = player_manager.players[player_id]['state']

            # conditions:
            if step == 1 and current_state == 0:
                available_rooms = list(waiting_rooms.keys())
                await websocket.send(json.dumps({"step": 1, "rooms": available_rooms}))
                player_manager.players[player_id]['state'] = 1

            # if connected, add to a room, if already is in a room, remove from that room and add to a different room
            elif step == 2 and (current_state == 1 or current_state == 2):
                
                if current_state == 2:
                    await waiting_rooms[player_manager.players[player_id]['room']].remove_player(player_id)
                    print(f'Player {player_id} removed from {waiting_rooms[player_manager.players[player_id]['room']].game_type}')

                chosen_room = data.get("game_type")
                if chosen_room in waiting_rooms:

                    if await waiting_rooms[chosen_room].add_player(player_id, websocket):
                        
                        # have to create a setter function for it
                        player_manager.players[player_id]['state'] = 2
                        player_manager.players[player_id]['room'] = chosen_room

                        
                        print(f'Player {player_id} added  to {waiting_rooms[player_manager.players[player_id]['room']].game_type}')
                        await websocket.send(json.dumps({"step": 2, "room": chosen_room, "capacity": waiting_rooms[chosen_room].max_players, "current": len(waiting_rooms[chosen_room].players), "minimum": waiting_rooms[chosen_room].min_players}))

                    else:
                        await websocket.send(json.dumps({"step": 2, "error": "Room full"}))
                else:
                    await websocket.send(json.dumps({"step": 2, "error": "Invalid room"}))

            elif step == 3 and current_state == 2:
                if waiting_rooms[chosen_room].start_the_game:
                    if data.get("transform"):
                        await player_manager.update_transform(player_id, data.get("transform"))
                        transforms = await player_manager.get_transforms(await waiting_rooms[chosen_room].get_player_ids())
                        await websocket.send(json.dumps({"step": 3, "transforms": transforms}))  
                    else:
                        await websocket.send(json.dumps({"step": 3, "status": "No transform array provided"}))
                else:
                    await websocket.send(json.dumps({"step": 3, "status": "The Room Doesn't have enough players."}))
            elif step == 4 and current_state >= 1:
                if chosen_room:
                    await waiting_rooms[chosen_room].remove_player(player_id)
                await player_manager.remove_player(player_id)
                #connected.remove(websocket)
                print(f"Player {player_id} exited.")
                await websocket.close()
                #print(player_id, player_manager.players)
                return

            else:
                await websocket.send(json.dumps({"message": "Invalid Query"}))

    except websockets.exceptions.ConnectionClosed:
        print(f"Client {player_id} disconnected")

    finally:
        if chosen_room:
            await waiting_rooms[chosen_room].remove_player(player_id)
        await player_manager.remove_player(player_id)
        connected.remove(websocket)
        print(f"Cleaned up player {player_id}")



async def clean_up_player(chosen_room, player_id, websocket, player_manager):
    if chosen_room:
            await waiting_rooms[chosen_room].remove_player(player_id)
    await player_manager.remove_player(player_id)
    connected.remove(websocket)
    print(f"Cleaned up player {player_id}")


async def handle_client(websocket, path, player_manager):
    connected.add(websocket)
    player_id = await player_manager.add_player()
    print('handle client function called')

    if player_id is None:
        await websocket.send(json.dumps({"step": 0, "error": "Server is full"}))
        await websocket.close()
        return

    player_info = {'step': 0, 'id': player_id}
    await websocket.send(json.dumps(player_info))

    receiver_task = asyncio.create_task(receive_data(websocket, player_manager, player_id))

    await receiver_task
    # for waiting in waiting_rooms:
    #     print(waiting_rooms[waiting].players)





async def main():
    player_manager = PlayerManager()
    
    async with websockets.serve(lambda ws, path: handle_client(ws, path, player_manager), "0.0.0.0", 12345):
        print("Server has started on ws://0.0.0.0:12345")
        await asyncio.Future()

asyncio.run(main())
