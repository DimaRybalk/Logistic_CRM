import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, delete
from app.database import async_session
from app.models import TaskModel
import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.celery_app import celery

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST")
raw_port = os.getenv("SMTP_PORT")
SMTP_PORT = int(raw_port) if raw_port else None
SMTP_FROM = os.getenv("SMTP_FROM")

@celery.task(name="send_task_created_notification")
def send_task_created_notification(
    task_id: int,
    title: str,
    user_id: int,
    company_id: int,
):
    recipient_email = f"user_{user_id}@tenant_{company_id}.local"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Твоя задача: {title}"
    msg["From"] = SMTP_FROM
    msg["To"] = recipient_email

    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #222; line-height: 1.5;">
        <h3>Новая задача:</h3>
        <div style="background: #f4f6f8; padding: 12px 16px; border-radius: 8px; margin: 12px 0;">
          <p style="margin: 0; font-size: 16px;"><b>{title}</b></p>
          <p style="margin: 4px 0 0 0; color: #666; font-size: 13px;">ID задачи: #{task_id}</p>
        </div>
        <p style="color: #777; font-size: 12px;">Уведомление из твоего личного ToDo-списка.</p>
      </body>
    </html>
    """
    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.sendmail(SMTP_FROM, recipient_email, msg.as_string())
        logger.info(f"[MAILPIT] Notification sent to {recipient_email} for task {task_id}")
        return {"status": "sent", "recipient": recipient_email, "task_id": task_id}
    except Exception as e:
        logger.error(f"[MAILPIT] Failed to send email: {e}")
        raise e


async def _check_deadlines_async():
    now = datetime.now(timezone.utc)
    target_time = now + timedelta(minutes=30)

    async with async_session() as session:
        query = select(TaskModel).where(
            TaskModel.is_completed == False,
            TaskModel.is_deadline_notified == False,
            TaskModel.deadline.is_not(None),
            TaskModel.deadline > now,
            TaskModel.deadline <= target_time,
        )
        result = await session.scalars(query)
        tasks = result.all()

        for task in tasks:
            send_task_created_notification.delay(
                task_id=task.id,
                title=f"Напоминание: через 30 минут дедлайн по задаче «{task.title}»",
                user_id=task.user_id,
                company_id=task.company_id,
            )
            task.is_deadline_notified = True

        if tasks:
            await session.commit()

        return len(tasks)

@celery.task(name="check_upcoming_deadlines")
def check_upcoming_deadlines():
    count = asyncio.run(_check_deadlines_async)
    return f"Checked deadlines. Sent reminders for {count} tasks."

async def _cleanup_completed_tasks_async():
    cut_time = datetime.now(timezone.utc) - timedelta(hours=48)
    async with async_session() as session:
        query = delete(TaskModel).where(TaskModel.is_completed == True,
                                        TaskModel.updated_at <= cut_time)
        result = await session.execute(query)
        await session.commit()
        return result.rowcount

@celery.task(name="clean_completed_tasks")
def clean_completed_taks():
    deleted_count = asyncio.run(_cleanup_completed_tasks_async())
    return f"Cleaned up {deleted_count} old completed tasks from personal to-do lists."
