from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from openai import OpenAI, AssistantEventHandler
from typing_extensions import override
import os


# Get the OpenAI API key from the environment variables
api_key = os.getenv("OPENAI_KEY")
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow connections from all origins

# Initialize OpenAI client
client = OpenAI(api_key=api_key)


# Event handler for receiving messages from the client
@socketio.on('start_assistant')
def start_assistant(data):
    thread_id = data['thread_id']
    assistant_id = data['assistant_id']
    message_by_user = data['message']
    print("Thread ID:", thread_id)
    print("Assistant ID:", assistant_id)
    print("Message:", message_by_user)

    # Create a message in the thread
    thread_message = client.beta.threads.messages.create(
        thread_id,
        role="user",
        content=message_by_user,
    )
    print(thread_message)

    # Your OpenAI assistant event handler class
    class EventHandler(AssistantEventHandler):
        @override
        def on_text_created(self, text):
            print("\nAssistant: ")
            send_message("\nAssistant: ")

        @override
        def on_text_delta(self, delta, snapshot):
            print(delta.value, end="", flush=True)
            if delta.annotations:
                send_message("File ID: ")
                print("\nFile ID: ", end="", flush=True)
                print(delta.annotations[0].file_path.file_id, end="", flush=True)
                send_message(f"\n{delta.annotations[0].file_path.file_id}\n")
            send_message(delta.value)

        def on_tool_call_created(self, tool_call):
            print("\nTool: ", tool_call.type, flush=True)
            send_message(f"\nTool: {tool_call.type}\n")

        def on_tool_call_delta(self, delta, snapshot):
            if delta.type == 'code_interpreter' and delta.code_interpreter.input:
                print(delta.code_interpreter.input, end="", flush=True)
                send_message(delta.code_interpreter.input)

    # Initialize the OpenAI assistant and start streaming
    with client.beta.threads.runs.create_and_stream(
            thread_id=thread_id,
            assistant_id=assistant_id,
            event_handler=EventHandler(),
    ) as stream:
        stream.until_done()


# Event handler for sending messages to the client
def send_message(message):
    socketio.emit('message', message)

if __name__ == '_main_':
    socketio.run(app, port=8080)