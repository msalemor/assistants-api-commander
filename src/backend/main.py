from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from assisstantapihelper import AssistantAPIHelper
from openai import AzureOpenAI
from ckvstorehelper import AHMemoryInstance
from models import AssistantCreateRequest, AssistantCreateResponse, KVStoreItem, ResponseMessage, PromptRequest
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, HTTPException, UploadFile
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
memory_store = AHMemoryInstance()
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
                        request.useTools,
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


@app.delete("/api/delete/{userName}")
def delete(userName: str):
    """
    Delete an Assistant for a user
    """
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

    kv_all_users = memory_store.get_all_users()
    for user in kv_all_users:
        # delete_objects(user.username)
        ah = AssistantAPIHelper(client)
        try:
            ah.recall_assistant(user.category)
            ah.cleanup(user.category)
        except:
            logging.error(
                f"Assistant not found for user {user.category} but exits in the database")
            memory_store.del_user(user.category)


# Get the Assistant status for a user
@app.get("/api/status/{userName}", response_model=list[KVStoreItem])
def get_status(userName: str):
    """
    Get the Assistant status for a user
    """

    items = memory_store.get_user(userName)
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

    items = memory_store.get_all_users()
    if items is None or items == []:
        raise HTTPException(
            status_code=404, detail=f"There are no users in the database")
    return items


@app.post("/api/upload/{area}")
async def upload_file(area: str, file: UploadFile = File(...)):
    print(area, file)
    # with open(file.filename, "wb") as buffer:
    #     buffer.write(await file.read())
    return JSONResponse(content={"filename": file.filename}, status_code=200)


# Show the static files
if settings.deploy_spa == "True":
    app.mount("/", StaticFiles(directory="wwwroot", html=True), name="site")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)
