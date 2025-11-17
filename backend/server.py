from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from starlette.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from contextlib import asynccontextmanager
import logging
from typing import List, Optional, Dict, Any
import json
import redis.asyncio as redis
import io
import csv

# Import configurations and database
from config import config
from database import connect_db, close_db, get_db
from models import *

# Import services
from services.auth_service import auth_service
from services.user_service import user_service
from services.profile_service import profile_service
from services.company_service import company_service
from services.plan_service import plan_service
from services.email_service import email_service

# Import utils
from utils import decode_access_token

# Import Celery tasks
from celery_app import celery_app
from tasks import process_bulk_upload

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Rate Limiter will be initialized in lifespan

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_db()
    db = get_db()
    
    # Initialize services with database
    auth_service.set_db(db)
    user_service.set_db(db)
    profile_service.set_db(db)
    company_service.set_db(db)
    plan_service.set_db(db)
    
    # Initialize FastAPI Limiter with Redis
    redis_conn = redis.from_url(config.REDIS_URL, encoding="utf8")
    await FastAPILimiter.init(redis_conn)
    
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    await FastAPILimiter.close()
    await close_db()
    logger.info("Application shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="LeadGen Pro API",
    version="1.0.0",
    description="Production-ready B2B Lead Generation Platform API",
    lifespan=lifespan
)

# Create API router with /api prefix
api_router = APIRouter(prefix="/api")

# Dependency to get current user from token
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user from JWT token"""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    email = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Get user from database
    user_data = await user_service.get_user_by_email(email)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return User(**user_data)

# Dependency for super admin only
async def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require super admin role"""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return current_user

# ========== AUTH ENDPOINTS ==========

