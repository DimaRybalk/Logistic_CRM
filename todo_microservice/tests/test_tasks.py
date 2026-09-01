import pytest
from httpx import AsyncClient
from app.models import TaskModel
import redis.asyncio as aioredis
import json

BASE_TASKS_URL = "/api/v1/tasks"


@pytest.mark.asyncio
async def test_show_tasks_list_empty(client: AsyncClient):
    response = await client.get(BASE_TASKS_URL)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


@pytest.mark.asyncio
async def test_show_tasks_list(client: AsyncClient, fixture_task: TaskModel):
    response = await client.get(BASE_TASKS_URL)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == fixture_task.id


@pytest.mark.asyncio
async def test_show_task_by_id(client: AsyncClient, fixture_task: TaskModel):
    response = await client.get(f"{BASE_TASKS_URL}/{fixture_task.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == fixture_task.id


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient, fixture_task: TaskModel):
    response = await client.delete(f"{BASE_TASKS_URL}/{fixture_task.id}")

    assert response.status_code == 204

    get_task = await client.get(f"{BASE_TASKS_URL}/{fixture_task.id}")
    assert get_task.status_code == 404


@pytest.mark.asyncio
async def test_update_task(client: AsyncClient, fixture_task: TaskModel):
    new_data = {"title": "new title"}

    response = await client.patch(f"{BASE_TASKS_URL}/{fixture_task.id}", json=new_data)

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

    response = await client.post(BASE_TASKS_URL, json=new_task)

    assert response.status_code == 201
    data = response.json()
    created_id = data["id"]

    get_response = await client.get(f"{BASE_TASKS_URL}/{created_id}")
    assert get_response.status_code == 200
    new_task_data = get_response.json()
    assert new_task_data["title"] == "new task"


@pytest.mark.asyncio
async def test_get_all_tasks_cache(
    client: AsyncClient, fixture_task: TaskModel, fixture_redis_client: aioredis.Redis
):

    cache_key = "tasks:all:limit=10:offset=0"
    assert await fixture_redis_client.get(cache_key) is None

    response = await client.get(BASE_TASKS_URL)
    assert response.status_code == 200

    cached_raw = await fixture_redis_client.get(cache_key)
    assert cached_raw is not None


@pytest.mark.asyncio
async def test_get_task_by_id_cache(
    client: AsyncClient,
    fixture_task: TaskModel,
    fixture_redis_client: aioredis.Redis,
):
    cache_key = f"task:{fixture_task.id}"
    assert await fixture_redis_client.get(cache_key) is None

    response = await client.get(f"{BASE_TASKS_URL}/{fixture_task.id}")
    assert response.status_code == 200

    cached_raw = await fixture_redis_client.get(cache_key)
    assert cached_raw is not None


@pytest.mark.asyncio
async def test_create_task_invalidates_list_cache(
    client: AsyncClient,
    fixture_task: TaskModel,
    fixture_redis_client: aioredis.Redis,
):
    cache_key = "tasks:all:limit=10:offset=0"
    await client.get(BASE_TASKS_URL)
    assert await fixture_redis_client.get(cache_key) is not None

    new_task = {
        "title": "Brand New Task",
        "description": "Task created for testing cache invalidation",
    }
    post_response = await client.post(BASE_TASKS_URL, json=new_task)
    assert post_response.status_code == 201
    assert await fixture_redis_client.get(cache_key) is None


@pytest.mark.asyncio
async def test_delete_task_invalidates_both_caches(
    client: AsyncClient,
    fixture_task: TaskModel,
    fixture_redis_client: aioredis.Redis,
):
    task_cache_key = f"task:{fixture_task.id}"
    list_cache_key = "tasks:all:limit=10:offset=0"

    await client.get(f"{BASE_TASKS_URL}/{fixture_task.id}")
    await client.get(BASE_TASKS_URL)
    assert await fixture_redis_client.get(task_cache_key) is not None
    assert await fixture_redis_client.get(list_cache_key) is not None

    delete_res = await client.delete(f"{BASE_TASKS_URL}/{fixture_task.id}")
    assert delete_res.status_code == 204
    assert await fixture_redis_client.get(task_cache_key) is None
    assert await fixture_redis_client.get(list_cache_key) is None
