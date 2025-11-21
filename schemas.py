from pydantic import BaseModel


class CreatePageRequest(BaseModel):
    parent_id: str
    title: str
    content: str | None = None


class AppendRequest(BaseModel):
    page_id: str
    content: str


class UpdateTitleRequest(BaseModel):
    page_id: str
    new_title: str
