from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# Хранение сообщений и пользователей
messages = []
users = {}

@app.route('/')
def index():
    """Главная страница с чатом"""
    return render_template('chat.html')

@app.route('/messages')
def get_messages():
    """Получить историю сообщений"""
    return jsonify(messages)

@socketio.on('connect')
def handle_connect():
    """Обработка подключения клиента"""
    print(f'Клиент подключился: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    """Обработка отключения клиента"""
    if request.sid in users:
        username = users[request.sid]
        del users[request.sid]
        socketio.emit('user_left', {'username': username, 'timestamp': get_timestamp()})
        print(f'Пользователь {username} отключился')

@socketio.on('join')
def handle_join(data):
    """Обработка присоединения пользователя"""
    username = data['username']
    users[request.sid] = username
    socketio.emit('user_joined', {
        'username': username,
        'timestamp': get_timestamp(),
        'users_count': len(users)
    })
    print(f'Пользователь {username} присоединился к чату')

@socketio.on('message')
def handle_message(data):
    """Обработка нового сообщения"""
    username = users.get(request.sid, 'Аноним')
    message_data = {
        'id': len(messages) + 1,
        'username': username,
        'text': data['text'],
        'timestamp': get_timestamp()
    }
    messages.append(message_data)
    
    # Отправляем сообщение всем клиентам
    socketio.emit('new_message', message_data)
    print(f'Сообщение от {username}: {data["text"]}')

def get_timestamp():
    """Получить текущее время в формате строки"""
    return datetime.datetime.now().strftime('%H:%M:%S')

if __name__ == '__main__':
    print("Запуск веб-чата...")
    print("Откройте браузер и перейдите по адресу: http://localhost:5000")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)