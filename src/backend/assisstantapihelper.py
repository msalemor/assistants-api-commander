import json
import logging
import os
import random
import shutil
from time import sleep
from urllib.parse import urlparse
import uuid
import httpx
from openai import AzureOpenAI
from openai.types.beta.assistant import Assistant
from openai.types.beta.threads.text_content_block import TextContentBlock
from openai.types.beta.threads.image_file_content_block import ImageFileContentBlock
from ckvstorehelper import AHMemory
from models import ResponseMessage
from tools import get_stock_price


def user_folders(user_name: str):
    kvitem_user_id = user_name
    return (f"wwwroot/images/{kvitem_user_id}/", f"images/{kvitem_user_id}/")


def get_current_temperature(location: str, unit: str) -> str:
    if unit and unit == "":
        return f"Unable to get the temperature for {location}"
    if unit and unit != "" and (unit.lower() == "farenheight" or unit.lower() == "f"):
        return f"Temperature at {location} is {str(random.randint(60,90))} {unit}"
    else:
        return f"Temperature at {location} is {str(random.randint(12,30))} {unit}"


class AssistantAPIHelper:
    def __init__(self, client: AzureOpenAI):
        self.client = client
        self.assistant: Assistant = None
        self.thread = None
        self.file_ids: list[str] = []
        self.vector_store = None
        self.memories = AHMemory()

    def __read_file_from_url(self, url) -> bytes | None:
        try:
            resp = httpx.get(
                url, headers={"content-type": "application/octet-stream"})
        # resp = requests.get(url, headers={
        #                    "content-type": "application/octet-stream"})
        # resp.raise_for_status()
            fileBytes = resp.content
            return fileBytes
        except:
            logging.error("Unable to read file from url: %s", url)
            return None

    def upload_files(self, files: list[str]) -> list[str]:
        file_ids = []
        for file in files:
            file = self.client.files.create(
                file=open(file, "rb"),
                purpose='assistants'
            )
            file_ids.append(file.id)
        return file_ids

    def create_files(self, user_name: str, file_urls: list[str]) -> list[str]:
        if len(file_urls) == 0:
            return []

        # Create a temp folder
        fid = str(uuid.uuid4())
        tfolder = f"wwwroot/{fid}"
        if not os.path.exists(tfolder):
            os.makedirs(tfolder)

        kv_files = []
        for url in file_urls:
            # Read the file contents from the url
            fileRead = self.__read_file_from_url(url)
            if fileRead is not None:
                parsed_url = urlparse(url)
                file_name = os.path.basename(parsed_url.path)

                # write file to disk
                with open(tfolder+"/"+file_name, "wb") as f:
                    f.write(fileRead)

                # Create the Assistant File from the file contents
                # assistant_file = self.client.files.create(
                #     file=io.BytesIO(fileRead), purpose="assistants")
                assistant_file = self.client.files.create(
                    file=open(tfolder+"/"+file_name, "rb"),
                    purpose="assistants")

                # Create the KVStore entry for the file
                # if fileRead is not None and assistant_file is not None:
                #     parsed_url = urlparse(url)
                #     file_name = os.path.basename(parsed_url.path)
                kv_files.append((file_name, assistant_file.id))

                # Save the file to the assistant memory
                self.memories.create_file(user_name, assistant_file.id)

        # Delete the temp folder
        if os.path.exists(tfolder):
            try:
                shutil.rmtree(tfolder)
            except:
                pass

        # Get the file ids
        file_ids = []
        for file in kv_files:
            (_, id) = file
            file_ids.append(id)

        # Return the file ids
        return file_ids

    def create_assistant(self, user_name: str,
                         name: str, instructions: str, model: str,
                         use_tools: bool = True, use_ci: bool = False, code_files: list[str] = [],
                         use_fs: bool = False, vs_name: str = 'Vector store',
                         search_files: list[str] = []) -> tuple[str, str, str]:
        """
        Create an OpenAI Assistant with the given parameters
        """

        self.assistant = self.client.beta.assistants.create(
            name=name,
            instructions=instructions,
            model=model,
        )

        tools = []
        tool_resources = {}

        if use_tools:
            tools = [
                {
                    "type": "function",
                            "function": {
                                "name": "get_current_temperature",
                                "description": "Get the current temperature for a specific location",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "location": {
                                            "type": "string",
                                            "description": "The city and state, e.g., San Francisco, CA"
                                        },
                                        "unit": {
                                            "type": "string",
                                            "enum": ["Celsius", "Fahrenheit"],
                                            "description": "The temperature unit to use. Infer this from the user's location."
                                        }
                                    },
                                    "required": ["location", "unit"]
                                }
                            }
                },
                {
                    "type": "function",
                            "function": {
                                "name": "get_stock_price",
                                "description": "Get the the current stock price for a specific company",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "symbol": {
                                            "type": "string",
                                            "description": "The stock symbol, e.g., AAPL"
                                        }
                                    },
                                    "required": ["symbol"]
                                }
                            }
                }
            ]

        if use_ci:
            tools.append({"type": "code_interpreter"})

        if len(code_files) > 0 and code_files[0] != "":
            self.file_ids = self.create_files(user_name, code_files)
            tool_resources['code_interpreter'] = {"file_ids": self.file_ids}

        if use_fs and len(search_files) > 0 and search_files[0] != "":
            tools.append({"type": "file_search"})

            self.vector_store = self.client.beta.vector_stores.create(
                name=vs_name)
            # Download files to temp folder
            # read the files in temp folder
            # file_streams = [open(path, "rb") for path in search_files]
            # file_batch = self.client.beta.vector_stores.file_batches.upload_and_poll(
            #     vector_store_id=self.vector_store.id, files=file_streams
            # )
            self.file_ids = self.create_files(user_name, search_files)

            # file_batch = self.client.beta.vector_stores.file_batches.create(
            #     vector_store_id=self.vector_store.id, file_id=file)
            try:
                self.client.beta.vector_stores.file_batches.create(
                    vector_store_id=self.vector_store.id,
                    file_ids=self.file_ids)
            except Exception as e:
                logging.error(e)
            # logging.info(file_batch.status)
            # logging.info(file_batch.file_counts)
            tool_resources['file_search'] = {
                "vector_store_ids": [self.vector_store.id]}

        if self.assistant is None:
            raise Exception("Unable to create the assistant")

        self.assistant = self.client.beta.assistants.update(
            assistant_id=self.assistant.id,
            tools=tools if len(tools) > 0 else None,
            tool_resources=tool_resources if len(tool_resources) > 0 else None,
        )

        self.thread = self.client.beta.threads.create()

        self.memories.create_assistant(
            user_name,
            name,
            instructions,
            "",
            self.assistant.id,
            self.thread.id,
            self.vector_store.id if self.vector_store is not None else "")

        # return (assistant.id, thread.id, str_tools)
        return (self.assistant.id, self.thread.id, "")

    def recall_assistant(self, user_name: str) -> None:
        # TODO: Use caching to avoid calling the database multiple times
        kvitems = self.memories.get_user(user_name)
        if kvitems is None or len(kvitems) == 0:
            raise Exception(f"Unable to find user {user_name}")

        for kvitem in kvitems:
            try:
                match kvitem.key:
                    case "assistant":
                        if kvitem.value:
                            self.assistant = self.client.beta.assistants.retrieve(
                                kvitem.value)
                    case "thread":
                        if kvitem.value:
                            self.thread = self.client.beta.threads.retrieve(
                                kvitem.value)
                    case "vector_store":
                        if kvitem.value:
                            self.vector_store = self.client.beta.vector_stores.retrieve(
                                kvitem.value)
            except Exception as e:
                logging.error(e)

    def create_thread(self, messages: list[dict]):
        return self.client.beta.threads.create(messages=messages)

    def create_run(self, thread_id: str, assistant_id: str):
        return self.client.beta.threads.runs.create_and_poll(
            thread_id=thread_id, assistant_id=assistant_id
        )

    def get_messages(self, thread_id: str, run_id: str):
        return list(self.client.beta.threads.messages.list(
            thread_id=thread_id, run_id=run_id))

    def delete_files(self, user_name: str):
        files = self.memories.get_files(user_name)
        for file in files:
            try:
                self.client.files.delete(file.value)
            except:
                logging.error(
                    f"Unable to delete file with ID: {file.value} for {user_name}")

    def delete_thread(self):
        try:
            if self.thread is not None:
                self.client.beta.threads.delete(self.thread.id)
        except:
            logging.error("Unable to delete thread")

    def delete_vector_store(self):
        try:
            if self.vector_store is not None:
                self.client.beta.vector_stores.delete(self.vector_store.id)
        except Exception as e:
            logging.error("Unable to delete vector store", e)

    def delete_assistant(self):
        try:
            if self.assistant is not None:
                self.client.beta.assistants.delete(self.assistant.id)
        except Exception as e:
            logging.error("Unable to delete assistant", e)

    def cleanup(self, user_name: str):
        self.delete_thread()
        self.delete_files(user_name)
        self.delete_vector_store()
        self.delete_assistant()
        self.memories.del_user(user_name)

    def recall_thread(self, thread_id: str) -> None:
        """
        Recall a thread by ID
        """
        self.thread = self.client.beta.threads.retrieve(thread_id)

    def get_response_messages(self, messages: list, user_name: str = "tmp_user") -> list:
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
                if isinstance(item, TextContentBlock):
                    if item.text.value is None or item.text.value == "":
                        continue
                    response_messages.append(
                        ResponseMessage(role=message.role, content=item.text.value))
                elif isinstance(item, ImageFileContentBlock):
                    # Retrieve image from file by id
                    response_content = self.client.files.content(
                        item.image_file.file_id)
                    # Read the bytes
                    image_data = response_content.read()
                    (user_image_folder_path, url_path) = user_folders(user_name)
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

        # message_content = messages[0].content[0].text
        # annotations = message_content.annotations
        # citations = []
        # for index, annotation in enumerate(annotations):
        #     message_content.value = message_content.value.replace(
        #         annotation.text, f"[{index}]")
        #     if file_citation := getattr(annotation, "file_citation", None):
        #         cited_file = self.client.files.retrieve(file_citation.file_id)
        #         citations.append(f"[{index}] {cited_file.filename}")

        # print(message_content.value)
        # print("\n".join(citations))

        # Return the list of ResponseMessages
        return response_messages

    def call_functions(self, run):
        logging.info("Calling tools")
        tool_outputs = []
        for tool in run.required_action.submit_tool_outputs.tool_calls:
            if tool.function.name == "get_current_temperature":
                arguments = json.loads(tool.function.arguments)
                output = get_current_temperature(
                    location=arguments['location'], unit=arguments['unit'])
                tool_outputs.append({
                    "tool_call_id": tool.id,
                    "output": output
                })
            elif tool.function.name == "get_stock_price":
                arguments = json.loads(tool.function.arguments)
                output = get_stock_price(arguments['symbol'])
                tool_outputs.append({
                    "tool_call_id": tool.id,
                    "output": output
                })
            else:
                # raise ValueError(f"Unknown function: {func_name}")
                logging.error(f"Unknown function: {tool.function.name}")

        logging.info("Submitting outputs back to the Assistant...")
        self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=self.thread.id,
            run_id=run.id,
            tool_outputs=tool_outputs
        )

    def process(self, message: dict, managed: bool = True) -> list:
        """
        Process a message with the assistant.

        Args:
            message: dict - the message to process
            managed: bool - if the thread should be managed or not

        Returns:
            list - the processed messages
        """
        # if managed, the assistant will be managed by thread history,
        # otherwise the thread will be deleted after the run.
        if managed:
            if self.thread is None:
                self.thread = self.client.beta.threads.create(
                    messages=[message]
                )
            else:
                self.client.beta.threads.messages.create(
                    self.thread.id,
                    role=message['role'],
                    content=message['content'],
                )
        else:
            self.thread = self.client.beta.threads.create(
                messages=[message]
            )

        # run = self.client.beta.threads.runs.create_and_poll(
        #     thread_id=self.thread.id, assistant_id=self.assistant.id
        # )

        # Create the run but dont wait
        run = self.client.beta.threads.runs.create(
            thread_id=self.thread.id, assistant_id=self.assistant.id
        )

        while True:
            # Check the status
            if run.status == "failed" or run.status == "cancelled" or run.status == "incomplete":
                return []
            if run.status == "completed":
                messages = list(self.client.beta.threads.messages.list(
                    thread_id=self.thread.id, run_id=run.id))

                processed_messages = self.get_response_messages(messages)

                if not managed:
                    self.client.beta.threads.delete(self.thread.id)

                return processed_messages
            elif run.status == "requires_action":
                # Called defined functions
                self.call_functions(run)

            run = self.client.beta.threads.runs.retrieve(
                run.id, thread_id=self.thread.id)

            sleep(.5)

        return []
