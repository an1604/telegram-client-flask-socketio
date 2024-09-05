# Flask Telegram Client Demo

This Flask-based demo application integrates with a Telegram client to automate sending and receiving text messages and audio files. The app features a web UI that dynamically updates as it interacts with Telegram, allowing users to send and receive messages and audio in real-time.

## Features

- **Real-Time Messaging**: Automatically send and receive text messages between the web UI and Telegram.
- **Audio Support**: Send and receive audio files, which can be dynamically loaded and played through the web interface.
- **Web Interface**: User-friendly interface built with Flask and Socket.IO for real-time updates and interactions.

## Technology Stack

- ![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white) - A micro web framework for Python.
- ![Telethon](https://img.shields.io/badge/Telethon-0000FF?style=for-the-badge) - An asynchronous Telegram client library for Python.
- ![Asyncio](https://img.shields.io/badge/Asyncio-0000FF?style=for-the-badge) - A library to write concurrent code using async/await in Python.
- ![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white) - A deep learning framework for building and training machine learning models.
- ![Hugging Face](https://img.shields.io/badge/Hugging%20Face-FFCA28?style=for-the-badge&logo=huggingface&logoColor=black) - A platform providing state-of-the-art NLP models and tools.

## Getting Started

To set up and run the Flask Telegram Client, follow these steps:

1. **Install the required dependencies**:  
   Ensure you have Python installed, then run the following command to install all necessary dependencies:  
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application**:  
   Start the Flask app by running:  
   ```bash
   python app.py
   ```

3. **Ensure the remote server is running**:  
   Make sure that the WhisperSpeech remote server is up and waiting for requests. You can find the WhisperSpeech remote server setup instructions in the [Deceptify project directory]([https://github.com/yourusername/Deceptify/tree/main/WhisperSpeech](https://github.com/an1604/Deceptify/tree/main/WhisperSpeech)).

## Usage

Once the application is running, you can:

- Use the web UI to send and receive messages and audio files in real-time.
- Monitor the status of incoming and outgoing messages and audio directly through the interface.
