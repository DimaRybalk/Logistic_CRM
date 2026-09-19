import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import TaskModel
from app.schemas import CreateTask, Task, UpdateTask
import redis.asyncio as aioredis
from app.redis_client import get_redis
from app.auth import get_current_user, CurrentUser
from app.celery_tasks import send_task_created_notification


router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=list[Task])
async def get_all_tasks(
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    current_user: CurrentUser = Depends(get_current_user),
):
    cache_key = f"company:{current_user.company_id}:user:{current_user.user_id}:tasks:limit=10:offset=0"

    cached_tasks = await redis.get(cache_key)
    if cached_tasks:
        return json.loads(cached_tasks)

    query = (
        select(TaskModel)
        .where(
            TaskModel.user_id == current_user.user_id,
            TaskModel.company_id == current_user.company_id,
        )
        .order_by(TaskModel.id)
        .offset(0)
        .limit(10)
    )
    result = await db.execute(query)
    tasks = result.scalars().all()

    tasks_data = [Task.model_validate(task).model_dump(mode="json") for task in tasks]

    await redis.set(cache_key, json.dumps(tasks_data), ex=300)

    return tasks_data


@router.get("/{task_id}", response_model=Task)
async def get_task_by_id(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    current_user: CurrentUser = Depends(get_current_user),
):
    cache_key = (
        f"company:{current_user.company_id}:user:{current_user.user_id}:task:{task_id}"
    )

    cached_tasks = await redis.get(cache_key)
    if cached_tasks:
        return json.loads(cached_tasks)

    query = select(TaskModel).where(
        TaskModel.id == task_id,
        TaskModel.company_id == current_user.company_id,
        TaskModel.user_id == current_user.user_id,
    )
    result = await db.execute(query)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Task with id {task_id} not found",
        )

    task_data = Task.model_validate(task).model_dump(mode="json")

    await redis.set(cache_key, json.dumps(task_data), ex=600)

    return task_data


@router.post("", response_model=Task, status_code=201)
async def add_task(
    task_in: CreateTask,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    current_user: CurrentUser = Depends(get_current_user),
):
    new_task = TaskModel(
        **task_in.model_dump(),
        user_id=current_user.user_id,
        company_id=current_user.company_id,
    )

    db.add(new_task)

    await db.commit()
    await db.refresh(new_task)

    send_task_created_notification.delay(
        task_id=new_task.id,
        title=new_task.title,
        user_id=current_user.user_id,
        company_id=current_user.company_id,
    )

    await redis.delete(
        f"company:{current_user.company_id}:user:{current_user.user_id}:tasks:limit=10:offset=0"
    )

    return new_task


@router.patch("/{task_id}", response_model=Task)
async def update_task(
    task_id: int,
    new_data: UpdateTask,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    current_user: CurrentUser = Depends(get_current_user),
):
    task_new_data = new_data.model_dump(exclude_unset=True)

    query = select(TaskModel).where(
        TaskModel.id == task_id,
        TaskModel.company_id == current_user.company_id,
        TaskModel.user_id == current_user.user_id,
    )
    result = await db.execute(query)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Task with id {task_id} not found",
        )

    if "deadline" in task_new_data and task_new_data["deadline"] != task.deadline:
        task.is_deadline_notified = False

    for key, value in task_new_data.items():
        setattr(task, key, value)

    await db.commit()
    await db.refresh(task)

    await redis.delete(
        f"company:{current_user.company_id}:user:{current_user.user_id}:task:{task_id}"
    )
    await redis.delete(
        f"company:{current_user.company_id}:user:{current_user.user_id}:tasks:limit=10:offset=0"
    )

    return task


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    current_user: CurrentUser = Depends(get_current_user),
):
    query = select(TaskModel).where(
        TaskModel.id == task_id,
        TaskModel.company_id == current_user.company_id,
        TaskModel.user_id == current_user.user_id,
    )
    result = await db.execute(query)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Task with id {task_id} not found",
        )

    await db.delete(task)
    await db.commit()

    await redis.delete(
        f"company:{current_user.company_id}:user:{current_user.user_id}:task:{task_id}"
    )
    await redis.delete(
        f"company:{current_user.company_id}:user:{current_user.user_id}:tasks:limit=10:offset=0"
    )

    return None
