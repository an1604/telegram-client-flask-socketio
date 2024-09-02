import asyncio
import os
import logging
from telethon import TelegramClient, events, errors
from dotenv import load_dotenv

load_dotenv()
default_app_id = os.getenv('TELEGRAM_CLIENT_APP_ID')
default_app_hash = os.getenv('TELEGRAM_CLIENT_APP_HASH')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Client(object):
    def __init__(self, app_id, app_hash, phone_number, auth_event):
        logging.info(f"Client.__init__: Initializing client with phone number {phone_number}")
        self.app_id = app_id
        self.app_hash = app_hash
        self.phone_number = phone_number
        self.auth_event = auth_event

        self.messages_received = []
        self.loop = None
        self.make_event_loop()

        self.client = TelegramClient('session_name', self.app_id, self.app_hash)
        self.initialize_client()

    def handle_routes(self, client):
        logging.info(f"Client.handle_routes: Handling routes for client {client}")

        @client.on(events.NewMessage)
        async def handle_new_message(event):
            message = event.message.message
            logging.info(f"Client.handle_routes.handle_new_message: New message received: {message}")
            self.messages_received.append(message)

    def initialize_client(self):
        logging.info("Client.initialize_client: Initializing client.")
        self.handle_routes(self.client)

        self.loop.create_task(self.run_client())
        logging.info("Client.initialize_client: Added run_client to the loop.")

    async def run_client(self):
        logging.info("Client.run_client: Running client...")
        try:
            await self.client.connect()
            await self.client.start(phone=self.phone_number)
            logging.info('Client.run_client: Client is running...')
            await self.client.run_until_disconnected()
        except errors.AuthKeyUnregisteredError:
            logging.error("Client.run_client: Authorization key not found or invalid. Re-authenticating...")
            await self.authenticate_client()
            await self.run_client()
        except Exception as e:
            logging.error(f"Client.run_client: An error occurred: {e}")
            await self.client.disconnect()

    async def send_message(self, receiver, message):
        logging.info(f"Client.send_message: Sending message to {receiver}")
        try:
            await self.client.connect()
            self.handle_routes(self.client)
            await self.client.send_message(receiver, message)
            logging.info(f'Client.send_message: Message sent: {message}')
        except errors.AuthKeyUnregisteredError:
            logging.error("Client.send_message: Authorization key not found or invalid. Re-authenticating...")
            await self.authenticate_client()
            await self.send_message(receiver, message)

    async def send_audio(self, receiver, audiofile_path):
        logging.info(f"Client.send_audio: Sending audio file {audiofile_path} to {receiver}")
        try:
            await self.client.connect()
            self.handle_routes(self.client)
            if await self.client.is_user_authorized():
                if audiofile_path and os.path.exists(audiofile_path):
                    logging.info("Client.send_audio: Audio file found!")
                    await self.client.send_file(receiver, audiofile_path)
                else:
                    logging.warning(f"Client.send_audio: Audio file {audiofile_path} does not exist.")
        except errors.AuthKeyUnregisteredError:
            logging.error("Client.send_audio: Authorization key not found or invalid. Re-authenticating...")
            await self.authenticate_client()
            await self.send_audio(receiver, audiofile_path)

    def get_messages(self):
        logging.info("Client.get_messages: Getting received messages.")
        return self.messages_received

    def make_event_loop(self):
        logging.info("Client.make_event_loop: Creating event loop.")
        try:
            self.loop = asyncio.get_event_loop()
            asyncio.set_event_loop(self.loop)
        except RuntimeError as e:
            logging.error(f"Client.make_event_loop: RuntimeError encountered: {e}")
            if str(e).startswith('There is no current event loop in thread'):
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
                logging.info("Client.make_event_loop: New event loop created.")
            else:
                raise

    async def stop_client(self):
        logging.info("Client.stop_client: Stopping client.")
        if self.loop:
            self.loop.close()
            self.loop = None
        await self.client.disconnect()
        logging.info('Client.stop_client: Client disconnected.')

    async def authenticate_client(self):
        logging.info("Client.authenticate_client: Authenticating client.")
        self.auth_event.set()
        await self.client.send_code_request(self.phone_number)
        code = input('Enter the code you received: ')
        await self.client.sign_in(self.phone_number, code)

    async def sign_in(self, code):
        logging.info(f"Client.sign_in: Signing in with code {code}.")
        await self.client.sign_in(self.phone_number, code)
