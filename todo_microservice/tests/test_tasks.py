import pytest
from httpx import AsyncClient
from app.models import TaskModel


@pytest.mark.asyncio
async def test_show_tasks_list_empty(client: AsyncClient):
    response = await client.get("/api/tasks/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


@pytest.mark.asyncio
async def test_show_tasks_list(client: AsyncClient, fixture_task: TaskModel):
    response = await client.get("/api/tasks/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == fixture_task.id


@pytest.mark.asyncio
async def test_show_task_by_id(client: AsyncClient, fixture_task: TaskModel):
    response = await client.get(f"/api/tasks/{fixture_task.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == fixture_task.id


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient, fixture_task: TaskModel):
    response = await client.delete(f"/api/tasks/{fixture_task.id}")
    assert response.status_code == 204

    get_task = await client.get(f"/api/tasks/{fixture_task.id}")
    assert get_task.status_code == 404


@pytest.mark.asyncio
async def test_update_task(client: AsyncClient, fixture_task: TaskModel):
    new_data = {"title": "new title"}
    response = await client.patch(f"/api/tasks/{fixture_task.id}", json=new_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "new title"
    assert data["description"] == fixture_task.description


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient):
    new_task = {
        "title": "new task",
        "description": "task desc",
    }
    response = await client.post("/api/tasks/", json=new_task)
    assert response.status_code == 201
    data = response.json()
    created_id = data["id"]

    get_response = await client.get(f"/api/tasks/{created_id}")
    assert get_response.status_code == 200
    new_task_data = get_response.json()
    assert new_task_data["title"] == "new task"
