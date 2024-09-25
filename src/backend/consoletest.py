from openai import AzureOpenAI
from assisstantapihelper import AssistantAPIHelper as Helper
import settings

settings = settings.Instance()


# Create an Azure OpenAI client
client = AzureOpenAI(api_key=settings.api_key,
                     api_version=settings.assistants_api_version,
                     azure_endpoint=settings.api_endpoint)

# The helper can handle state for users, so we need a user id
user_name = 'user1@email.com'

# Create an assistant for the user
ah = Helper(client)

# just in case, delete the objects from the previeous run
ah.cleanup(user_name)

# create a new assistant
ah.create_assistant(user_name, "name", "instructions",
                    settings.chat_model,
                    True,  # use tools
                    True,  # Use Code interpreter
                    [],  # Code interpreter file urls
                    False,  # use File Search
                    "",  # File Search store name
                    [])  # File Search file urls

# process some requests
print(ah.process(
    {'role': 'user', 'content': 'What is the current weather in Miami, Florida and in London, UK? What is the current price of MSFT and APPL?'}))

# process another request
print(ah.process(
    {'role': 'user', 'content': 'What is the current value of 10 shares of Microsoft?'}))

# cleanup
ah.cleanup(user_name)
