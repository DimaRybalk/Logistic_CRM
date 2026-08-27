from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models import RoleEnum


class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128)


class User(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UpdateUser(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)


class LoginUser(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(...)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: str
    company_id: int
    role: RoleEnum
    exp: int


class ChangePassword(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=6, max_length=128)


# _____________________________________________________________________________


class CompanyBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)


class CompanyCreate(CompanyBase):
    pass


class Company(CompanyBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UpdateCompany(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)


class CompanyRegister(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    first_name: Optional[str] = None
    last_name: Optional[str] = None


# _________________________________________________________


class CompanyMemberBase(BaseModel):
    role: RoleEnum = RoleEnum.VIEWER


class CompanyMemberCreate(CompanyMemberBase):
    user_id: int
    company_id: int


class CompanyMember(CompanyMemberBase):
    id: int
    user_id: int
    company_id: int
    is_active: bool
    user: Optional[User] = None

    model_config = ConfigDict(from_attributes=True)


class UpdateCompanyMember(BaseModel):
    role: RoleEnum | None = None
    is_active: bool | None = None


class UpdateMemberRole(BaseModel):
    role: RoleEnum


# ____________________________________________________________


class CompanyInviteBase(BaseModel):
    role: RoleEnum = RoleEnum.VIEWER
    email: EmailStr


class CreateCompanyInvite(CompanyInviteBase):
    pass


class CompanyInvite(CompanyInviteBase):
    id: int
    company_id: int
    token: str
    is_accepted: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InviteAccept(BaseModel):
    token: str
    password: str = Field(..., min_length=6, max_length=128)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
