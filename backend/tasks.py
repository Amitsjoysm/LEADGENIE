from celery_app import celery_app
from database import Database, get_shard_key
from motor.motor_asyncio import AsyncIOMotorClient
from config import config
import logging
import asyncio
import openpyxl
import xlrd
import csv
import io
from datetime import datetime, timezone
import uuid

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def process_bulk_upload(self, file_content: bytes, file_type: str, field_mapping: dict, validations: dict):
    """Process bulk upload file"""
    try:
        # Parse file based on type
        if file_type == 'csv':
            rows = parse_csv(file_content)
        elif file_type == 'xlsx':
            rows = parse_xlsx(file_content)
        elif file_type == 'xls':
            rows = parse_xls(file_content)
        else:
            return {"status": "error", "message": "Unsupported file type"}
        
        total_rows = len(rows)
        self.update_state(state='PROGRESS', meta={'total': total_rows, 'processed': 0, 'success': 0, 'errors': 0})
        
        # Process rows asynchronously
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            process_rows_async(rows, field_mapping, validations, self)
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Bulk upload error: {e}")
        return {"status": "error", "message": str(e)}

def parse_csv(file_content: bytes) -> list:
    """Parse CSV file"""
    content = file_content.decode('utf-8')
    reader = csv.DictReader(io.StringIO(content))
    return list(reader)

def parse_xlsx(file_content: bytes) -> list:
    """Parse XLSX file"""
    workbook = openpyxl.load_workbook(io.BytesIO(file_content))
    sheet = workbook.active
    
    # Get headers from first row
    headers = [cell.value for cell in sheet[1]]
    
    # Get data rows
    rows = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        row_dict = dict(zip(headers, row))
        rows.append(row_dict)
    
    return rows

def parse_xls(file_content: bytes) -> list:
    """Parse XLS file"""
    workbook = xlrd.open_workbook(file_contents=file_content)
    sheet = workbook.sheet_by_index(0)
    
    # Get headers
    headers = [cell.value for cell in sheet.row(0)]
    
    # Get data rows
    rows = []
    for row_idx in range(1, sheet.nrows):
        row_values = [cell.value for cell in sheet.row(row_idx)]
        row_dict = dict(zip(headers, row_values))
        rows.append(row_dict)
    
    return rows

async def process_rows_async(rows: list, field_mapping: dict, validations: dict, task):
    """Process rows and insert into database"""
    # Connect to database
    client = AsyncIOMotorClient(config.MONGO_URL)
    db = client[config.DB_NAME]
    
    success_count = 0
    error_count = 0
    errors = []
    
    for idx, row in enumerate(rows):
        try:
            # Map fields
            profile_data = {}
            company_data = {}
            
            for csv_field, model_field in field_mapping.items():
                value = row.get(csv_field)
                
                # Apply validations if specified
                if model_field in validations:
                    validation = validations[model_field]
                    if not validate_field(value, validation):
                        raise ValueError(f"Validation failed for {model_field}")
                
                # Separate profile and company fields
                if model_field in ['first_name', 'last_name', 'job_title', 'emails', 'phones', 'profile_linkedin_url']:
                    profile_data[model_field] = value
                elif model_field in ['company_name', 'company_domain', 'revenue', 'employee_size', 'industry']:
                    company_data[model_field if not model_field.startswith('company_') else model_field.replace('company_', '')] = value
                else:
                    # Fields that go to both
                    profile_data[model_field] = value
                    company_data[model_field] = value
            
            # Create profile if we have required fields
            if profile_data.get('last_name'):
                shard = get_shard_key(profile_data['last_name'])
                collection_name = f'profiles_{shard}'
                
                # Handle array fields
                if 'emails' in profile_data and isinstance(profile_data['emails'], str):
                    profile_data['emails'] = [e.strip() for e in profile_data['emails'].split(',')]
                if 'phones' in profile_data and isinstance(profile_data['phones'], str):
                    profile_data['phones'] = [p.strip() for p in profile_data['phones'].split(',')]
                
                profile_data['id'] = str(uuid.uuid4())
                profile_data['created_at'] = datetime.now(timezone.utc).isoformat()
                profile_data['updated_at'] = datetime.now(timezone.utc).isoformat()
                
                await db[collection_name].insert_one(profile_data)
            
            # Create company if we have required fields
            if company_data.get('name'):
                shard = get_shard_key(company_data['name'])
                collection_name = f'companies_{shard}'
                
                company_data['id'] = str(uuid.uuid4())
                company_data['created_at'] = datetime.now(timezone.utc).isoformat()
                company_data['updated_at'] = datetime.now(timezone.utc).isoformat()
                
                # Check if company already exists
                existing = await db[collection_name].find_one({"name": company_data['name']})
                if not existing:
                    await db[collection_name].insert_one(company_data)
            
            success_count += 1
            
        except Exception as e:
            error_count += 1
            errors.append({"row": idx + 1, "error": str(e)})
            logger.error(f"Error processing row {idx + 1}: {e}")
        
        # Update progress every 100 rows
        if (idx + 1) % 100 == 0:
            task.update_state(
                state='PROGRESS',
                meta={
                    'total': len(rows),
                    'processed': idx + 1,
                    'success': success_count,
                    'errors': error_count
                }
            )
    
    client.close()
    
    return {
        "status": "completed",
        "total_rows": len(rows),
        "success_count": success_count,
        "error_count": error_count,
        "errors": errors[:100]  # Return first 100 errors
    }

def validate_field(value, validation: dict) -> bool:
    """Validate field based on validation rules"""
    if 'type' in validation:
        if validation['type'] == 'string' and not isinstance(value, str):
            return False
        elif validation['type'] == 'number' and not isinstance(value, (int, float)):
            return False
    
    if 'max_length' in validation:
        if isinstance(value, str) and len(value) > validation['max_length']:
            return False
    
    if 'min_length' in validation:
        if isinstance(value, str) and len(value) < validation['min_length']:
            return False
    
    return True
