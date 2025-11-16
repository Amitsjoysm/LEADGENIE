from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from contextlib import asynccontextmanager
import logging
from typing import List, Optional, Dict, Any
import json
import redis.asyncio as redis

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

# Rate Limiter with Redis storage
from slowapi.middleware import SlowAPIMiddleware
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=config.REDIS_URL
)

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
    
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    await close_db()
    logger.info("Application shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="LeadGen Pro API",
    version="1.0.0",
    description="Production-ready B2B Lead Generation Platform API",
    lifespan=lifespan
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

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
    
    user = await auth_service.get_user_by_email(email)
    return user

# Dependency for super admin only
async def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require super admin role"""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return current_user

# ========== AUTH ENDPOINTS ==========

@api_router.post("/auth/register", response_model=User)
@limiter.limit("5/minute")
async def register(request: Request, user_data: UserCreate):
    """Register a new user"""
    return await auth_service.register_user(user_data)

@api_router.post("/auth/login", response_model=Token)
@limiter.limit("10/minute")
async def login(request: Request, login_data: UserLogin):
    """Login user"""
    return await auth_service.login_user(login_data)

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return current_user

@api_router.post("/auth/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(request: Request, reset_request: PasswordResetRequest):
    """Request password reset"""
    token = await auth_service.create_password_reset_token(reset_request.email)
    
    # Send email (async task)
    await email_service.send_password_reset_email(reset_request.email, token)
    
    return {"message": "Password reset email sent if account exists"}

@api_router.post("/auth/reset-password")
@limiter.limit("5/minute")
async def reset_password(request: Request, reset_confirm: PasswordResetConfirm):
    """Reset password with token"""
    await auth_service.reset_password(reset_confirm.token, reset_confirm.new_password)
    return {"message": "Password reset successful"}

# ========== USER ENDPOINTS ==========

@api_router.get("/users", response_model=List[User])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
    current_user: User = Depends(require_super_admin)
):
    """Get all users (super admin only)"""
    return await user_service.get_all_users(skip, limit, role)

@api_router.get("/users/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    current_user: User = Depends(require_super_admin)
):
    """Get user by ID (super admin only)"""
    return await user_service.get_user_by_id(user_id)

@api_router.patch("/users/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(require_super_admin)
):
    """Update user (super admin only)"""
    return await user_service.update_user(user_id, user_update)

@api_router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_super_admin)
):
    """Delete user (super admin only)"""
    await user_service.delete_user(user_id)
    return {"message": "User deleted successfully"}

@api_router.post("/users/{user_id}/credits", response_model=User)
async def add_credits(
    user_id: str,
    credits: int,
    current_user: User = Depends(require_super_admin)
):
    """Add credits to user (super admin only)"""
    return await user_service.add_credits(user_id, credits)

# ========== PROFILE ENDPOINTS ==========

@api_router.post("/profiles", response_model=Profile)
async def create_profile(
    profile_data: ProfileCreate,
    current_user: User = Depends(require_super_admin)
):
    """Create profile (super admin only)"""
    return await profile_service.create_profile(profile_data)

@api_router.post("/profiles/search")
async def search_profiles(
    filters: ProfileFilter,
    current_user: User = Depends(get_current_user)
):
    """Search profiles with filters"""
    # Regular users see masked data
    mask_data = current_user.role != UserRole.SUPER_ADMIN
    return await profile_service.get_profiles(filters, mask_data)

@api_router.get("/profiles/{profile_id}", response_model=Profile)
async def get_profile(
    profile_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get profile by ID"""
    mask_data = current_user.role != UserRole.SUPER_ADMIN
    return await profile_service.get_profile_by_id(profile_id, mask_data)

@api_router.patch("/profiles/{profile_id}", response_model=Profile)
async def update_profile(
    profile_id: str,
    update_data: dict,
    current_user: User = Depends(require_super_admin)
):
    """Update profile (super admin only)"""
    return await profile_service.update_profile(profile_id, update_data)

@api_router.delete("/profiles/{profile_id}")
async def delete_profile(
    profile_id: str,
    current_user: User = Depends(require_super_admin)
):
    """Delete profile (super admin only)"""
    await profile_service.delete_profile(profile_id)
    return {"message": "Profile deleted successfully"}

@api_router.post("/profiles/{profile_id}/reveal")
async def reveal_contact_endpoint(
    profile_id: str,
    reveal_request: RevealRequest,
    current_user: User = Depends(get_current_user)
):
    """Reveal email or phone (costs credits, charges only once per unique reveal)"""
    if reveal_request.reveal_type not in ['email', 'phone']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="reveal_type must be 'email' or 'phone'"
        )
    
    return await profile_service.reveal_contact(
        user_id=current_user.id,
        profile_id=profile_id,
        reveal_type=reveal_request.reveal_type
    )

# ========== COMPANY ENDPOINTS ==========

@api_router.post("/companies", response_model=Company)
async def create_company(
    company_data: CompanyCreate,
    current_user: User = Depends(require_super_admin)
):
    """Create company (super admin only)"""
    return await company_service.create_company(company_data)

@api_router.post("/companies/search")
async def search_companies(
    filters: CompanyFilter,
    current_user: User = Depends(get_current_user)
):
    """Search companies with filters"""
    return await company_service.get_companies(filters)

@api_router.get("/companies/{company_id}", response_model=Company)
async def get_company(
    company_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get company by ID"""
    return await company_service.get_company_by_id(company_id)

@api_router.patch("/companies/{company_id}", response_model=Company)
async def update_company(
    company_id: str,
    update_data: dict,
    current_user: User = Depends(require_super_admin)
):
    """Update company (super admin only)"""
    return await company_service.update_company(company_id, update_data)

@api_router.delete("/companies/{company_id}")
async def delete_company(
    company_id: str,
    current_user: User = Depends(require_super_admin)
):
    """Delete company (super admin only)"""
    await company_service.delete_company(company_id)
    return {"message": "Company deleted successfully"}

# ========== PLAN ENDPOINTS ==========

@api_router.post("/plans", response_model=Plan)
async def create_plan(
    plan_data: PlanCreate,
    current_user: User = Depends(require_super_admin)
):
    """Create plan (super admin only)"""
    return await plan_service.create_plan(plan_data)

@api_router.get("/plans", response_model=List[Plan])
async def get_plans(active_only: bool = True):
    """Get all plans"""
    return await plan_service.get_all_plans(active_only)

@api_router.get("/plans/{plan_id}", response_model=Plan)
async def get_plan(plan_id: str):
    """Get plan by ID"""
    return await plan_service.get_plan_by_id(plan_id)

@api_router.patch("/plans/{plan_id}", response_model=Plan)
async def update_plan(
    plan_id: str,
    update_data: dict,
    current_user: User = Depends(require_super_admin)
):
    """Update plan (super admin only)"""
    return await plan_service.update_plan(plan_id, update_data)

@api_router.delete("/plans/{plan_id}")
async def delete_plan(
    plan_id: str,
    current_user: User = Depends(require_super_admin)
):
    """Delete plan (super admin only)"""
    await plan_service.delete_plan(plan_id)
    return {"message": "Plan deleted successfully"}

# ========== BULK UPLOAD ENDPOINTS ==========

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
    allow_credentials=True,
    allow_origins=cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
