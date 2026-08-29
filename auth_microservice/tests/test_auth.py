import pytest
from httpx import AsyncClient
from app.models import CompanyMemberModel, RoleEnum, UserModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.security import (
    create_password_reset_token,
    create_refresh_token,
    verify_password,
)

REGISTRATION_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
REFRESH_URL = "/api/v1/auth/refresh"
FORGOT_PASSWORD_URL = "/api/v1/auth/forgot_password"
RESET_PASSWORD_URL = "/api/v1/auth/reset_password"


@pytest.mark.asyncio
async def test_company_and_owner_registration(
    client: AsyncClient, db_session: AsyncSession
):
    payload = {
        "email": "newowner@example.com",
        "password": "securepassword123",
        "first_name": "Alice",
        "last_name": "Smith",
        "company_name": "New Horizons LLC",
    }

    response = await client.post(REGISTRATION_URL, json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert "id" in data

    query = select(UserModel).where(UserModel.email == payload["email"])
    result = await db_session.execute(query)
    user = result.scalar_one_or_none()

    assert user is not None

    member_query = select(CompanyMemberModel).where(
        CompanyMemberModel.user_id == user.id, CompanyMemberModel.role == RoleEnum.OWNER
    )
    member_result = await db_session.execute(member_query)
    member = member_result.scalar_one_or_none()

    assert member is not None


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, fixture_user: UserModel):
    payload = {
        "email": fixture_user.email,
        "password": "securepassword123",
        "first_name": "Alice",
        "last_name": "Smith",
        "company_name": "New Horizons LLC",
    }

    response = await client.post(REGISTRATION_URL, json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "User with this email already exists"


@pytest.mark.asyncio
async def test_user_login(
    client: AsyncClient, fixture_user: UserModel, fixture_member: CompanyMemberModel
):
    payload = {
        "email": fixture_user.email,
        "password": "password123",
    }

    response = await client.post(LOGIN_URL, json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(
    client: AsyncClient, fixture_user: UserModel, fixture_member: CompanyMemberModel
):
    payload = {
        "email": fixture_user.email,
        "password": "pass",
    }
    response = await client.post(LOGIN_URL, json=payload)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_login_user_not_found(client: AsyncClient):
    payload = {
        "email": "nonexistent@example.com",
        "password": "password123",
    }
    response = await client.post(LOGIN_URL, json=payload)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_refresh_token_success(
    client: AsyncClient, fixture_user: UserModel, fixture_member: CompanyMemberModel
):
    refresh_token = create_refresh_token(
        data={"sub": str(fixture_user.id), "email": fixture_user.email}
    )

    response = await client.post(REFRESH_URL, json={"refresh_token": refresh_token})

    assert response.status_code == 200
    data = response.json()
    assert "refresh_token" in data
    assert "access_token" in data


@pytest.mark.asyncio
async def test_refresh_token_wrong(client: AsyncClient):
    response = await client.post(REFRESH_URL, json={"refresh_token": "232434324"})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_forgot_password(client: AsyncClient, fixture_user: UserModel):
    response = await client.post(
        FORGOT_PASSWORD_URL, json={"email": fixture_user.email}
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_reset_password(
    client: AsyncClient, fixture_user: UserModel, db_session: AsyncSession
):
    reset_token = create_password_reset_token(email=fixture_user.email)
    new_password = "BrandNewPassword2026!"

    payload = {"token": reset_token, "new_password": new_password}

    response = await client.post(RESET_PASSWORD_URL, json=payload)

    assert response.status_code == 200
    await db_session.refresh(fixture_user)
    assert verify_password(new_password, fixture_user.hashed_password)


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client: AsyncClient):
    payload = {
        "token": "fake-or-expired-reset-token",
        "new_password": "BrandNewPassword2026!",
    }
    response = await client.post(RESET_PASSWORD_URL, json=payload)
    assert response.status_code == 400
