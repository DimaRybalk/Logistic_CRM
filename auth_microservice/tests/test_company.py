import json
import uuid
from httpx import AsyncClient
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    CompanyInviteModel,
    CompanyMemberModel,
    CompanyModel,
    RoleEnum,
    UserModel,
)

import redis.asyncio as aioredis

BASE_COMPANY_URL = "/api/v1/companies"


@pytest.mark.asyncio
async def test_get_my_company_success(
    client: AsyncClient,
    fixture_user: UserModel,
    fixture_company: CompanyModel,
    fixture_member: CompanyMemberModel,
    auth_headers: dict[str, str],
):
    response = await client.get(f"{BASE_COMPANY_URL}/my", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == fixture_company.id
    assert data["name"] == fixture_company.name


@pytest.mark.asyncio
async def test_update_my_company(
    client: AsyncClient,
    fixture_user: UserModel,
    fixture_company: CompanyModel,
    fixture_member: CompanyMemberModel,
    auth_headers: dict[str, str],
):
    new_data = {"name": "Updated Corp LLC"}
    response = await client.patch(
        f"{BASE_COMPANY_URL}/my", headers=auth_headers, json=new_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Corp LLC"


@pytest.mark.asyncio
async def test_get_my_company_members(
    client: AsyncClient,
    fixture_user: UserModel,
    fixture_company: CompanyModel,
    fixture_member: CompanyMemberModel,
    auth_headers: dict[str, str],
):
    response = await client.get(f"{BASE_COMPANY_URL}/members", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_my_company_member(
    client: AsyncClient,
    fixture_user: UserModel,
    fixture_company: CompanyModel,
    fixture_member: CompanyMemberModel,
    auth_headers: dict[str, str],
):
    response = await client.get(
        f"{BASE_COMPANY_URL}/members/{fixture_user.id}", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == fixture_user.id


@pytest.mark.asyncio
async def test_change_member_role_success(
    client: AsyncClient,
    fixture_user: UserModel,
    fixture_company: CompanyModel,
    fixture_member: CompanyMemberModel,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    employee = UserModel(
        email="emp@example.com",
        hashed_password="hash",
        first_name="Bob",
        last_name="Marley",
        is_active=True,
    )
    db_session.add(employee)
    await db_session.flush()

    emp_member = CompanyMemberModel(
        company_id=fixture_company.id,
        user_id=employee.id,
        role=RoleEnum.DISPATCHER,
        is_active=True,
    )
    db_session.add(emp_member)
    await db_session.commit()

    payload = {"role": RoleEnum.DRIVER.value}
    response = await client.patch(
        f"{BASE_COMPANY_URL}/members/{employee.id}/role",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_change_own_role_forbidden(
    client: AsyncClient,
    fixture_user: UserModel,
    fixture_company: CompanyModel,
    fixture_member: CompanyMemberModel,
    auth_headers: dict[str, str],
):
    payload = {"role": RoleEnum.DISPATCHER.value}
    response = await client.patch(
        f"{BASE_COMPANY_URL}/members/{fixture_user.id}/role",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Cannot change own role"


@pytest.mark.asyncio
async def test_delete_member_from_company(
    client: AsyncClient,
    fixture_user: UserModel,
    fixture_company: CompanyModel,
    fixture_member: CompanyMemberModel,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    employee = UserModel(
        email="emp_del@example.com",
        hashed_password="hash",
        first_name="Bob",
        last_name="Marley",
        is_active=True,
    )
    db_session.add(employee)
    await db_session.flush()

    emp_member = CompanyMemberModel(
        company_id=fixture_company.id,
        user_id=employee.id,
        role=RoleEnum.DISPATCHER,
        is_active=True,
    )
    db_session.add(emp_member)
    await db_session.commit()

    response = await client.delete(
        f"{BASE_COMPANY_URL}/members/{employee.id}", headers=auth_headers
    )
    assert response.status_code == 200
    await db_session.refresh(emp_member)
    assert emp_member.is_active is False


@pytest.mark.asyncio
async def test_send_invite_success(
    client: AsyncClient,
    fixture_user: UserModel,
    fixture_company: CompanyModel,
    fixture_member: CompanyMemberModel,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    payload = {
        "email": "newinvitee@example.com",
        "role": RoleEnum.DISPATCHER.value,
    }
    response = await client.post(
        f"{BASE_COMPANY_URL}/invite", json=payload, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["role"] == payload["role"]
    assert "token" in data


@pytest.mark.asyncio
async def test_accept_invite_success(
    client: AsyncClient,
    fixture_company: CompanyModel,
    db_session: AsyncSession,
):
    invite_token = str(uuid.uuid4())
    invite = CompanyInviteModel(
        company_id=fixture_company.id,
        email="accepted_user@example.com",
        role=RoleEnum.VIEWER,
        token=invite_token,
        is_accepted=False,
    )
    db_session.add(invite)
    await db_session.commit()

    payload = {
        "token": invite_token,
        "password": "SecurePassword123!",
        "first_name": "John",
        "last_name": "Doe",
    }
    response = await client.post(f"{BASE_COMPANY_URL}/accept_invite", json=payload)
    assert response.status_code == 200
    await db_session.refresh(invite)
    assert invite.is_accepted is True


@pytest.mark.asyncio
async def test_accept_invalid_invite_fails(client: AsyncClient):
    payload = {
        "token": "fake-non-existent-token",
        "password": "SecurePassword123!",
        "first_name": "John",
        "last_name": "Doe",
    }
    response = await client.post(f"{BASE_COMPANY_URL}/accept_invite", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired invitation token"


@pytest.mark.asyncio
async def test_get_my_company_cache(
    client: AsyncClient,
    auth_headers: dict,
    fixture_company: CompanyModel,
    fixture_redis_client: aioredis.Redis,
):
    cache_key = f"company:{fixture_company.id}"

    assert await fixture_redis_client.get(cache_key) is None

    response = await client.get(f"{BASE_COMPANY_URL}/my", headers=auth_headers)
    assert response.status_code == 200
    cached_raw = await fixture_redis_client.get(cache_key)
    assert cached_raw is not None
    cached_data = json.loads(cached_raw)
    assert cached_data["name"] == fixture_company.name


@pytest.mark.asyncio
async def test_update_company_invalidates_cache(
    client: AsyncClient,
    auth_headers: dict,
    fixture_company: CompanyModel,
    fixture_redis_client: aioredis.Redis,
):
    cache_key = f"company:{fixture_company.id}"

    await client.get(f"{BASE_COMPANY_URL}/my", headers=auth_headers)
    assert await fixture_redis_client.get(cache_key) is not None
    patch_response = await client.patch(
        f"{BASE_COMPANY_URL}/my",
        json={"name": "New Awesome Company Name"},
        headers=auth_headers,
    )
    assert patch_response.status_code == 200

    assert await fixture_redis_client.get(cache_key) is None


@pytest.mark.asyncio
async def test_members_list_cache(
    client: AsyncClient,
    auth_headers: dict,
    fixture_company: CompanyModel,
    fixture_user: UserModel,
    fixture_redis_client: aioredis.Redis,
):
    cache_key = f"company:{fixture_company.id}:members"
    assert await fixture_redis_client.get(cache_key) is None

    members_res = await client.get(f"{BASE_COMPANY_URL}/members", headers=auth_headers)
    assert members_res.status_code == 200

    cached_members = await fixture_redis_client.get(cache_key)
    assert cached_members is not None


@pytest.mark.asyncio
async def test_members_one_cache(
    client: AsyncClient,
    auth_headers: dict,
    fixture_company: CompanyModel,
    fixture_user: UserModel,
    fixture_redis_client: aioredis.Redis,
):
    single_member_cache_key = f"company:{fixture_company.id}:member:{fixture_user.id}"
    res_single = await client.get(
        f"{BASE_COMPANY_URL}/members/{fixture_user.id}", headers=auth_headers
    )
    assert res_single.status_code == 200

    cached_single_raw = await fixture_redis_client.get(single_member_cache_key)
    assert cached_single_raw is not None
    assert json.loads(cached_single_raw)["email"] == fixture_user.email
