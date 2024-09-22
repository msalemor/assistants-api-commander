from pydantic import BaseModel


class Status(BaseModel):
    userName: str = ""
    clientUp: bool = False
    assistantUp: bool = False
    threadUp: bool = False
    filesLoaded: bool = False


class Message(BaseModel):
    userName: str
    role: str
    content: str
    bytes: list[str] | None = None


class PromptRequest(BaseModel):
    userName: str
    prompt: str


class AssistantCreateRequest(BaseModel):
    userName: str
    name: str = "Assistant API assistant"
    instructions: str = "You are a general AI assistant."
    ci: bool = True
    ciFileURLs: list[str] = []
    fs: bool = False
    vs_name: str = "vector store name"
    fsFileURLs: list[str] = []


class AssistantCreateResponse(BaseModel):
    userName: str
    name: str | None
    instructions: str | None
    tools: str | None
    assistant_id: str
    thread_id: str
    file_ids: list[str]


class ResponseMessage(BaseModel):
    role: str
    content: str | None
    imageContent: str | None = None
    citations: list | None = None


class KVStoreItem(BaseModel):
    category: str
    key: str
    value: str
