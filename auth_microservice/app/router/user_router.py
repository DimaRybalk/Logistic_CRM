import json

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import CompanyMemberModel, UserModel
from app.schemas import User, UpdateUser, ChangePassword
from app.security import hash_password, verify_password

import redis.asyncio as aioredis
from app.redis_client import get_redis

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=User)
async def get_me(
    current_user: tuple = Depends(get_current_user),
    redis: aioredis.Redis = Depends(get_redis),
):
    user, _, _ = current_user
    cache_key = f"user:{user.id}"

    cached_user = await redis.get(cache_key)
    if cached_user:
        return json.loads(cached_user)

    user_dict = User.model_validate(user).model_dump(mode="json")

    await redis.set(cache_key, json.dumps(user_dict), ex=600)
    return user


@router.patch("/me", response_model=User)
async def change_my_data(
    new_data: UpdateUser,
    user_data: tuple = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    user, company_id, _ = user_data
    update_data = new_data.model_dump(exclude_unset=True)

    if "email" in update_data and update_data["email"] != user.email:
        query = select(UserModel).where(UserModel.email == update_data["email"])
        result = await db.execute(query)
        email_check = result.scalar_one_or_none()
        if email_check:
            raise HTTPException(
                status_code=400, detail="User with this email already exists"
            )

    for key, value in update_data.items():
        setattr(user, key, value)

    await db.commit()
    await db.refresh(user)

    await redis.delete(f"user:{user.id}")
    await redis.delete(f"company:{company_id}:members")

    return user


@router.delete("/me")
async def delete_my_account(
    current_user: tuple = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    user, company_id, _ = current_user
    user.is_active = False
    query = select(CompanyMemberModel).where(
        CompanyMemberModel.user_id == user.id,
        CompanyMemberModel.company_id == company_id,
    )
    result = await db.execute(query)
    member = result.scalar_one_or_none()

    if member:
        member.is_active = False

    await db.commit()
    await redis.delete(f"user:{user.id}")
    await redis.delete(f"company:{company_id}:members")
    return {"message": "Account successfully deleted"}


@router.patch("/me/change_password")
async def change_my_password(
    change_password: ChangePassword,
    current_user: tuple = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user, _, _ = current_user

    if not verify_password(change_password.old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid password")

    if verify_password(change_password.new_password, user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail="New password must be different from the old password",
        )

    user.hashed_password = hash_password(change_password.new_password)

    await db.commit()

    return {"message": "Password successfully changed"}


@router.post("/logout")
async def logout(
    authorization: str = Header(...),
    current_user: tuple = Depends(get_current_user),
    redis: aioredis.Redis = Depends(get_redis),
):
    user, _, _ = current_user
    token = authorization.split(" ")[1] if " " in authorization else authorization

    await redis.set(f"blacklist:{token}", "revoked", ex=3600)
    await redis.delete(f"user:{user.id}")

    return {
        "message": "Successfully logged out. Please remove your access token on the client."
    }
