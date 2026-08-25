from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models import CompanyMemberModel, RoleEnum, UserModel
from app.schemas import User, UpdateUser


router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=User)
async def get_me(current_user: tuple = Depends(get_current_user)):
    user, company_id, role = current_user
    return user

@router.get("/members",response_model=list[User])
async def get_company_members(user_data: tuple = Depends(require_role(RoleEnum.OWNER)), db: AsyncSession = Depends(get_db)):
    user, company_id, role = user_data
    query = select(UserModel).join(CompanyMemberModel, CompanyMemberModel.user_id == UserModel.id).where(CompanyMemberModel.company_id == company_id, CompanyMemberModel.is_active == True)
    result = await db.execute(query)
    members = result.scalars().all()

    return members

@router.get("/members/{member_id}",response_model=User)
async def get_company_member(member_id: int,user_data: tuple = Depends(require_role(RoleEnum.OWNER)), db: AsyncSession = Depends(get_db)):
    user, company_id, role = user_data
    query = select(UserModel).join(CompanyMemberModel, CompanyMemberModel.user_id == UserModel.id).where(CompanyMemberModel.company_id == company_id, CompanyMemberModel.is_active == True, CompanyMemberModel.user_id == member_id)
    result = await db.execute(query)
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return member

@router.patch("/me", response_model=User)
async def change_my_data(new_data: UpdateUser,user_data: tuple = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user, company_id, role = user_data
    update_data = new_data.model_dump(exclude_unset=True)

    if "email" in update_data and update_data["email"] != user.email:
        query = select(UserModel).where(UserModel.email == update_data["email"])
        result = await db.execute(query)
        email_check = result.scalar_one_or_none()
        if email_check:
            raise HTTPException(status_code=400,
            detail="User with this email already exists")
        
    for key,value in update_data.items():
        setattr(user,key,value)

    await db.commit()
    await db.refresh(user)

    return user    