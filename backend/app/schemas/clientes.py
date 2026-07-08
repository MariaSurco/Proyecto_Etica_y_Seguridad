from pydantic import BaseModel


class ClienteOut(BaseModel):
    cliente_id: str
    deposit: str | None = None

    class Config:
        extra = "allow"
