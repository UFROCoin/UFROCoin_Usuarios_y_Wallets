import json

import pika

from src.core.config import settings


BLOCKCHAIN_EVENTS_EXCHANGE = "ufrocoin.blockchain.events"
WALLET_CREDIT_ROUTING_KEY = "wallet.credit.issued"


def publish_event(routing_key: str, payload: dict) -> None:
    if not settings.rabbitmq_url:
        raise RuntimeError("RABBITMQ_URL is not configured")

    parameters = pika.URLParameters(settings.rabbitmq_url)
    connection = pika.BlockingConnection(parameters)
    try:
        channel = connection.channel()
        channel.exchange_declare(
            exchange=BLOCKCHAIN_EVENTS_EXCHANGE,
            exchange_type="topic",
            durable=True,
        )
        channel.basic_publish(
            exchange=BLOCKCHAIN_EVENTS_EXCHANGE,
            routing_key=routing_key,
            body=json.dumps(payload).encode("utf-8"),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
            ),
        )
    finally:
        connection.close()
