from openai import AzureOpenAI
import settings

settings = settings.Instance()


# Create an Azure OpenAI client
client = AzureOpenAI(api_key=settings.api_key,
                     api_version=settings.assistants_api_version,
                     azure_endpoint=settings.api_endpoint)

# Upload a file with an "assistants" purpose
file = client.files.create(
    file=open("docs/failed_banks.csv", "rb"),
    purpose='assistants'
)

# Create an assistant using the file ID
assistant = client.beta.assistants.create(
    instructions="You are an AI assistant that can analze the failed banks dataset.",
    model="gpt-4o",
    tools=[{"type": "code_interpreter"}],
    tool_resources={
        "code_interpreter": {
          "file_ids": [file.id]
        }
    }
)

thread = client.beta.threads.create(
    messages=[
        {
            "role": "user",
            "content": "What banks failed in Florida?",
            # # Attach the new file to the message.
            # "attachments": [
            #     {"file_id": message_file.id, "tools": [
            #         {"type": "file_search"}]}
            # ],
        }
    ]
)

run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id, assistant_id=assistant.id
)

messages = list(client.beta.threads.messages.list(
    thread_id=thread.id, run_id=run.id))

message_content = messages[0].content[0].text
annotations = message_content.annotations
citations = []
for index, annotation in enumerate(annotations):
    message_content.value = message_content.value.replace(
        annotation.text, f"[{index}]")
    if file_citation := getattr(annotation, "file_citation", None):
        cited_file = client.files.retrieve(file_citation.file_id)
        citations.append(f"[{index}] {cited_file.filename}")

print(message_content.value)
print("\n".join(citations))

try:
    client.files.delete(file.id)
except:
    pass
try:
    client.beta.threads.delete(thread.id)
except:
    pass
try:
    client.beta.assistants.delete(assistant.id)
except:
    pass
