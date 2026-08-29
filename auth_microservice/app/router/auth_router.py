import jwt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import CompanyMemberModel, CompanyModel, RoleEnum, UserModel
from app.schemas import (
    CompanyRegister,
    LoginUser,
    RefreshTokenRequest,
    Token,
    User,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.security import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    create_password_reset_token,
    verify_password_reset_token,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=User, status_code=201)
async def register_company_with_owner(
    data: CompanyRegister, db: AsyncSession = Depends(get_db)
):
    company_query = select(CompanyModel).where(CompanyModel.name == data.company_name)
    result = await db.execute(company_query)
    companies = result.scalar_one_or_none()
    if not companies:
        new_company = CompanyModel(name=data.company_name)
        db.add(new_company)
        await db.flush()
    else:
        raise HTTPException(
            status_code=400, detail="Company with this name already exists"
        )

    user_query = select(UserModel).where(UserModel.email == data.email)
    user_result = await db.execute(user_query)
    users = user_result.scalar_one_or_none()
    if not users:
        new_user = UserModel(
            email=data.email,
            hashed_password=hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
        )
        db.add(new_user)
        await db.flush()
    else:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists",
        )

    new_member = CompanyMemberModel(
        company_id=new_company.id, user_id=new_user.id, role=RoleEnum.OWNER
    )

    db.add(new_member)

    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
async def login_user(data: LoginUser, db: AsyncSession = Depends(get_db)):
    query = select(UserModel).where(UserModel.email == data.email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    member_query = select(CompanyMemberModel).where(
        CompanyMemberModel.user_id == user.id
    )
    member_result = await db.execute(member_query)
    member = member_result.scalar_one_or_none()

    if not member or not member.is_active:
        raise HTTPException(
            status_code=403, detail="User does not belong to any active company"
        )

    token_payload = {
        "sub": str(user.id),
        "company_id": member.company_id,
        "role": member.role.value,
    }

    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=Token)
async def receiving_refresh_token(
    data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)
):
    try:
        payload = jwt.decode(data.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=400,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="User identifier missing in token",
        )

    query = select(UserModel).where(UserModel.id == int(user_id))
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="User not found or inactive",
        )

    member_query = select(CompanyMemberModel).where(
        CompanyMemberModel.user_id == user.id, CompanyMemberModel.is_active == True
    )
    member_result = await db.execute(member_query)
    member = member_result.scalars().first()

    if not member:
        raise HTTPException(
            status_code=403,
            detail="User does not belong to any active company",
        )

    token_payload = {
        "sub": str(user.id),
        "company_id": member.company_id,
        "role": member.role.value,
    }

    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/forgot_password")
async def forgot_password(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    query = select(UserModel).where(
        UserModel.email == data.email, UserModel.is_active == True
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user:
        reset_token = create_password_reset_token(user.email)

        print(f"Reset Link: https://yourapp.com/reset-password?token={reset_token}")

    return {
        "message": "If this email is registered, a password reset link has been sent."
    }


@router.post("/reset_password")
async def reset_password(
    data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
):
    email = verify_password_reset_token(data.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    query = select(UserModel).where(
        UserModel.email == email, UserModel.is_active == True
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(data.new_password)
    await db.commit()

    return {"message": "Password has been successfully reset"}
