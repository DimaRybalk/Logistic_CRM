import os
import uuid
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
import redis.asyncio as aioredis
from app.database import Base, get_db
from app.main import app
from app.models import (
    CompanyInviteModel,
    CompanyMemberModel,
    CompanyModel,
    RoleEnum,
    UserModel,
)
from app.security import create_access_token, hash_password
from app.redis_client import get_redis

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
REDIS_NAME = os.getenv("REDIS_NAME")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_HOST = os.getenv("REDIS_HOST")


engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession, fixture_redis_client: aioredis.Redis):
    async def override_get_db():
        yield db_session

    async def override_get_redis():
        return fixture_redis_client

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def fixture_user(db_session: AsyncSession) -> UserModel:
    user = UserModel(
        email="testowner@example.com",
        hashed_password=hash_password("password123"),
        first_name="John",
        last_name="Doe",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def fixture_company(db_session: AsyncSession) -> CompanyModel:
    company = CompanyModel(
        name="Test company",
        is_active=True,
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)
    return company


@pytest_asyncio.fixture
async def fixture_member(
    db_session: AsyncSession,
    fixture_user: UserModel,
    fixture_company: CompanyModel,
) -> CompanyMemberModel:
    member = CompanyMemberModel(
        user_id=fixture_user.id,
        company_id=fixture_company.id,
        role=RoleEnum.OWNER,
        is_active=True,
    )
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)
    return member


@pytest_asyncio.fixture
async def auth_headers(
    fixture_user: UserModel, fixture_member: CompanyMemberModel
) -> dict[str, str]:
    token_data = {
        "sub": str(fixture_user.id),
        "email": fixture_user.email,
        "company_id": fixture_member.company_id,
        "role": fixture_member.role.value,
    }
    token = create_access_token(data=token_data)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def fixture_invite(
    db_session: AsyncSession, fixture_company: CompanyModel
) -> CompanyInviteModel:
    invite = CompanyInviteModel(
        company_id=fixture_company.id,
        email="emailforinvite@test.com",
        token=str(uuid.uuid4()),
        role=RoleEnum.VIEWER,
        is_accepted=False,
    )
    db_session.add(invite)
    await db_session.commit()
    await db_session.refresh(invite)
    return invite


@pytest_asyncio.fixture(scope="function")
async def fixture_redis_client():
    if not all([REDIS_NAME, REDIS_PORT, REDIS_HOST]):
        raise RuntimeError(
            "Missing required Redis environment variables: REDIS_NAME, REDIS_PORT,"
            " REDIS_HOST"
        )

    client = aioredis.from_url(
        f"{REDIS_NAME}://{REDIS_HOST}:{REDIS_PORT}/0", decode_responses=True
    )

    await client.flushdb()

    yield client

    await client.flushdb()
    await client.aclose()
