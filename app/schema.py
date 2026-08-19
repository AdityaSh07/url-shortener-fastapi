from pydantic import BaseModel, HttpUrl


class URLCreate(BaseModel):
    url: HttpUrl


class URLResponse(BaseModel):
    short_code: str
    short_url: str