import logging
import os.path
import string
import threading

from flask import Flask, render_template, session, request, \
    copy_current_request_context, send_file
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
from telegram_client import Client, default_app_id, default_app_hash

from app_utils import *

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
    logging.info("manual_send_message: Sending message to receiver.")
    await client.send_message(receiver, message)


async def manual_send_audio(client, receiver, audio):
    logging.info("manual_send_audio: Sending audio to receiver.")
    await client.send_audio(receiver, audio)


async def authenticate_user(client, auth_code):
    logging.info("authenticate_user: Authenticating user with auth code.")
    await client.sign_in(auth_code)


def background_thread():
    logging.info("background_thread: Starting background thread...")
    global new_message_event, message_tuple, socketio
    global audio_tuple, new_audio_event
    global ask_for_new_messages_event, new_messages
    global client_auth_event
    global auth_code_set_event, code

    client = Client(default_app_id, default_app_hash, "+972522464648", client_auth_event)
    logging.info("background_thread: Client connected.")
    while True:
        socketio.sleep(5)
        if auth_code_set_event.is_set() and code is not None:
            logging.info("background_thread: Auth code set, proceeding with authentication.")
            client_auth_event.clear()
            client.loop.run_until_complete(authenticate_user(client, code))
        if client_auth_event.is_set():
            logging.info("background_thread: Client authenticated, emitting client_auth.")
            client_auth_event.clear()
            socketio.emit("client_auth")
        if new_message_event.is_set() and message_tuple is not None:
            logging.info(f"background_thread: New message event set with message_tuple: {message_tuple}")
            new_message_event.clear()
            client.loop.run_until_complete(manual_send_message(client, message_tuple[0], message_tuple[1]))
            socketio.emit('server_update',
                          {'data': f'Message {message_tuple[1]} Successfully Sent to {message_tuple[0]} :)'})
            message_tuple = None
        if new_audio_event.is_set() and audio_tuple is not None:
            logging.info(f"background_thread: New audio event set with audio_tuple: {audio_tuple}")
            new_audio_event.clear()
            try:
                action, audio_info, regenerate = audio_tuple
                if isinstance(action, tuple):
                    if action[0] == 'generate':
                        tts, profile_name, output_filename, cps = audio_info
                        audio_path = clone(tts, profile_name, output_filename, cps, regenerate=regenerate)
                        if audio_path:
                            logging.info(f'background_thread: Generating audio from {audio_path}')
                            socketio.emit("new_audio", {"tts": tts, "audio_path": audio_path})
                        else:
                            logging.error(
                                "background_thread: Error while trying to generate the speech from remote server")
                            socketio.emit("server_update",
                                          {'data': "Could not clone the audio file. Please try again later."})
                    elif action[0] == 'accept':

                        output_filename = audio_info[0]
                        receiver = action[1]

                        logging.info(f'background_thread: Accepted audio from {output_filename}, to {receiver}')
                        client.loop.run_until_complete(manual_send_audio(client, receiver, output_filename))
                        socketio.emit("server_update", {'data': f'Audio sent to {receiver} :) '})
                audio_tuple = None
            except Exception as e:
                logging.error(f"background_thread: Error processing audio event. {e}")
        if ask_for_new_messages_event.is_set():
            logging.info("background_thread: Handling new messages request.")
            ask_for_new_messages_event.clear()
            new_messages = client.get_messages()
            logging.info(f"background_thread: Retrieved new messages: {new_messages}")
            socketio.emit('server_update', {'data': 'New messages requests handled'})


@app.route('/')
def index():
    logging.info("index: Serving index page.")
    return render_template('index.html')


@app.route('/get_audio')
def get_audio():
    logging.info("get_audio: Processing get_audio request.")
    file_path = request.args.get('file_path')
    if file_path:
        logging.info(f"get_audio: Sending audio file {file_path}.")
        return send_file(file_path, mimetype='audio/mpeg')
    logging.warning("get_audio: Audio file not found.")
    return "Audio file not found", 404


@socketio.on("connect_event")
def connect_event(data):
    global socketio, thread, thread_lock
    logging.info(f"connect_event: New client connected with data: {data}")
    response = data['data']
    logging.info(f"connect_event: New client said: {response}")
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)


@socketio.on("new_message")
def handle_new_message(data):
    global message_tuple
    logging.info(f"handle_new_message: Received data: {data}")
    receiver, message = data['receiver'], data['message']
    message_tuple = (receiver, message)
    new_message_event.set()
    emit("server_update", {'data': f"Request to send message to {message_tuple[0]} with content: {message_tuple[1]}"},
         broadcast=True)


@socketio.on("new_audio_generation")
def handle_new_audio(data):
    global new_audio_event, audio_tuple
    logging.info(f"handle_new_audio: Received data for new audio generation: {data}")
    tts = data['tts']
    profile_name = data['profile_name']
    cps = data['cps']
    action = ("generate",)
    output_filename = get_output_filename(profile_name, tts)
    logging.info("handle_new_audio: Sending the cloning request to the remote server...")
    audio_tuple = (action, (tts, profile_name, output_filename, cps), False)
    new_audio_event.set()
    emit("server_update", {'data': "Request to send audio to remote server..."})


@socketio.on("client_audio_decision")
def handle_audio_decision(data):
    global new_audio_event, audio_tuple
    logging.info(f"handle_audio_decision: Received client decision data: {data}")
    action, output_filename, receiver = data['action'], data['audio'], data['receiver']
    if action == "accept":
        audio_tuple = ((action, receiver), (output_filename,), False)
        new_audio_event.set()
        emit("server_update", {'data': "Client has accepted the audio"}, broadcast=True)
    else:
        tts, profile_name, cps = data['tts'], data['profile_name'], data['cps']
        action = ("generate",)
        audio_tuple = (action, (tts, profile_name, output_filename, cps), True)
        new_audio_event.set()
        emit("server_update", {'data': 'Client has not accepted the audio, regenerate it.'}, broadcast=True)


@socketio.on('ask_for_new_messages')
def handle_ask_for_new_messages():
    global ask_for_new_messages_event, new_messages
    logging.info("handle_ask_for_new_messages: Handling request for new messages.")
    ask_for_new_messages_event.set()
    emit("new_messages_update", {'data': new_messages}, broadcast=True)


@socketio.on("auth_code")
def handle_auth_code(data):
    global code, auth_code_set_event
    logging.info(f"handle_auth_code: Received auth code data: {data}")
    code = data['code']
    auth_code_set_event.set()
    emit("server_update", {'data': "Authentication request sent."})


if __name__ == '__main__':
    logging.info("Starting SocketIO server...")
    socketio.run(app, debug=True, host='0.0.0.0', use_reloader=True)
