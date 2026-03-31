from datetime import datetime

from pydantic import BaseModel, Field

from app.models.stock_movement import MovementType
from app.schemas.common import ORMModel


class StockMovementCreate(BaseModel):
    item_id: int
    quantity: int = Field(gt=0)
    movement_type: MovementType
    note: str | None = None


class StockMovementRead(ORMModel):
    id: int
    item_id: int
    quantity: int
    movement_type: MovementType
    note: str | None
    performed_by: int
    created_at: datetime

