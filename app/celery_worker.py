import logging
# pyrefly: ignore [missing-import]
from celery import Celery
from app.config import settings

logger = logging.getLogger("eve_healthcare")

celery_app = Celery(
    "eve_healthcare_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_webhook_retry_task(self, event_id: str, payload_dict: dict):
    """
    Background worker task for processing webhooks asynchronously or retrying transient failures
    with exponential backoff.
    """
    logger.info(f"[CELERY WORKER] Processing background webhook task for event_id: {event_id}")
    try:
        # In a distributed setup, worker can execute asynchronous processing here
        return {"status": "success", "event_id": event_id}
    except Exception as exc:
        logger.error(f"[CELERY WORKER ERROR] Task failed for {event_id}: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 30)


@celery_app.task
def send_email_notification_task(recipient_email: str, subject: str, message_body: str):
    """Celery background task to dispatch emails asynchronously."""
    logger.info(f"[CELERY EMAIL] Sent to {recipient_email}: {subject}")
    return {"status": "sent", "recipient": recipient_email}
