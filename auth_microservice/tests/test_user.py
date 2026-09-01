import json

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis
from app.models import CompanyMemberModel, UserModel
from app.security import verify_password

USERS_ME_URL = "/api/v1/users/me"
CHANGE_PASSWORD_URL = "/api/v1/users/me/change_password"
LOGOUT_URL = "/api/v1/users/logout"


@pytest.mark.asyncio
async def test_get_my_account(
    client: AsyncClient,
    fixture_user: UserModel,
    fixture_member: CompanyMemberModel,
    auth_headers: dict[str, str],
):
    response = await client.get(USERS_ME_URL, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == fixture_user.id
    assert data["email"] == fixture_user.email
    assert data["first_name"] == fixture_user.first_name


@pytest.mark.asyncio
async def test_get_my_account_unauthorized(client: AsyncClient):
    response = await client.get(USERS_ME_URL)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_change_my_data_success(
    client: AsyncClient,
    fixture_user: UserModel,
    fixture_member: CompanyMemberModel,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    new_data = {"first_name": "UpdatedName", "last_name": "UpdatedLastName"}

    response = await client.patch(USERS_ME_URL, json=new_data, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "UpdatedName"
    assert data["last_name"] == "UpdatedLastName"

    await db_session.refresh(fixture_user)
    assert fixture_user.first_name == "UpdatedName"
    assert fixture_user.last_name == "UpdatedLastName"


@pytest.mark.asyncio
async def test_change_email_to_existing_fails(
    client: AsyncClient,
    fixture_user: UserModel,
    fixture_member: CompanyMemberModel,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    other_user = UserModel(
        email="other@example.com",
        hashed_password="hashedpassword123",
        first_name="Bob",
        last_name="Marley",
        is_active=True,
    )
    db_session.add(other_user)
    await db_session.commit()

    response = await client.patch(
        USERS_ME_URL, json={"email": "other@example.com"}, headers=auth_headers
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "User with this email already exists"


@pytest.mark.asyncio
async def test_delete_my_account(
    client: AsyncClient,
    fixture_user: UserModel,
    fixture_member: CompanyMemberModel,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    response = await client.delete(USERS_ME_URL, headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["message"] == "Account successfully deleted"

    await db_session.refresh(fixture_user)
    await db_session.refresh(fixture_member)

    assert fixture_user.is_active is False
    assert fixture_member.is_active is False


@pytest.mark.asyncio
async def test_change_my_password_success(
    client: AsyncClient,
    fixture_user: UserModel,
    fixture_member: CompanyMemberModel,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    payload = {
        "old_password": "password123",
        "new_password": "BrandNewPassword2026!",
    }

    response = await client.patch(
        CHANGE_PASSWORD_URL, json=payload, headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Password successfully changed"

    await db_session.refresh(fixture_user)
    assert verify_password("BrandNewPassword2026!", fixture_user.hashed_password)


@pytest.mark.asyncio
async def test_change_my_password_invalid_old_password(
    client: AsyncClient,
    fixture_user: UserModel,
    fixture_member: CompanyMemberModel,
    auth_headers: dict[str, str],
):
    payload = {
        "old_password": "wrongpassword",
        "new_password": "BrandNewPassword2026!",
    }

    response = await client.patch(
        CHANGE_PASSWORD_URL, json=payload, headers=auth_headers
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid password"


@pytest.mark.asyncio
async def test_change_my_password_same_as_old(
    client: AsyncClient,
    fixture_user: UserModel,
    fixture_member: CompanyMemberModel,
    auth_headers: dict[str, str],
):
    payload = {
        "old_password": "password123",
        "new_password": "password123",
    }

    response = await client.patch(
        CHANGE_PASSWORD_URL, json=payload, headers=auth_headers
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "New password must be different from the old password"
    )


@pytest.mark.asyncio
async def test_logout(
    client: AsyncClient,
    fixture_user: UserModel,
    fixture_member: CompanyMemberModel,
    auth_headers: dict[str, str],
):
    response = await client.post(LOGOUT_URL, headers=auth_headers)

    assert response.status_code == 200
    assert (
        response.json()["message"]
        == "Successfully logged out. Please remove your access token on the client."
    )


@pytest.mark.asyncio
async def test_get_me_cache(
    client: AsyncClient,
    auth_headers: dict,
    fixture_user: UserModel,
    fixture_redis_client: aioredis.Redis,
):
    cache_key = f"user:{fixture_user.id}"

    await fixture_redis_client.delete(cache_key)
    assert await fixture_redis_client.get(cache_key) is None

    response = await client.get(USERS_ME_URL, headers=auth_headers)
    assert response.status_code == 200

    cached_raw = await fixture_redis_client.get(cache_key)
    assert cached_raw is not None
    cached_data = json.loads(cached_raw)
    assert cached_data["email"] == fixture_user.email

    response_cached = await client.get(USERS_ME_URL, headers=auth_headers)

    assert response_cached.status_code == 200
    assert response_cached.json()["email"] == fixture_user.email


@pytest.mark.asyncio
async def test_logout(
    client: AsyncClient,
    auth_headers: dict,
    fixture_user: UserModel,
    fixture_redis_client: aioredis.Redis,
):
    token = auth_headers["Authorization"].split(" ")[1]
    blacklist_key = f"blacklist:{token}"

    logout_response = await client.post(LOGOUT_URL, headers=auth_headers)
    assert logout_response.status_code == 200

    is_revoked = await fixture_redis_client.get(blacklist_key)
    assert is_revoked == "revoked"
