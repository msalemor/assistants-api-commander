from fastapi.staticfiles import StaticFiles
from assisstantapihelper import AssistantAPIHelper
from openai import AzureOpenAI
from kvstorehelper import AHMemoryInstance
from models import AssistantCreateRequest, AssistantCreateResponse, KVStoreItem, ResponseMessage, PromptRequest
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
import logging
import settings
# Read the environment variables into settings
settings = settings.Instance()


logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)

# Create an Azure OpenAI client
client = AzureOpenAI(azure_endpoint=settings.api_endpoint,
                     api_key=settings.api_key,
                     api_version=settings.assistants_api_version,
                     )

# Create a FastAPI app
memories = AHMemoryInstance()
app = FastAPI()

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create an Assistant for a user


@app.post("/api/create", response_model=AssistantCreateResponse)
def create_assistant(request: AssistantCreateRequest):
    """
    Create an Assistant for a user
    """

    if request.userName is None or request.userName == "":
        raise HTTPException(
            status_code=400, detail=".userName was not provided")
    if request.name is None or request.name == "":
        raise HTTPException(
            status_code=400, detail=".name was not provided")
    if request.instructions is None or request.instructions == "":
        raise HTTPException(
            status_code=400, detail=".instructions were note provided")

    ah = AssistantAPIHelper(client)
    ah.create_assistant(request.userName,
                        request.name,
                        request.instructions,
                        settings.chat_model,
                        request.ci,
                        request.ciFileURLs,
                        request.fs,
                        request.vs_name,
                        request.fsFileURLs)

    response = AssistantCreateResponse(userName=request.userName,
                                       name=request.name,
                                       instructions=request.instructions,
                                       tools="",
                                       assistant_id=ah.assistant.id,
                                       thread_id=ah.thread.id,
                                       file_ids=ah.file_ids)

    return response


# Process a Prompt using the user's Assistant
@app.post("/api/process", response_model=list[ResponseMessage])
def post_process(request: PromptRequest):
    """
    Process a prompt using the user's Assistant
    """

    if request.userName is None or request.userName == "":
        raise HTTPException(
            status_code=400, detail="No user name name was provided. User name is required.")

    if request.prompt is None or request.prompt == "":
        raise HTTPException(
            status_code=400, detail="No prompt was provided. Prompt is required.")

    ah = AssistantAPIHelper(client)
    try:
        ah.recall_assistant(request.userName)
    except:
        raise HTTPException(
            status_code=404, detail=f"Assistant not found for user {request.userName}")

    return ah.process({"role": "user", "content": request.prompt})


# def delete_objects(user_name: str) -> tuple[str, int]:
#     try:
#         kv_items = kvstore.get_user(user_name)
#         if kv_items is None or kv_items == []:
#             raise HTTPException(
#                 status_code=404, detail=f"No objects found for user {user_name}")
#         for item in kv_items:
#             match item.key:
#                 case "assistant":
#                     try:
#                         client.beta.threads.delete(item.value)
#                     except:
#                         pass
#                 case "thread":
#                     try:
#                         client.beta.assistants.delete(item.value)
#                     except:
#                         pass
#                 case "file":
#                     try:
#                         client.files.delete(item.value)
#                     except:
#                         pass
#                 case _:
#                     pass
#         count = kvstore.del_user(user_name)
#         if count > 0:
#             return f"Assistant deleted for user: {user_name}", 200
#         else:
#             return f"User {user_name} not found", 404
#     except:
#         return f"Unable to delete assistant", 500

# Delete an Assistant


@app.delete("/api/delete/{userName}")
def delete(userName: str):
    ah = AssistantAPIHelper(client)
    try:
        ah.recall_assistant(userName)
        ah.cleanup(userName)
    except:
        raise HTTPException(
            status_code=404, detail=f"Assistant not found for user {userName}")


# Delete all Assistants
@app.delete("/api/delete")
def delete_all():
    """
    Delete all Assistants
    """

    kv_all_users = memories.get_all_users()
    for user in kv_all_users:
        # delete_objects(user.username)
        ah = AssistantAPIHelper(client)
        try:
            ah.recall_assistant(user.category)
            ah.cleanup(user.category)
        except:
            logging.error(
                f"Assistant not found for user {user.category} but exits in the database")
            memories.del_user(user.category)


# Get the Assistant status for a user
@app.get("/api/status/{userName}", response_model=list[KVStoreItem])
def get_status(userName: str):
    """
    Get the Assistant status for a user
    """

    items = memories.get_user(userName)
    if items is None or items == []:
        raise HTTPException(
            status_code=404, detail=f"user {userName} not found")
    return items


# Get all status for all users
@app.get("/api/status", response_model=list[KVStoreItem])
def get_all_status():
    """
    Get all status for all users
    """

    items = memories.get_all_users()
    if items is None or items == []:
        raise HTTPException(
            status_code=404, detail=f"There are no users in the database")
    return items


# Show the static files
if settings.deploy_spa == "True":
    app.mount("/", StaticFiles(directory="wwwroot", html=True), name="site")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)