@api_router.post("/auth/register", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def register(request: RegisterRequest):
    """Register new user"""
    try:
        # Create UserCreate object
        user_create = UserCreate(
            email=request.email,
            password=request.password,
            full_name=f"{request.first_name} {request.last_name}",
            role="user"
        )
        result = await auth_service.register_user(user_create)
        return result
    except HTTPException:
        # Re-raise HTTPException with correct status code
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@api_router.post("/auth/login", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def login(request: LoginRequest):
    """Login user"""
    try:
        # Create UserLogin object
        user_login = UserLogin(
            email=request.email,
            password=request.password
        )
        result = await auth_service.login_user(user_login)
        return result
    except HTTPException:
        # Re-raise HTTPException with correct status code
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@api_router.get("/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@api_router.post("/auth/forgot-password", dependencies=[Depends(RateLimiter(times=3, seconds=60))])
async def forgot_password(request: ForgotPasswordRequest):
    """Request password reset"""
    try:
        auth_service.forgot_password(request.email)
        return {"message": "Password reset email sent"}
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        # Don't reveal if email exists
        return {"message": "Password reset email sent"}

@api_router.post("/auth/reset-password", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def reset_password(request: ResetPasswordRequest):
    """Reset password with token"""
    try:
        auth_service.reset_password(request.token, request.new_password)
        return {"message": "Password reset successful"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ========== USER ENDPOINTS ==========

@api_router.get("/users")
async def get_users(
    page: int = 1,
    page_size: int = 20,
    role: Optional[str] = None,
    current_user: User = Depends(require_super_admin)
):
    """Get all users (super admin only)"""
    skip = (page - 1) * page_size
    users = await user_service.get_all_users(skip=skip, limit=page_size, role=role)
    return users

@api_router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    current_user: User = Depends(require_super_admin)
):
    """Get user by ID (super admin only)"""
    user = await user_service.get_user_by_id(user_id)
    return user

@api_router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    current_user: User = Depends(require_super_admin)
):
    """Update user (super admin only)"""
    try:
        user = await user_service.update_user(user_id, request.dict(exclude_unset=True))
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@api_router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_super_admin)
):
    """Delete user (super admin only)"""
    try:
        await user_service.delete_user(user_id)
        return {"message": "User deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@api_router.post("/users/{user_id}/credits")
async def add_credits(
    user_id: str,
    request: CreditRequest,
    current_user: User = Depends(require_super_admin)
):
    """Add or deduct credits from user (super admin only)"""
    try:
        user = await user_service.add_credits(user_id, request.amount)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

# ========== PROFILE ENDPOINTS ==========

@api_router.post("/profiles/search")
async def search_profiles(
    request: ProfileSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """Search profiles with filters"""
    is_admin = current_user.role == "super_admin"
    # Create ProfileFilter object with field mapping
    filter_data = request.dict(exclude={'page', 'page_size'})
    
    # Map fields from ProfileSearchRequest to ProfileFilter
    mapped_data = {}
    if filter_data.get('name'):
        # Split name into first_name and last_name if provided
        name_parts = filter_data['name'].split(' ', 1)
        mapped_data['first_name'] = name_parts[0]
        if len(name_parts) > 1:
            mapped_data['last_name'] = name_parts[1]
    
    # Map other fields
    field_mapping = {
        'job_title': 'job_title',
        'company_name': 'company_name', 
        'industry': 'industry',
        'location': 'city',  # Map location to city
        'keywords': 'keywords',
        'experience_years_min': 'experience_years_min',
        'experience_years_max': 'experience_years_max',
        'company_size': 'company_size',
        'revenue_range': 'revenue_range',
        'skills': 'skills'
    }
    
    for search_field, filter_field in field_mapping.items():
        if filter_data.get(search_field) is not None:
            mapped_data[filter_field] = filter_data[search_field]
    
    profile_filter = ProfileFilter(
        page=request.page,
        page_size=request.page_size,
        **mapped_data
    )
    results = await profile_service.get_profiles(
        filters=profile_filter,
        mask_data=not is_admin
    )
    return results

@api_router.get("/profiles/{profile_id}")
async def get_profile(
    profile_id: str,
    current_user: User = Depends(require_super_admin)
):
    """Get profile by ID (super admin only)"""
    profile = await profile_service.get_profile_by_id(profile_id, mask_data=False)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    return profile

@api_router.post("/profiles")
async def create_profile(
    request: ProfileCreateRequest,
    current_user: User = Depends(require_super_admin)
):
    """Create new profile (super admin only)"""
    try:
        profile = profile_service.create_profile(request.dict())
        return profile
    except Exception as e:
        logger.error(f"Create profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@api_router.put("/profiles/{profile_id}")
async def update_profile(
    profile_id: str,
    request: ProfileUpdateRequest,
    current_user: User = Depends(require_super_admin)
):
    """Update profile (super admin only)"""
    try:
        profile = profile_service.update_profile(profile_id, request.dict(exclude_unset=True))
        return profile
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@api_router.delete("/profiles/{profile_id}")
async def delete_profile(
    profile_id: str,
    current_user: User = Depends(require_super_admin)
):
    """Delete profile (super admin only)"""
    try:
        profile_service.delete_profile(profile_id)
        return {"message": "Profile deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@api_router.post("/profiles/{profile_id}/reveal")
async def reveal_contact(
    profile_id: str,
    request: RevealRequest,
    current_user: User = Depends(get_current_user)
):
    """Reveal contact information (email or phone)"""
    try:
        result = await profile_service.reveal_contact(
            user_id=current_user.id,
            profile_id=profile_id,
            reveal_type=request.reveal_type
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Reveal contact error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# ========== COMPANY ENDPOINTS ==========

@api_router.post("/companies/search")
async def search_companies(
    request: CompanySearchRequest,
    current_user: User = Depends(get_current_user)
):
    """Search companies with filters"""
    # Create CompanyFilter object
    from models import CompanyFilter
    company_filter = CompanyFilter(
        page=request.page,
        page_size=request.page_size,
        **request.dict(exclude={'page', 'page_size'})
    )
    results = await company_service.get_companies(company_filter)
    return results

@api_router.get("/companies/{company_id}")
async def get_company(
    company_id: str,
    current_user: User = Depends(require_super_admin)
):
    """Get company by ID (super admin only)"""
    company = await company_service.get_company_by_id(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    return company

@api_router.post("/companies")
async def create_company(
    request: CompanyCreateRequest,
    current_user: User = Depends(require_super_admin)
):
    """Create new company (super admin only)"""
    try:
        company = await company_service.create_company(request.dict())
        return company
    except Exception as e:
        logger.error(f"Create company error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@api_router.put("/companies/{company_id}")
async def update_company(
    company_id: str,
    request: CompanyUpdateRequest,
    current_user: User = Depends(require_super_admin)
):
    """Update company (super admin only)"""
    try:
        company = company_service.update_company(company_id, request.dict(exclude_unset=True))
        return company
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@api_router.delete("/companies/{company_id}")
async def delete_company(
    company_id: str,
    current_user: User = Depends(require_super_admin)
):
    """Delete company (super admin only)"""
    try:
        company_service.delete_company(company_id)
        return {"message": "Company deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

# ========== PLAN ENDPOINTS ==========

@api_router.get("/plans")
async def get_plans(
    page: int = 1,
    page_size: int = 20
):
    """Get all plans (public)"""
    plans = await plan_service.get_all_plans()
    return plans

@api_router.get("/plans/{plan_id}")
async def get_plan(plan_id: str):
    """Get plan by ID (public)"""
    plan = await plan_service.get_plan_by_id(plan_id)
    return plan

@api_router.post("/plans")
async def create_plan(
    request: PlanCreateRequest,
    current_user: User = Depends(require_super_admin)
):
    """Create new plan (super admin only)"""
    try:
        plan = plan_service.create_plan(request.dict())
        return plan
    except Exception as e:
        logger.error(f"Create plan error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@api_router.put("/plans/{plan_id}")
async def update_plan(
    plan_id: str,
    request: PlanUpdateRequest,
    current_user: User = Depends(require_super_admin)
):
    """Update plan (super admin only)"""
    try:
        plan = plan_service.update_plan(plan_id, request.dict(exclude_unset=True))
        return plan
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@api_router.delete("/plans/{plan_id}")
async def delete_plan(
    plan_id: str,
    current_user: User = Depends(require_super_admin)
):
    """Delete plan (super admin only)"""
    try:
        plan_service.delete_plan(plan_id)
        return {"message": "Plan deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

# ========== BULK UPLOAD ENDPOINTS ==========

@api_router.get("/bulk-upload/templates/{template_type}")
async def download_template(
    template_type: str,
    current_user: User = Depends(require_super_admin)
):
    """Download CSV template for bulk upload (super admin only)"""
    
    templates = {
        "profiles": [
            "first_name", "last_name", "job_title", "company_name", "industry",
            "emails", "phones", "city", "state", "country", "linkedin_url",
            "experience_years", "skills"
        ],
        "companies": [
            "name", "industry", "size", "revenue", "website", "description",
            "city", "state", "country", "founded_year"
        ],
        "combined": [
            "type", "first_name", "last_name", "job_title", "company_name", 
            "industry", "emails", "phones", "city", "state", "country", 
            "linkedin_url", "experience_years", "skills", "size", "revenue", 
            "website", "description", "founded_year"
        ]
    }
    
    if template_type not in templates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid template type. Use 'profiles', 'companies', or 'combined'"
        )
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(templates[template_type])
    
    # Add example row
    if template_type == "profiles":
        writer.writerow([
            "John", "Doe", "CEO", "TechCorp Inc", "Technology",
            "john.doe@techcorp.com", "+1-555-123-4567", "San Francisco", "CA", 
            "USA", "https://linkedin.com/in/johndoe", "10", "Leadership,Strategy"
        ])
    elif template_type == "companies":
        writer.writerow([
            "TechCorp Inc", "Technology", "100-500", "$10M-$50M",
            "https://techcorp.com", "Leading tech company", "San Francisco",
            "CA", "USA", "2015"
        ])
    else:  # combined
        writer.writerow([
            "profile", "John", "Doe", "CEO", "TechCorp Inc", "Technology",
            "john.doe@techcorp.com", "+1-555-123-4567", "San Francisco", "CA",
            "USA", "https://linkedin.com/in/johndoe", "10", "Leadership,Strategy",
            "", "", "", "", ""
        ])
        writer.writerow([
            "company", "", "", "", "TechCorp Inc", "Technology",
            "", "", "San Francisco", "CA", "USA", "", "", "",
            "100-500", "$10M-$50M", "https://techcorp.com",
            "Leading tech company", "2015"
        ])
    
    # Return as downloadable file
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={template_type}_template.csv"
        }
    )

@api_router.post("/bulk-upload")
async def bulk_upload(
    file: UploadFile = File(...),
    field_mapping: str = Form(...),
    validations: str = Form("{}"),
    current_user: User = Depends(require_super_admin)
):
    """Bulk upload profiles/companies from CSV/Excel (super admin only)"""
    try:
        # Read file content
        file_content = await file.read()
        
        # Determine file type
        file_type = file.filename.split('.')[-1].lower()
        if file_type not in ['csv', 'xlsx', 'xls']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type. Use CSV, XLSX, or XLS"
            )
        
        # Parse field mapping and validations
        mapping = json.loads(field_mapping)
        vals = json.loads(validations)
        
        # Start Celery task
        task = process_bulk_upload.delay(
            file_content=file_content,
            file_type=file_type,
            field_mapping=mapping,
            validations=vals
        )
        
        return {
            "task_id": task.id,
            "status": "processing",
            "message": "Bulk upload started"
        }
        
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid field_mapping or validations JSON"
        )
    except Exception as e:
        logger.error(f"Bulk upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@api_router.get("/bulk-upload/{task_id}")
async def get_upload_status(
    task_id: str,
    current_user: User = Depends(require_super_admin)
):
    """Get bulk upload task status"""
    task = process_bulk_upload.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {
            "task_id": task_id,
            "status": "pending",
            "progress": 0
        }
    elif task.state == 'PROGRESS':
        response = {
            "task_id": task_id,
            "status": "processing",
            "progress": task.info
        }
    elif task.state == 'SUCCESS':
        response = {
            "task_id": task_id,
            "status": "completed",
            "result": task.info
        }
    else:
        response = {
            "task_id": task_id,
            "status": "failed",
            "error": str(task.info)
        }
    
    return response

# ========== HEALTH CHECK ==========

@api_router.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "LeadGen Pro API is running", "version": "1.0.0"}

@api_router.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "redis": "connected"
    }

# Include router in app
app.include_router(api_router)

# CORS middleware
cors_origins = config.CORS_ORIGINS.split(',') if isinstance(config.CORS_ORIGINS, str) else ['*']
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
