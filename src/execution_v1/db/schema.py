from pydantic import BaseModel


class ResultSchema(BaseModel):
    line_id: int
    number: str
    name: str
    isp: str
    description: str
    download: float | None = None
    upload: float | None = None
    used: int | None = None
    usage_percentage: int | None = None
    remaining: int | None = None
    renewal_date: str | None = None
    balance: int | None = None

    class Config:
        from_attributes = True
