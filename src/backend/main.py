from fastapi.staticfiles import StaticFiles
import kvstore
from openai import AzureOpenAI
from models import AssistantCreateRequest, AssistantCreateResponse, ResponseMessage, PromptRequest
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
import playground
import logging
import settings
# Read the environment variables into settings
settings = settings.Instance()


logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)

# Create the SQLite KV store
kvstore.create_store()


# Create an Azure OpenAI client
client = AzureOpenAI(api_key=settings.api_key,
                     api_version=settings.api_version,
                     azure_endpoint=settings.api_endpoint)

# Create a FastAPI app
app = FastAPI()

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Get the Assistant status for a user
@app.get("/api/status/{userName}", response_model=list[kvstore.KVStoreItem])
def get_status(userName: str):
    items = kvstore.get_user(userName)
    if items is None or items == []:
        raise HTTPException(
            status_code=404, detail=f"user {userName} not found")
    return items


# Create an Assistant for a user
@app.post("/api/create", response_model=AssistantCreateResponse)
async def create_assistant(request: AssistantCreateRequest):

    if request.userName is None or request.userName == "":
        raise HTTPException(
            status_code=400, detail=".userName was not provided")
    if request.name is None or request.name == "":
        raise HTTPException(
            status_code=400, detail=".name was not provided")
    if request.instructions is None or request.instructions == "":
        raise HTTPException(
            status_code=400, detail=".instructions were note provided")
    if request.fileURLs is None or request.fileURLs == []:
        raise HTTPException(
            status_code=400, detail=".fileURLs missing. No files were provided")

    # Create the files
    file_ids = await playground.create_files(
        client, request.userName, request.fileURLs)

    # Create the Assistant and the thread for the user
    (assistant_id, thread_id, tools) = playground.create_assistant(client,
                                                                   request.userName, request.name, request.instructions, file_ids, settings.api_deployment_name)

    if assistant_id is None or thread_id is None:
        raise HTTPException(
            status_code=500, detail="Unable to create the assistant")

    return AssistantCreateResponse(userName=request.userName, name=request.name,
                                   instructions=request.instructions, tools=tools,
                                   assistant_id=assistant_id,
                                   thread_id=thread_id, file_ids=file_ids)


# Process a Prompt using the user's Assistant
@app.post("/api/process", response_model=list[ResponseMessage])
async def post_process(request: PromptRequest):
    if request.userName is None or request.userName == "":
        raise HTTPException(
            status_code=400, detail="No user name name was provided. User name is required.")

    if request.prompt is None or request.prompt == "":
        raise HTTPException(
            status_code=400, detail="No prompt was provided. Prompt is required.")

    # Find the assistant for the user
    user_assistant = kvstore.get_assistant(request.userName)
    assistant = None
    if user_assistant is None:
        raise HTTPException(
            status_code=404, detail=f"Assistant not found for user {request.userName}")
    try:
        assistant = client.beta.assistants.retrieve(user_assistant.value)
    except:
        raise HTTPException(
            status_code=404, detail=f"Assistant not found for user {request.userName}")

    # Find the thread for the user
    user_thread = kvstore.get_thread(request.userName)
    thread = None
    if user_thread is None:
        raise HTTPException(
            status_code=404, detail=f"thread not found for user {request.userName}")
    try:
        thread = client.beta.threads.retrieve(user_thread.value)
    except:
        raise HTTPException(
            status_code=404, detail=f"thread not found for user {request.userName}")

    return await playground.process_prompt(client, assistant, thread, request.prompt, settings.email_URI, request.userName)


# Delete an Assistant
@app.delete("/api/delete/{userName}")
def delete(userName: str):
    error = playground.delete_assistant(client, userName)
    if error is not None:
        raise HTTPException(
            status_code=404, detail=f"User {userName} note found")

    # Delete the KVStore entries for the user
    count = kvstore.del_user(userName)
    if count > 0:
        return {"message": f"Assistant deleted for user: {userName}"}
    else:
        raise HTTPException(
            status_code=404, detail=f"User {userName} not found")


# Maintenance routes
# Delete all Assistants
@app.delete("/api/delete")
def delete_all():

    kv_all_users = kvstore.get_all_user()
    # Delete all the Assistants for all users
    for user in kv_all_users:
        userName = user.value
        error = playground.delete_assistant(client, userName)
        if error is not None:
            raise HTTPException(
                status_code=404, detail=f"User {userName} note found")

        # Delete the KVStore entries for the user
        count = kvstore.del_user(userName)
        if count > 0:
            return {"message": f"Assistant deleted for user: {userName}"}
        else:
            raise HTTPException(
                status_code=404, detail=f"User {userName} not found")


# Get all status for all users
@app.get("/api/status", response_model=list[kvstore.KVStoreItem])
def get_all_status():
    items = kvstore.get_all_user()
    if items is None or items == []:
        raise HTTPException(
            status_code=404, detail=f"There are no users in the database")
    return items


# Show the static files
if settings.deploy_spa == "True":
    app.mount("/", StaticFiles(directory="wwwroot", html=True), name="site")
