import base64
import shutil
from urllib.parse import urlparse

import kvstore
from models import ResponseMessage
import tools
import requests
import logging
import io
import os
import json
import time
from datetime import datetime

from openai.types.beta.threads.message_content_text import MessageContentText
from openai.types.beta.threads.message_content_image_file import MessageContentImageFile


def __user_folders(user_name: str):
    kvitem_user_id = kvstore.get_user_id(user_name)
    return (f"wwwroot/images/{kvitem_user_id.value}/", f"images/{kvitem_user_id.value}/")


def get_response_messages(client, messages, user_name: str) -> list[ResponseMessage]:
    message_list = []
    # From all the messages in the tread, get the messages till the last user message only.
    for message in messages:
        message_list.append(message)
        if message.role == "user":
            break
    # Reverse the messages to show the last user message first
    message_list.reverse()
    # Get a list of Assistant text and images for the UI
    response_messages = []
    for message in message_list:
        for item in message.content:
            if isinstance(item, MessageContentText):
                if item.text.value is None or item.text.value == "":
                    continue
                response_messages.append(
                    ResponseMessage(role=message.role, content=item.text.value))
            elif isinstance(item, MessageContentImageFile):
                # Retrieve image from file by id
                response_content = client.files.content(
                    item.image_file.file_id)
                # Read the bytes
                image_data = response_content.read()
                (user_image_folder_path, url_path) = __user_folders(user_name)
                if not os.path.exists(user_image_folder_path):
                    os.makedirs(user_image_folder_path)
                # Save the file
                full_file_path = f"{user_image_folder_path}{item.image_file.file_id}.png"
                url_path = f"{url_path}/{item.image_file.file_id}.png"
                logging.info(
                    f"Saving image to {full_file_path} and available at {url_path}")
                with open(f"{full_file_path}", "wb") as f:
                    f.write(image_data)
                # Encode the bytes into base64 and then utf-u
                # imageContent = base64.b64encode(image_data).decode('utf-8')
                if (len(message.content) > 0):
                    # Add an image to the list
                    response_messages.append(
                        ResponseMessage(role=message.role, content="", imageContent=f"{url_path}"))
                    # ResponseMessage(role=message.role, content="", imageContent="data:image/png;base64,"+imageContent))
    # Return the list of ResponseMessages
    return response_messages


def __read_file_from_url(url) -> bytes | None:
    try:
        resp = requests.get(url, headers={
                            "content-type": "application/octet-stream"})
        resp.raise_for_status()
        fileBytes = resp.content
        return fileBytes
    except:
        logging.error("Unable to read file from url: %s", url)
        return None


def create_files(client, user_name: str, file_urls: list[str]) -> list[str]:
    # sample file:
    # "https://alemoraoaist.z13.web.core.windows.net/docs/Energy/operating_ranges.csv"
    # "https://alemoraoaist.z13.web.core.windows.net/docs/Energy/wind_turbines_telemetry.csv"
    kv_files = []
    for url in file_urls:
        # Read the file contents from the url
        fileRead = __read_file_from_url(url)

        # Create the Assistant File from the file contents
        assistant_file = client.files.create(
            file=io.BytesIO(fileRead), purpose="assistants")

        # Create the KVStore entry for the file
        if fileRead is not None and assistant_file is not None:
            parsed_url = urlparse(url)
            file_name = os.path.basename(parsed_url.path)
            kv_files.append((file_name, assistant_file.id))

    # Create the KVStore entries for the files
    kvstore.create_files(user_name, kv_files)

    # Get the file ids
    file_ids = []
    for file in kv_files:
        (_, id) = file
        file_ids.append(id)

    # Return the file ids
    return file_ids


def create_thread(client, user_name: str):
    thread = None
    try:
        id = kvstore.get_thread(user_name)
        if id is not None and id != "":
            thread = client.beta.threads.retrieve(id)
        if thread is None:
            raise Exception("Thread not found")
    except:
        thread = client.beta.threads.create()
    kvstore.create_thread(user_name, thread.id)
    return thread


