from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid

class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        return str(v)

# User Models
class UserRole(str):
    SUPER_ADMIN = 'super_admin'
    ADMIN = 'admin'
    USER = 'user'

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = UserRole.USER

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    role: str
    credits: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = None
    credits: Optional[int] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None

class CreditRequest(BaseModel):
    amount: int

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    credits: Optional[int] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None

# Token Models
class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    user: User

class TokenData(BaseModel):
    email: Optional[str] = None

# Password Reset Models
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

# Profile Models
class ProfileSearchRequest(BaseModel):
    name: Optional[str] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    keywords: Optional[str] = None
    experience_years_min: Optional[int] = None
    experience_years_max: Optional[int] = None
    company_size: Optional[str] = None
    revenue_range: Optional[str] = None
    skills: Optional[str] = None
    page: int = 1
    page_size: int = 20

class ProfileCreateRequest(BaseModel):
    first_name: str
    last_name: str
    job_title: str
    industry: Optional[str] = None
    sub_industry: Optional[str] = None
    keywords: Optional[List[str]] = []
    seo_description: Optional[str] = None
    company_name: str
    company_domain: str  # Required for company lookup/creation
    profile_linkedin_url: Optional[str] = None
    company_linkedin_url: Optional[str] = None
    emails: List[str] = []
    phones: List[str] = []
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

class ProfileUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    job_title: Optional[str] = None
    industry: Optional[str] = None
    sub_industry: Optional[str] = None
    keywords: Optional[List[str]] = None
    seo_description: Optional[str] = None
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    profile_linkedin_url: Optional[str] = None
    company_linkedin_url: Optional[str] = None
    emails: Optional[List[str]] = None
    phones: Optional[List[str]] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

class ProfileCreate(BaseModel):
    first_name: str
    last_name: str
    job_title: str
    industry: Optional[str] = None
    sub_industry: Optional[str] = None
    keywords: Optional[List[str]] = []
    seo_description: Optional[str] = None
    company_name: str
    company_domain: str  # Required for company lookup/creation
    profile_linkedin_url: Optional[str] = None
    company_linkedin_url: Optional[str] = None
    emails: List[str] = []
    phones: List[str] = []
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

class Profile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    first_name: str
    last_name: str
    job_title: str
    industry: Optional[str] = None
    sub_industry: Optional[str] = None
    keywords: List[str] = []
    seo_description: Optional[str] = None
    company_id: str  # Foreign key to Company - hierarchical relationship
    company_name: str  # Denormalized for quick access
    company_domain: str  # Denormalized for quick access
    profile_linkedin_url: Optional[str] = None
    company_linkedin_url: Optional[str] = None
    emails: List[str] = []
    phones: List[str] = []
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Company Models
class CompanySearchRequest(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    revenue: Optional[str] = None
    employee_size: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    page: int = 1
    page_size: int = 20

class CompanyCreateRequest(BaseModel):
    name: str
    domain: str  # Required - unique identifier for company
    linkedin_url: Optional[str] = None
    revenue: Optional[str] = None
    employee_size: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

class CompanyUpdateRequest(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    linkedin_url: Optional[str] = None
    revenue: Optional[str] = None
    employee_size: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

class CompanyCreate(BaseModel):
    name: str
    domain: str  # Required - unique identifier for company
    linkedin_url: Optional[str] = None
    revenue: Optional[str] = None
    employee_size: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

class Company(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    domain: str  # Required - unique identifier for company
    linkedin_url: Optional[str] = None
    revenue: Optional[str] = None
    employee_size: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Filter Models
class ProfileFilter(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    job_title: Optional[str] = None
    industry: Optional[str] = None
    sub_industry: Optional[str] = None
    company_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    keywords: Optional[List[str]] = None
    experience_years_min: Optional[int] = None
    experience_years_max: Optional[int] = None
    company_size: Optional[str] = None
    revenue_range: Optional[str] = None
    skills: Optional[str] = None
    page: int = 1
    page_size: int = 20

class CompanyFilter(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    revenue: Optional[str] = None
    employee_size: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    page: int = 1
    page_size: int = 20

# Reveal Request Models
class RevealRequest(BaseModel):
    profile_id: str
    reveal_type: str  # 'email' or 'phone'

# Plan Models
class PlanCreateRequest(BaseModel):
    name: str
    credits: int
    price: float
    duration_days: int
    features: List[str] = []

class PlanUpdateRequest(BaseModel):
    name: Optional[str] = None
    credits: Optional[int] = None
    price: Optional[float] = None
    duration_days: Optional[int] = None
    features: Optional[List[str]] = None
    is_active: Optional[bool] = None

class PlanCreate(BaseModel):
    name: str
    credits: int
    price: float
    duration_days: int
    features: List[str] = []

class Plan(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    credits: int
    price: float
    duration_days: int
    features: List[str] = []
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Bulk Upload Models
class BulkUploadRequest(BaseModel):
    field_mapping: Dict[str, str]  # CSV column -> model field
    validations: Optional[Dict[str, Any]] = {}

class BulkUploadStatus(BaseModel):
    task_id: str
    status: str
    total_rows: int = 0
    processed_rows: int = 0
    success_count: int = 0
    error_count: int = 0
    errors: List[Dict[str, Any]] = []

# Revealed Contact Models (for unique reveal tracking)
class RevealedContact(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    profile_id: str
    reveal_type: str  # 'email' or 'phone'
    revealed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Credit Transaction Models
class CreditTransaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    amount: int  # negative for deduction, positive for addition
    transaction_type: str  # 'reveal_email', 'reveal_phone', 'purchase', 'admin_adjustment'
    reference_id: Optional[str] = None  # profile_id for reveals
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Profile/Company Update Models
class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    job_title: Optional[str] = None
    industry: Optional[str] = None
    sub_industry: Optional[str] = None
    keywords: Optional[List[str]] = None
    seo_description: Optional[str] = None
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    profile_linkedin_url: Optional[str] = None
    company_linkedin_url: Optional[str] = None
    emails: Optional[List[str]] = None
    phones: Optional[List[str]] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    linkedin_url: Optional[str] = None
    revenue: Optional[str] = None
    employee_size: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

class PlanUpdate(BaseModel):
    name: Optional[str] = None
    credits: Optional[int] = None
    price: Optional[float] = None
    duration_days: Optional[int] = None
    features: Optional[List[str]] = None
    is_active: Optional[bool] = None
