import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="inventory.send_low_stock_alert")
def send_low_stock_alert(item_id: int, sku: str, quantity: int, reorder_level: int) -> None:
    logger.warning(
        "Low stock alert triggered | item_id=%s sku=%s quantity=%s reorder_level=%s",
        item_id,
        sku,
        quantity,
        reorder_level,
    )

