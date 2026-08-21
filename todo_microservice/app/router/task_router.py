from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import TaskModel
from app.schemas import CreateTask, Task, UpdateTask

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/", response_model=list[Task])
async def get_all_tasks(db: AsyncSession = Depends(get_db)):
    query = select(TaskModel).order_by(TaskModel.id).offset(0).limit(10)
    result = await db.execute(query)
    tasks = result.scalars().all()
    return tasks


@router.get("/{task_id}", response_model=Task)
async def get_task_by_id(task_id: int, db: AsyncSession = Depends(get_db)):
    query = select(TaskModel).where(TaskModel.id == task_id)
    result = await db.execute(query)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found",
        )

    return task


@router.post("/", response_model=Task, status_code=status.HTTP_201_CREATED)
async def add_task(task_in: CreateTask, db: AsyncSession = Depends(get_db)):
    new_task = TaskModel(**task_in.model_dump())
    db.add(new_task)

    await db.commit()
    await db.refresh(new_task)

    return new_task


@router.patch("/{task_id}", response_model=Task)
async def update_task(
    task_id: int, new_data: UpdateTask, db: AsyncSession = Depends(get_db)
):
    task_new_data = new_data.model_dump(exclude_unset=True)

    query = select(TaskModel).where(TaskModel.id == task_id)
    result = await db.execute(query)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found",
        )

    for key, value in task_new_data.items():
        setattr(task, key, value)

    await db.commit()
    await db.refresh(task)

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    query = select(TaskModel).where(TaskModel.id == task_id)
    result = await db.execute(query)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found",
        )

    await db.delete(task)
    await db.commit()

    return None
