import json
from openai import AzureOpenAI
from assisstantapihelper import AssistantAPIHelper as Helper
from ckvstorehelper import AHMemoryInstance
import settings

settings = settings.Instance()


ahmemory = AHMemoryInstance()
ahmemory.create_assistant("user", "name", "instructions",
                          "tools", "assistant_id", "thread_id")
ahmemory.get_user("user")
ahmemory.get_assistant("user")
ahmemory.get_thread("user")


ahmemory.del_thread("user")
ahmemory.del_assistant("user")
ahmemory.del_user("user")


# Create an Azure OpenAI client
client = AzureOpenAI(api_key=settings.api_key,
                     api_version=settings.assistants_api_version,
                     azure_endpoint=settings.api_endpoint)


ah = Helper(client)
ah.create_assistant(
    name="General assistant.",
    instructions="You are a general assistant.",
    model="gpt-4o",
    use_ci=True,
    code_files=["docs/failed_banks.csv"],
    # use_fs=True,
    # vs_name="APIM vector Store",
    # search_files=["docs/apim.txt"]
)
print(ah.assistant.id)

message = {"role": "user",
           "content": "Generate a chart of failed banks by state?"}
print(ah.process(message))

ah1 = Helper(client)
ah1.recall_assistant(ah.assistant.id)

message = {"role": "user",
           "content": "What banks failed in Florida?"}
print(ah1.process(message))

# messages = {"role": "user", "content": "What is APIM?"}
# assistant = ah.process(messages)

# messages = {"role": "user", "content": "What are some APIM features?"}
# assistant = ah.process(messages)

# messages = {"role": "user", "content": "What are some more?"}
# ah.process(messages)

# ah1 = AH(client)
# ah1.recall_assistant(ah.assistant.id)

ah.cleanup()
