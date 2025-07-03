import json
import logging
from typing import Optional
import pika
from pika.exceptions import AMQPError
from pika.adapters.blocking_connection import BlockingChannel
from .events import BaseEvent

logger = logging.getLogger(__name__)

class EventPublisher:
    def __init__(self, rabbitmq_url: str, exchange_name: str = "communication_platform"):
        self.rabbitmq_url = rabbitmq_url
        self.exchange_name = exchange_name
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[BlockingChannel] = None
        try:
            self.connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
            self.channel = self.connection.channel()
            self.channel.exchange_declare(
                exchange=self.exchange_name,
                exchange_type="topic",
                durable=True
            )
            logger.info(f"Connected to RabbitMQ and declared exchange '{self.exchange_name}'")
        except AMQPError as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def publish(self, event: BaseEvent, routing_key: str) -> bool:
        if not self.channel or self.channel.is_closed:
            logger.error("Cannot publish event: channel is not open.")
            return False
        try:
            body = event.model_dump_json().encode("utf-8")
            properties = pika.BasicProperties(
                delivery_mode=2,  # persistent
                content_type="application/json",
                headers={
                    "event_type": event.event_type.value,
                    "trace_id": str(event.trace_id),
                    "source_service": event.source_service,
                },
            )
            self.channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=routing_key,
                body=body,
                properties=properties
            )
            logger.info(f"Published event '{event.event_type.value}' with routing_key '{routing_key}'")
            return True
        except AMQPError as e:
            logger.error(f"Failed to publish event '{event.event_type.value}' with routing_key '{routing_key}': {e}")
            return False

    def close(self):
        try:
            if self.channel and self.channel.is_open:
                self.channel.close()
            if self.connection and self.connection.is_open:
                self.connection.close()
            logger.info("Closed RabbitMQ connection and channel.")
        except AMQPError as e:
            logger.error(f"Error closing RabbitMQ connection or channel: {e}") 