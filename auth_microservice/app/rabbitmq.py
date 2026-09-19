import os
from typing import Any
import aio_pika
import json
import logging

from pydantic import BaseModel

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL")

async def publish_event(routing_key: str, payload: BaseModel | dict[str, Any]) -> None:
    data = payload.model_dump() if isinstance(payload, BaseModel) else payload

    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(
                "app_events", aio_pika.ExchangeType.TOPIC, durable=True
            )

            message = aio_pika.Message(
                body=json.dumps(data).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )
            await exchange.publish(message, routing_key=routing_key)
            logger.info(f"[EVENT] Published {routing_key}")
    except Exception as e:
        logger.error(f"[EVENT ERROR] Failed to send {routing_key}: {e}")