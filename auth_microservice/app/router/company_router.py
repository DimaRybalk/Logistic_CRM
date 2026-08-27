import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models import (
    CompanyModel,
    RoleEnum,
    UserModel,
    CompanyMemberModel,
    CompanyInviteModel,
)
from app.schemas import (
    Company,
    UpdateCompany,
    User,
    UpdateMemberRole,
    CompanyInvite,
    CreateCompanyInvite,
    InviteAccept,
)
from app.security import hash_password

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.get("/my", response_class=Company)
async def get_my_company(
    user_data: tuple = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _, company_id, _ = user_data

    query = select(CompanyModel).where(
        CompanyModel.id == company_id, CompanyModel.is_active == True
    )
    result = await db.execute(query)
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found or inactive",
        )

    return company


@router.patch("/my", response_model=Company)
async def update_my_company(
    new_data: UpdateCompany,
    user_data: tuple = Depends(require_role(RoleEnum.OWNER)),
    db: AsyncSession = Depends(get_db),
):
    user, company_id, _ = user_data
    updated_data = new_data.model_dump(exclude_unset=True)

    query = select(CompanyModel).where(
        CompanyModel.id == company_id, CompanyModel.is_active == True
    )
    result = await db.execute(query)
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found or inactive",
        )

    if "name" in updated_data and updated_data["name"] != company.name:
        name_query = select(CompanyModel).where(
            CompanyModel.name == updated_data["name"]
        )
        result = await db.execute(name_query)
        name_check = result.scalar_one_or_none()

        if name_check:
            raise HTTPException(
                status_code=400,
                detail="Company with this name already exists",
            )

        for key, value in updated_data.items():
            setattr(user, key, value)

        await db.commit()
        await db.refresh(company)

        return company


@router.get("/members", response_model=list[User])
async def get_company_members(
    user_data: tuple = Depends(require_role(RoleEnum.OWNER)),
    db: AsyncSession = Depends(get_db),
):
    _, company_id, _ = user_data
    query = (
        select(UserModel)
        .join(CompanyMemberModel, CompanyMemberModel.user_id == UserModel.id)
        .where(
            CompanyMemberModel.company_id == company_id,
            CompanyMemberModel.is_active == True,
        )
    )
    result = await db.execute(query)
    members = result.scalars().all()

    return members


@router.get("/members/{member_id}", response_model=User)
async def get_company_member(
    member_id: int,
    user_data: tuple = Depends(require_role(RoleEnum.OWNER)),
    db: AsyncSession = Depends(get_db),
):
    _, company_id, _ = user_data
    query = (
        select(UserModel)
        .join(CompanyMemberModel, CompanyMemberModel.user_id == UserModel.id)
        .where(
            CompanyMemberModel.company_id == company_id,
            CompanyMemberModel.is_active == True,
            CompanyMemberModel.user_id == member_id,
        )
    )
    result = await db.execute(query)
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="User not found")

    return member


@router.patch("/members/{member_id}/role")
async def change_member_role(
    member_id: int,
    new_role: UpdateMemberRole,
    user_data: tuple = Depends(require_role(RoleEnum.OWNER)),
    db: AsyncSession = Depends(get_db),
):
    user, company_id, _ = user_data
    update_role = new_role.model_dump(exclude_unset=True)

    if member_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot change own role")

    query = select(CompanyMemberModel).where(
        CompanyMemberModel.user_id == member_id,
        CompanyMemberModel.company_id == company_id,
        CompanyMemberModel.is_active == True,
    )
    result = await db.execute(query)
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=404,
            detail="Member not found in this company",
        )

    for key, value in update_role.items():
        setattr(member, key, value)

    await db.commit()
    await db.refresh(member)

    return {
        "message": "Role updated successfully",
        "member_id": member.user_id,
        "new_role": member.role,
    }


@router.delete("/members/{member_id}")
async def delete_member_from_company(
    member_id: int,
    user_data: tuple = Depends(require_role(RoleEnum.OWNER)),
    db: AsyncSession = Depends(get_db),
):
    user, company_id, _ = user_data
    if member_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    query = select(CompanyMemberModel).where(
        CompanyMemberModel.user_id == member_id,
        CompanyMemberModel.company_id == company_id,
        CompanyMemberModel.is_active == True,
    )
    result = await db.execute(query)
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=404,
            detail="Member not found in this company",
        )

    member.is_active = False
    await db.commit()

    return {"message": "Member successfully deleted", "member_id": member.user_id}


@router.post("/invite", response_model=CompanyInvite)
async def send_invite(
    data: CreateCompanyInvite,
    user_data: tuple = Depends(require_role(RoleEnum.OWNER)),
    db: AsyncSession = Depends(get_db),
):
    user, company_id, _ = user_data

    if data.email == user.email:
        raise HTTPException(status_code=400, detail="Cannot send invite for yourself")

    member_query = (
        select(UserModel)
        .join(CompanyMemberModel, CompanyMemberModel.user_id == UserModel.id)
        .where(
            UserModel.email == data.email,
            CompanyMemberModel.company_id == company_id,
            CompanyMemberModel.is_active == True,
        )
    )
    member_result = await db.execute(member_query)
    member = member_result.scalar_one_or_none()

    if member:
        raise HTTPException(
            status_code=400,
            detail="User is already a member of this company",
        )

    invite_query = select(CompanyInviteModel).where(
        CompanyInviteModel.email == data.email,
        CompanyInviteModel.company_id == company_id,
        CompanyInviteModel.is_accepted == False,
    )
    invite_result = await db.execute(invite_query)
    invite = invite_result.scalar_one_or_none()

    if invite:
        raise HTTPException(
            status_code=400,
            detail="Invite for this email is already pending",
        )

    new_invite = CompanyInviteModel(
        company_id=company_id,
        email=data.email,
        role=data.role,
        token=str(uuid.uuid4()),
    )
    db.add(new_invite)
    await db.commit()
    await db.refresh(new_invite)

    print(f"Invite link: https://yourapp.com/accept-invite?token={new_invite.token}")

    return new_invite


@router.post("/accept_invite")
async def accept_invite(data: InviteAccept, db: AsyncSession = Depends(get_db)):
    query = select(CompanyInviteModel).where(
        CompanyInviteModel.token == data.token, CompanyInviteModel.is_accepted == False
    )
    result = await db.execute(query)
    invite = result.scalar_one_or_none()

    if not invite:
        raise HTTPException(
            status_code=400, detail="Invalid or expired invitation token"
        )

    user_query = select(UserModel).where(UserModel.email == invite.email)
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()

    if not user:
        user = UserModel(
            email=invite.email,
            hashed_password=hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
        )
        db.add(user)
        await db.flush()

    new_member = CompanyMemberModel(
        company_id=invite.company_id, user_id=user.id, role=invite.role
    )
    db.add(new_member)

    invite.is_accepted = True
    await db.commit()

    return {"message": "Invite successfully accepted"}
