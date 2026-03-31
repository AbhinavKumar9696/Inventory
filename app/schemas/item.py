from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel, PaginatedResponse


class ItemCreate(BaseModel):
    sku: str = Field(min_length=3, max_length=100)
    name: str = Field(min_length=2, max_length=255)
    description: str | None = None
    quantity: int = Field(ge=0, default=0)
    reorder_level: int = Field(ge=0, default=10)
    unit_price: Decimal = Field(gt=0)


class ItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    reorder_level: int | None = Field(default=None, ge=0)
    unit_price: Decimal | None = Field(default=None, gt=0)


class ItemRead(ORMModel):
    id: int
    sku: str
    name: str
    description: str | None
    quantity: int
    reorder_level: int
    unit_price: Decimal
    created_at: datetime
    updated_at: datetime


class PaginatedItemRead(PaginatedResponse[ItemRead]):
    pass


class ItemQuantityTotalRead(BaseModel):
    total_quantity: int = Field(ge=0)
