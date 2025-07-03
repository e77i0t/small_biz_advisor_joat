import json
import logging
from typing import Callable, Dict, Optional
import pika
from pika.exceptions import AMQPError
from pika.adapters.blocking_connection import BlockingChannel

logger = logging.getLogger(__name__)

class EventSubscriber:
    def __init__(self, rabbitmq_url: str, service_name: str, exchange_name: str = "communication_platform"):
        self.rabbitmq_url = rabbitmq_url
        self.exchange_name = exchange_name
        self.service_name = service_name
        self.queue_name = f"{service_name}_queue"
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[BlockingChannel] = None
        self.handlers: Dict[str, Callable] = {}
        try:
            self.connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
            self.channel = self.connection.channel()
            self.channel.exchange_declare(
                exchange=self.exchange_name,
                exchange_type="topic",
                durable=True
            )
            self.channel.queue_declare(queue=self.queue_name, durable=True)
            logger.info(f"Connected to RabbitMQ, declared exchange '{self.exchange_name}' and queue '{self.queue_name}'")
        except AMQPError as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def subscribe(self, routing_key: str, handler: Callable):
        self.handlers[routing_key] = handler
        if not self.channel:
            raise RuntimeError("Channel is not initialized.")
        try:
            self.channel.queue_bind(
                exchange=self.exchange_name,
                queue=self.queue_name,
                routing_key=routing_key
            )
            logger.info(f"Subscribed to routing_key '{routing_key}' with handler '{handler.__name__}'")
        except AMQPError as e:
            logger.error(f"Failed to bind queue to routing_key '{routing_key}': {e}")
            raise

    def start_consuming(self):
        def callback(ch, method, properties, body):
            routing_key = method.routing_key
            try:
                event_data = json.loads(body)
                handler = self.handlers.get(routing_key)
                if handler:
                    handler(event_data)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    logger.info(f"Handled event for routing_key '{routing_key}' and acknowledged message.")
                else:
                    logger.warning(f"No handler for routing_key '{routing_key}'. Message not processed.")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            except Exception as e:
                logger.error(f"Error processing message for routing_key '{routing_key}': {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        if not self.channel:
            raise RuntimeError("Channel is not initialized.")
        try:
            self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=callback,
                auto_ack=False
            )
            logger.info(f"Started consuming on queue '{self.queue_name}'")
            self.channel.start_consuming()
        except AMQPError as e:
            logger.error(f"Error during consuming: {e}")
        except KeyboardInterrupt:
            logger.info("Consumption interrupted by user.")
        finally:
            if self.connection and self.connection.is_open:
                self.connection.close()
                logger.info("Closed RabbitMQ connection.") 