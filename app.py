import threading

from flask import Flask, render_template, session, request, \
    copy_current_request_context, send_file
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
from telegram_client import Client, default_app_id, default_app_hash

client_auth_event = threading.Event()

auth_code_set_event = threading.Event()
code = None

new_message_event = threading.Event()
message_tuple = None

new_audio_event = threading.Event()
audio_tuple = None

ask_for_new_messages_event = threading.Event()
new_messages = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=None)

thread = None
thread_lock = threading.Lock()


async def manual_send_message(client, receiver, message):
    await client.send_message(receiver, message)


async def manual_send_audio(client, receiver, audio):
    await client.send_audio(receiver, audio)


async def authenticate_user(client, auth_code):
    await client.sign_in(auth_code)


def background_thread():
    print("Starting background thread...")
    global new_message_event, message_tuple, socketio
    global audio_tuple, new_audio_event
    global ask_for_new_messages_event, new_messages
    global client_auth_event
    global auth_code_set_event, code

    client = Client(default_app_id, default_app_hash, "+972522464648",
                    client_auth_event)
    print("Client connected")
    while True:
        socketio.sleep(5)
        if auth_code_set_event.is_set() and code is not None:
            client_auth_event.clear()
            client.loop.run_until_complete(
                authenticate_user(client, code)
            )
        if client_auth_event.is_set():
            client_auth_event.clear()
            socketio.emit("client_auth")
        if new_message_event.is_set() and message_tuple is not None:
            new_message_event.clear()

            client.loop.run_until_complete(
                manual_send_message(client, message_tuple[0], message_tuple[1]))

            socketio.emit('server_update',
                          {'data': f'Message {message_tuple[1]} Successfully Sent to {message_tuple[0]} :)'})
            message_tuple = None
        if new_audio_event.is_set() and audio_tuple is not None:
            new_audio_event.clear()
            client.loop.run_until_complete(
                manual_send_audio(client, audio_tuple[0], audio_tuple[1])
            )
            socketio.emit('server_update',
                          {'data': f'Record {audio_tuple[1]} Successfully Sent to {audio_tuple[0]} :)'})
        if ask_for_new_messages_event.is_set():
            ask_for_new_messages_event.clear()
            new_messages = client.get_messages()

            print(f"from back: {new_messages}")
            socketio.emit('server_update',
                          {'data': 'New messages requests handled'})


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get_audio')
def get_audio():
    return send_file("C:/Users/adina/Desktop/aviv.mp3", mimetype='audio/mpeg')


@socketio.on("connect_event")
def connect_event(data):
    global socketio, thread, thread_lock

    response = data['data']
    print(f"New client said: {response}")
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)


@socketio.on("new_message")
def handle_new_message(data):
    global message_tuple
    print(f"handle_new_message called --> {data}")
    receiver, message = data['receiver'], data['message']
    message_tuple = (receiver, message)
    new_message_event.set()
    emit("server_update",
         {'data': f"Request to send message to {message_tuple[0]} with content: {message_tuple[1]}"}, broadcast=True)


@socketio.on("new_audio_generation")
def handle_new_audio(data):
    tts = data['tts']
    # TODO: Function call to generate TTS

    # This is just a demo:
    audio = r"static/aviv_emergency.mp3"
    emit("new_audio", {"tts": tts, "audio": audio}, broadcast=True)


@socketio.on("client_audio_decision")
def handle_audio_decision(data):
    global new_audio_event, audio_tuple
    action, audio, receiver = data['action'], data['audio'], data['receiver']
    if action == "accept":
        audio_tuple = (receiver, audio)
        new_audio_event.set()
        emit("server_update", {'data': "Client has accepted the audio"}, broadcast=True)
    else:
        emit("server_update", {'data': 'Client has not accepted the audio'}, broadcast=True)


@socketio.on('ask_for_new_messages')
def handle_ask_for_new_messages():
    global ask_for_new_messages_event, new_messages
    ask_for_new_messages_event.set()
    print(f"from handle_ask_for_new_messages --> {new_messages}")
    emit("new_messages_update",
         {'data': new_messages},
         broadcast=True)


@socketio.on("auth_code")
def handle_auth_code(data):
    global code, auth_code_set_event
    code = data['code']
    auth_code_set_event.set()
    emit("server_update", {
        'data': "Authentication request sent."
    })


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0',
                 use_reloader=True)
