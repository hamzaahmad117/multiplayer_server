let timerInterval;

document.getElementById('connectBtn').addEventListener('click', connect);
document.getElementById('exitBtn').addEventListener('click', exit);

let websocket;
let playerID;
let transform = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0];
let transformInterval;
let checkTransformInterval;
let messages = [];

// Function to connect to the WebSocket server
function connect() {
    websocket = new WebSocket('ws://127.0.0.1:12345');
    
    websocket.onopen = () => {
        console.log('Connected to the server');
        document.getElementById('connectBtn').style.display = 'none';
        document.getElementById('exitBtn').style.display = 'block';
    };

    websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Received data:', data);
        if (data.time) {
                startTimer(data.time);
        }
        if (data.message) {
            displayMessage(data.message);
        } else {
            handleMessage(data);
        }
    };

    websocket.onclose = () => {
        console.log('Disconnected from the server');
        document.getElementById('connectBtn').style.display = 'block';
        document.getElementById('exitBtn').style.display = 'none';
        clearInterval(transformInterval);
        clearInterval(checkTransformInterval);
        clearInterval(timerInterval);
        transformInterval = null;
        checkTransformInterval = null;
        resetUI();
    };
}

// Function to display messages on the screen
function displayMessage(message) {
    messages.push(message);
    if (messages.length > 4) {
        messages.shift();
    }

    const messageTableBody = document.getElementById('messageTableBody');
    messageTableBody.innerHTML = ''; // Clear the table body

    messages.forEach(msg => {
        const row = document.createElement('tr');
        const cell = document.createElement('td');
        cell.textContent = msg;
        row.appendChild(cell);
        messageTableBody.appendChild(row);
    });

    document.getElementById('messages').style.display = 'block';
}

// Function to handle incoming WebSocket messages
function handleMessage(data) {
    switch (data.step) {
        case 0:
            console.log(`Connected as Player ${data.id}`);
            playerID = data.id;
            document.getElementById('player_id').innerHTML = 'Your ID: ' + playerID
            document.getElementById('player_id').style.display = 'block';

            requestRoomList();
            break;
        case 1:
            displayRoomList(data.rooms);
            break;
        case 2:
            if (!data.error) {
                displayMessage(`You have joined ${data.room} with ${data.current} player(s).`);
                document.getElementById('roomSelection').style.display = 'none';
                if (data.current < data.minimum) {
                    displayMessage(`Game will start after ${data.minimum} players have joined.`)
                }
            } else {
                displayMessage(data.error);
            }
            break;
        case 2.5:
            displayMessage(`Game has started!`);
            document.getElementById('timer').style.display = 'none';
            if (checkTransformInterval) {
                clearInterval(checkTransformInterval);
            }
            setTimeout(() => {
                checkTransformInterval = setInterval(() => {
                    if (websocket.readyState === WebSocket.OPEN) {
                        transform = transform.map(x => x + Math.random() * 0.1 - 0.05);
                        websocket.send(JSON.stringify({ step: 3, player_id: playerID, transform }));
                    } else {
                        clearInterval(checkTransformInterval);
                    }
                }, 2000);
            }, 2000);
            break;
        case 3:
            if (data.transforms) {
                // Update transform with the received data
                transform = data.transforms[playerID] || transform;
                updateTransformTable(data.transforms);
            } else {
                displayMessage("Room doesn't have enough Players.");
                clearInterval(checkTransformInterval);
                clearInterval(transformInterval);
                checkTransformInterval = null;
                transformInterval = null;
            }
            break;
            
        default:
            console.error('Unknown step');
    }
}

// Function to request the room list
function requestRoomList() {
    websocket.send(JSON.stringify({ step: 1 }));
}

// Function to display the room list and add event listener for room selection
function displayRoomList(rooms) {
    const roomList = document.getElementById('roomList');
    roomList.innerHTML = '';
    rooms.forEach(room => {
        const option = document.createElement('option');
        option.value = room;
        option.text = room;
        roomList.appendChild(option);
    });

    document.getElementById('roomSelection').style.display = 'block';

    // Remove any existing event listeners to avoid duplicates
    const newSelectRoomBtn = document.getElementById('selectRoomBtn').cloneNode(true);
    document.getElementById('selectRoomBtn').replaceWith(newSelectRoomBtn);

    newSelectRoomBtn.addEventListener('click', () => {
        const selectedRoom = roomList.value;
        websocket.send(JSON.stringify({ step: 2, game_type: selectedRoom }));
    });
}

// Function to update the transform table with received data
function updateTransformTable(transforms) {
    document.getElementById('transformData').style.display = 'block';

    const tableBody = document.getElementById('transformTableBody');
    tableBody.innerHTML = ''; // Clear the table body

    for (const player in transforms) {
        const row = document.createElement('tr');

        const playerCell = document.createElement('td');
        playerCell.textContent = player;
        row.appendChild(playerCell);

        const transformCell = document.createElement('td');
        transformCell.textContent = transforms[player].join(', ');
        row.appendChild(transformCell);

        tableBody.appendChild(row);
    }
}

// Function to start the timer
function startTimer(seconds) {
    const timerDisplay = document.getElementById('timerDisplay');
    let timeLeft = Math.ceil(seconds);

    clearInterval(timerInterval);
    document.getElementById('timer').style.display = 'block';

    timerInterval = setInterval(() => {
        if (timeLeft <= 0) {
            clearInterval(timerInterval);
            document.getElementById('timer').style.display = 'none';
        } else {
            timerDisplay.textContent = `${timeLeft} second(s) remaining`;
            timeLeft -= 1;
        }
    }, 1000);
}

// Function to handle exiting the WebSocket connection
function exit() {
    if (websocket) {
        websocket.send(JSON.stringify({ step: 4, action: 'exit' }));
        websocket.close();
        clearInterval(transformInterval);
        clearInterval(checkTransformInterval);
        clearInterval(timerInterval);
        transformInterval = null;
        checkTransformInterval = null;
    }
}

// Function to reset the UI
function resetUI() {
    document.getElementById('roomSelection').style.display = 'none';
    document.getElementById('transformData').style.display = 'none';
    document.getElementById('timer').style.display = 'none';
    document.getElementById('messages').style.display = 'none';
    document.getElementById('player_id').style.display = 'none';
    document.getElementById('messageTableBody').innerHTML = ''; // Clear messages
    messages = [];
}

// Handle window unload event to close the WebSocket connection
window.addEventListener('beforeunload', () => {
    if (websocket) {
        websocket.send(JSON.stringify({ step: 4, action: 'exit' }));
        websocket.close();
        clearInterval(transformInterval);
        clearInterval(checkTransformInterval);
        clearInterval(timerInterval);
        transformInterval = null;
        checkTransformInterval = null;
    }
});
