import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import TaskModel
from app.schemas import CreateTask, Task, UpdateTask
import redis.asyncio as aioredis
from app.redis_client import get_redis

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=list[Task])
async def get_all_tasks(
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    cache_key = "tasks:all:limit=10:offset=0"

    cached_tasks = await redis.get(cache_key)
    if cached_tasks:
        return json.loads(cached_tasks)

    query = select(TaskModel).order_by(TaskModel.id).offset(0).limit(10)
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
):
    cache_key = f"task:{task_id}"

    cached_tasks = await redis.get(cache_key)
    if cached_tasks:
        return json.loads(cached_tasks)

    query = select(TaskModel).where(TaskModel.id == task_id)
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
):
    new_task = TaskModel(**task_in.model_dump())
    db.add(new_task)

    await db.commit()
    await db.refresh(new_task)

    await redis.delete("tasks:all:limit=10:offset=0")

    return new_task


@router.patch("/{task_id}", response_model=Task)
async def update_task(
    task_id: int,
    new_data: UpdateTask,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    task_new_data = new_data.model_dump(exclude_unset=True)

    query = select(TaskModel).where(TaskModel.id == task_id)
    result = await db.execute(query)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Task with id {task_id} not found",
        )

    for key, value in task_new_data.items():
        setattr(task, key, value)

    await db.commit()
    await db.refresh(task)

    await redis.delete(f"task:{task_id}")
    await redis.delete("tasks:all:limit=10:offset=0")

    return task


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    query = select(TaskModel).where(TaskModel.id == task_id)
    result = await db.execute(query)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Task with id {task_id} not found",
        )

    await db.delete(task)
    await db.commit()

    await redis.delete(f"task:{task_id}")
    await redis.delete("tasks:all:limit=10:offset=0")

    return None
