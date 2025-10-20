from pydantic import BaseModel


class ResultSchema(BaseModel):
    line_id: int
    number: str
    name: str
    isp: str
    description: str
    download: int | None = None
    upload: int | None = None
    used: int | None = None
    usage_perc: int | None = None
    remaining: int | None = None
    renewal_date: str | None = None
    balance: int | None = None

    class Config:
        from_attributes = True
