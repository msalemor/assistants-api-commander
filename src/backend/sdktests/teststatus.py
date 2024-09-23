from openai import AzureOpenAI
from assisstantapihelper import AssistantAPIHelper as Helper
import settings

settings = settings.Instance()


# Create an Azure OpenAI client
client = AzureOpenAI(api_key=settings.api_key,
                     api_version=settings.assistants_api_version,
                     azure_endpoint=settings.api_endpoint)

user_name = 'user1@email.com'

ah = Helper(client)
ah.cleanup(user_name)
ah.create_assistant(user_name, "name", "instructions",
                    settings.chat_model,
                    True,
                    True,
                    [],
                    False,
                    "",
                    [])


print(ah.process(
    {'role': 'user', 'content': 'What is the current weather in Miami, Florida and in London, UK? What is the current price of MSFT and APPL?'}))
print(ah.process(
    {'role': 'user', 'content': 'What is the current value of 10 shares of Microsoft?'}))

ah.cleanup(user_name)
