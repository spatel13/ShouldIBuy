# FastAPI's jsonable_encoder handles converting various non-JSON types,
# such as datetime between JSON types and native Python types.
from fastapi.encoders import jsonable_encoder

# Pydantic, and Python's built-in typing are used to define a schema
# that defines the structure and types of the different objects stored
# in the recipes collection, and managed by this API.
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from .objectid import PydanticObjectId


class StockDatapoint(BaseModel):
    id: Optional[PydanticObjectId] = Field(None, alias="_id")
    ticker: str
    timestamp: datetime
    open: float
    close: float
    high: float
    low: float

    def to_json(self):
        return jsonable_encoder(self, exclude_none=True)

    def to_bson(self):
        data = self.dict(by_alias=True, exclude_none=True)
        if data.get("_id") is None:
            data.pop("_id", None)
        return data
