from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


class TaskBase(BaseModel):
    title: str = Field(..., description="Назва задачі")
    description: str | None = Field(default=None, description="Опис задачі")
    is_completed: bool = Field(default=False)
    deadline: datetime | None = Field(default=None, description="Дедлайн задачі")


class CreateTask(TaskBase):
    pass


class UpdateTask(BaseModel):
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    is_completed: bool | None = Field(default=None)
    deadline: datetime | None = Field(default=None)


class Task(TaskBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
