from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)


class UploadQueryParams(BaseModel):
    model_config = ConfigDict(extra="ignore")
    limit: int = Field(default=20, ge=1, le=100)


class AprioriJobRequest(BaseModel):
    upload_id: int
    min_support: float = Field(default=0.1, ge=0.001, le=1.0)
    min_confidence: float = Field(default=0.4, ge=0.001, le=1.0)
    min_lift: float = Field(default=1.0, ge=0.0)
    max_len: int = Field(default=3, ge=1, le=6)


class ClassifierJobRequest(BaseModel):
    upload_id: int
    target_column: str
    epochs: int = Field(default=10, ge=1, le=200)
    batch_size: int = Field(default=32, ge=4, le=512)
    test_size: float = Field(default=0.2, ge=0.05, le=0.5)


class QuestionAnswerRequest(BaseModel):
    context: str = Field(min_length=10, max_length=12000)
    question: str = Field(min_length=2, max_length=500)


class TextGenerationRequest(BaseModel):
    prompt: str = Field(min_length=2, max_length=4000)
    max_new_tokens: int = Field(default=80, ge=16, le=512)
    temperature: float = Field(default=0.7, ge=0.1, le=2.0)


class NerRequest(BaseModel):
    text: str = Field(min_length=2, max_length=8000)


class ChatSessionCreateRequest(BaseModel):
    title: str = Field(default="New Conversation", min_length=1, max_length=120)
    system_prompt: str | None = Field(default=None, max_length=4000)


class ChatMessageCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=12000)
