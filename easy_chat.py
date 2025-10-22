#pip install flask-socketio
# Просто импортируйте и запустите в отдельном потоке
""" 
from simple_chat_server import app, socketio
import threading

def start_chat():
    socketio.run(app, port=5000)

# Запуск в фоне
chat_thread = threading.Thread(target=start_chat, daemon=True)
chat_thread.start()

print("Чат запущен на http://localhost:5000")

# Ваш основной код продолжает работать...
 """


from flask import Flask, render_template_string
from flask_socketio import SocketIO
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret123'
socketio = SocketIO(app, cors_allowed_origins="*")

# Храним последние 100 сообщений
messages = []
users = set()

@app.route('/')
def chat_page():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Простой Чат</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        body { 
            font-family: Arial; 
            margin: 20px;
            background: #f0f0f0;
        }
        .chat-container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        #messages {
            height: 400px;
            border: 1px solid #ddd;
            padding: 10px;
            overflow-y: auto;
            margin-bottom: 10px;
            background: #fafafa;
        }
        .message {
            margin: 5px 0;
            padding: 5px;
            border-radius: 5px;
        }
        .message.system {
            color: #666;
            font-style: italic;
        }
        .message.user {
            background: #e3f2fd;
        }
        input, button {
            padding: 10px;
            margin: 5px 0;
            width: 100%;
            box-sizing: border-box;
        }
        button {
            background: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
        }
        button:hover {
            background: #45a049;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <h2>💬 Простой Чат</h2>
        <div id="messages"></div>
        <div id="login" style="display: block;">
            <input type="text" id="username" placeholder="Введите ваше имя" maxlength="20">
            <button onclick="joinChat()">Войти в чат</button>
        </div>
        <div id="chat" style="display: none;">
            <input type="text" id="message" placeholder="Введите сообщение..." maxlength="500">
            <button onclick="sendMessage()">Отправить</button>
        </div>
        <div style="text-align: center; color: #666; margin-top: 10px;">
            Онлайн: <span id="online">0</span>
        </div>
    </div>

    <script>
        let socket = null;
        let username = '';

        function joinChat() {
            username = document.getElementById('username').value.trim();
            if (!username) return alert('Введите имя');
            
            socket = io();
            
            socket.emit('join', username);
            
            document.getElementById('login').style.display = 'none';
            document.getElementById('chat').style.display = 'block';
            document.getElementById('message').focus();
            
            socket.on('message', function(data) {
                addMessage(data);
            });
            
            socket.on('user_count', function(count) {
                document.getElementById('online').textContent = count;
            });
            
            socket.on('user_joined', function(data) {
                addSystemMessage(data);
            });
            
            socket.on('user_left', function(data) {
                addSystemMessage(data);
            });
        }

        function sendMessage() {
            const message = document.getElementById('message').value.trim();
            if (!message) return;
            
            socket.emit('message', message);
            document.getElementById('message').value = '';
        }

        function addMessage(data) {
            const messages = document.getElementById('messages');
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${data.type === 'system' ? 'system' : 'user'}`;
            
            if (data.type === 'system') {
                msgDiv.innerHTML = `📢 ${data.text}`;
            } else {
                msgDiv.innerHTML = `<b>${data.username}:</b> ${data.text} <small>(${data.time})</small>`;
            }
            
            messages.appendChild(msgDiv);
            messages.scrollTop = messages.scrollHeight;
        }

        function addSystemMessage(text) {
            addMessage({ type: 'system', text: text });
        }

        document.getElementById('message').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendMessage();
        });
        
        document.getElementById('username').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') joinChat();
        });
    </script>
</body>
</html>
    ''')

@socketio.on('connect')
def handle_connect():
    print('Новое подключение')

@socketio.on('disconnect')
def handle_disconnect():
    if hasattr(handle_connect, 'username'):
        users.discard(handle_connect.username)
        socketio.emit('user_left', f'{handle_connect.username} вышел')
        socketio.emit('user_count', len(users))

@socketio.on('join')
def handle_join(name):
    username = name[:20]  # Ограничиваем длину имени
    handle_connect.username = username
    users.add(username)
    
    # Отправляем историю сообщений новому пользователю
    for msg in messages[-50:]:  # Последние 50 сообщений
        socketio.emit('message', msg)
    
    socketio.emit('user_joined', f'{username} присоединился')
    socketio.emit('user_count', len(users))

@socketio.on('message')
def handle_message(msg):
    username = getattr(handle_connect, 'username', 'Аноним')
    text = msg[:500]  # Ограничиваем длину сообщения
    
    message_data = {
        'type': 'user',
        'username': username,
        'text': text,
        'time': datetime.datetime.now().strftime('%H:%M:%S')
    }
    
    messages.append(message_data)
    if len(messages) > 100:  # Храним только 100 последних сообщений
        messages.pop(0)
    
    socketio.emit('message', message_data)

if __name__ == '__main__':
    print("🚀 Запуск простого чат-сервера...")
    print("📧 Откройте браузер и перейдите по адресу: http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)