def call_functions(client, thread, run, email_URI: str):
    print("Function Calling")
    required_actions = run.required_action.submit_tool_outputs.model_dump()
    print(required_actions)
    tool_outputs = []
    import json
    for action in required_actions["tool_calls"]:
        func_name = action['function']['name']
        arguments = json.loads(action['function']['arguments'])

        if func_name == "get_stock_price":
            output = tools.get_stock_price(symbol=arguments['symbol'])
            tool_outputs.append({
                "tool_call_id": action['id'],
                "output": output
            })
        elif func_name == "send_email":
            print("Sending email...")
            email_to = arguments['to']
            email_content = arguments['content']
            tools.send_logic_apps_email(email_URI, email_to, email_content)

            tool_outputs.append({
                "tool_call_id": action['id'],
                "output": "Email sent"
            })
        else:
            raise ValueError(f"Unknown function: {func_name}")

    print("Submitting outputs back to the Assistant...")
    client.beta.threads.runs.submit_tool_outputs(
        thread_id=thread.id,
        run_id=run.id,
        tool_outputs=tool_outputs
    )


def create_assistant(client, user_name: str, name: str, instructions: str, file_ids: list[str], api_deployment_name: str):
    assistant = None
    try:
        id = kvstore.get_assistant(user_name)
        if id is not None:
            assistant = client.beta.assistants.retrieve(id)
            if assistant is None:
                raise Exception("Assistant not found")
        else:
            raise Exception("Assistant not found")
    except:
        tools_list = [
            {"type": "code_interpreter"},
            {"type": "function",
             "function": {

                 "name": "get_stock_price",
                 "description": "Retrieve the latest closing price of a stock using its ticker symbol.",
                 "parameters": {
                     "type": "object",
                     "properties": {
                         "symbol": {
                             "type": "string",
                             "description": "The ticker symbol of the stock"
                         }
                     },
                     "required": ["symbol"]
                 }
             }
             },
            {"type": "function",
                "function": {
                    "name": "send_email",
                    "description": "Sends an email to a recipient(s).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "to": {
                                "type": "string",
                                "description": "The email(s) the email should be sent to."
                            },
                            "content": {
                                "type": "string",
                                "description": "The content of the email."
                            }
                        },
                        "required": ["to", "content"]
                    }
                }
             }]

        # Create the Assistant for the user and files
        assistant = client.beta.assistants.create(
            name=name,
            instructions=instructions,
            tools=tools_list,
            model=api_deployment_name,
            file_ids=file_ids
        )
        # Update the user's state
        str_tools = json.dumps(tools_list)
        kvstore.create_assistant(
            user_name, name, instructions, str_tools, assistant.id)

        # Create the thread for the user
        thread = create_thread(client, user_name)

        return (assistant.id, thread.id, str_tools)


def process_prompt(client, assistant, thread, prompt, email_uri, user_name: str) -> list[ResponseMessage]:
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=prompt
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
        instructions="The current date and time is: " +
        datetime.now().strftime("%x %X") + "."
    )

    while True:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id, run_id=run.id)
        if run.status == "completed":
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            return get_response_messages(client, messages, user_name)
        elif run.status == "failed":
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            return get_response_messages(client, messages, user_name)
        elif run.status == "expired":
            # Handle expired
            return []
        elif run.status == "cancelled":
            # Handle cancelled
            return []
        elif run.status == "requires_action":
            call_functions(client, thread, run, email_uri)
        else:
            time.sleep(5)


def delete_assistant(client, user_name) -> str | None:
    # Get the Assistant settings for the user
    user_assistant_settings = kvstore.get_user(user_name)
    if user_assistant_settings is None or user_assistant_settings == []:
        return "User not found"
    try:
        # Delete all the used objects
        for setting in user_assistant_settings:
            if setting.key == "assistant":
                try:
                    client.beta.assistants.delete(setting.value)
                except:
                    logging.warning(
                        f"Unable to delete assistant: {setting.value}")
            elif setting.key == "thread":
                try:
                    client.beta.threads.delete(setting.value)
                except:
                    logging.warning(
                        f"Unable to delete thread: {setting.value}")
            elif setting.key == "file":
                json_data = json.loads(setting.value)
                try:
                    client.files.delete(json_data['id'])
                except:
                    logging.warning(
                        f"Unable to delete file: {json_data['id']}")
    except:
        pass
    try:
        (new_path, _) = __user_folders(user_name)
        shutil.rmtree(new_path)
    except:
        logging.warning(
            f"Unable to delete the image folder for user {user_name}")
    return None
