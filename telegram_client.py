import asyncio
import os
from telethon import TelegramClient, events, errors
from dotenv import load_dotenv

load_dotenv()
default_app_id = os.getenv('TELEGRAM_CLIENT_APP_ID')
default_app_hash = os.getenv('TELEGRAM_CLIENT_APP_HASH')


class Client(object):
    def __init__(self, app_id, app_hash, phone_number):
        self.app_id = app_id
        self.app_hash = app_hash
        self.phone_number = phone_number

        self.messages_received = []
        self.loop = None
        self.make_event_loop()

        self.client = TelegramClient('session_name', self.app_id, self.app_hash)
        self.initialize_client()

    def handle_routes(self):
        @self.client.on(events.NewMessage)
        async def handle_new_message(event):
            message = event.message.message  # Extract the message text
            self.messages_received.append(message)
            print(f'New message received: {message}')

    def initialize_client(self):
        self.loop.create_task(self.run_client())  # Run the telegram client as a background task
        print('Client initialized')

    async def run_client(self):
        try:
            await self.client.start(phone=self.phone_number)
            self.handle_routes()
            print('Client is running...')
            await self.client.run_until_disconnected()
        except errors.AuthKeyUnregisteredError:
            print("Authorization key not found or invalid. Re-authenticating...")
            await self.authenticate_client()
            await self.run_client()  # Retry running the client after re-authentication
        except Exception as e:
            print(f"An error occurred: {e}")
            await self.client.disconnect()

    async def send_message(self, receiver, message):
        try:
            await self.client.connect()
            await self.client.send_message(receiver, message)
            print(f'Message sent: {message}')
        except errors.AuthKeyUnregisteredError:
            print("Authorization key not found or invalid. Re-authenticating...")
            await self.authenticate_client()
            await self.send_message(receiver, message)  # Retry sending the message after re-authentication

    async def send_audio(self, receiver, audiofile_path):
        try:
            await self.client.connect()
            if await self.client.is_user_authorized():
                if audiofile_path and os.path.exists(audiofile_path):
                    print("Audio file found!")
                    await self.client.send_file(receiver, audiofile_path)
                else:
                    print(f"Audio file {audiofile_path} does not exist.")
        except errors.AuthKeyUnregisteredError:
            print("Authorization key not found or invalid. Re-authenticating...")
            await self.authenticate_client()
            await self.send_audio(receiver, audiofile_path)  # Retry sending the audio after re-authentication

    def get_messages(self):
        return self.messages_received

    def make_event_loop(self):
        try:
            self.loop = asyncio.get_event_loop()
            asyncio.set_event_loop(self.loop)
        except RuntimeError as e:
            if str(e).startswith('There is no current event loop in thread'):
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
            else:
                raise

    async def stop_client(self):
        if self.loop:
            self.loop.close()
            self.loop = None
        self.client.disconnect()
        print('Client disconnected')

    async def authenticate_client(self):
        await self.client.send_code_request(self.phone_number)
        code = input('Enter the code you received: ')
        await self.client.sign_in(self.phone_number, code)
