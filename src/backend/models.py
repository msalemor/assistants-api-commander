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
    name: str
    instructions: str
    fileURLs: list[str]
    userName: str


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
