#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: |
  Building production-ready B2B lead generation platform (LeadGen Pro) with:
  - 200M+ profile/company data handling with MongoDB sharding
  - Credit-based contact reveal (1 for email, 3 for phone) - charge only once per unique reveal
  - Super admin CRUD for users, profiles, companies, plans, credits
  - Bulk upload (CSV/Excel) with field mapping and validation
  - JWT auth with password reset/forgot password
  - Data masking (not encryption at REST)
  - Fast filtering with proper indexing
  - Redis + Celery async processing
  - SEO-optimized frontend
  - Production-ready for 10k+ users
  - Auto setup script

backend:
  - task: "JWT Authentication (register, login, me)"
    implemented: true
    working: "NA"
    file: "services/auth_service.py, server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Implemented user registration, login with JWT tokens. Rate limited (5/min register, 10/min login). Sends welcome email on registration."
  
  - task: "Password Reset/Forgot Password"
    implemented: true
    working: "NA"
    file: "services/auth_service.py, services/email_service.py, server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Implemented forgot password and reset password with email tokens. Rate limited (3/min forgot, 5/min reset). SMTP configured with user credentials."
  
  - task: "User Management CRUD (Super Admin)"
    implemented: true
    working: "NA"
    file: "services/user_service.py, server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Full CRUD operations for users. Get all users with pagination and role filtering. Add/deduct credits."
  
  - task: "Profile Search with Filters"
    implemented: true
    working: "NA"
    file: "services/profile_service.py, server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Profile search across sharded collections (a-z + other). Filters: name, job_title, industry, location, keywords. Data masked for regular users."
  
  - task: "Credit-based Contact Reveal"
    implemented: true
    working: "NA"
    file: "services/profile_service.py, server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Reveal email (1 credit) or phone (3 credits). Tracks revealed_contacts to charge only once per unique reveal. Creates credit_transactions for audit."
  
  - task: "Profile CRUD (Super Admin)"
    implemented: true
    working: "NA"
    file: "services/profile_service.py, server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Create, update, delete profiles. Works with sharded collections."
  
  - task: "Company Search and CRUD"
    implemented: true
    working: "NA"
    file: "services/company_service.py, server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Company search and CRUD operations. Sharded by company name (a-z + other)."
  
  - task: "Plan Management (Super Admin)"
    implemented: true
    working: "NA"
    file: "services/plan_service.py, server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Create, update, delete subscription plans. Soft delete (is_active flag)."
  
  - task: "Bulk Upload with Celery"
    implemented: true
    working: "NA"
    file: "tasks.py, server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Async bulk upload for CSV/XLSX/XLS. Field mapping and validation support. Progress tracking with Celery tasks."
  
  - task: "Data Masking (emails, phones, domains)"
    implemented: true
    working: "NA"
    file: "utils.py, services/profile_service.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Masking functions for email (j***@gmail.com), phone (***-***-1234), domain (***com). Applied to profile responses for non-admin users."
  
  - task: "MongoDB Sharding and Indexing"
    implemented: true
    working: "NA"
    file: "database.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Sharded collections by first letter (profiles_a-z, companies_a-z). Compound indexes on searchable fields. Text indexes for full-text search."
  
  - task: "Rate Limiting"
    implemented: true
    working: "NA"
    file: "server.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Rate limiting with slowapi. Auth endpoints rate limited to prevent abuse."

frontend:
  - task: "Auth Pages (Login, Register, Forgot/Reset Password)"
    implemented: false
    working: "NA"
    file: "pages/"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Not yet implemented. Need to create auth pages with proper UI/UX."
  
  - task: "Dashboard - Search & Filter Profiles"
    implemented: false
    working: "NA"
    file: "pages/"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Not yet implemented. Main user dashboard for searching profiles."
  
  - task: "Super Admin Dashboard"
    implemented: false
    working: "NA"
    file: "pages/"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Not yet implemented. Admin panel for managing users, profiles, companies, plans."
  
  - task: "Bulk Upload UI with Field Mapping"
    implemented: false
    working: "NA"
    file: "pages/"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Not yet implemented. UI wizard for bulk upload with drag-drop field mapping."
  
  - task: "SEO Optimization"
    implemented: false
    working: "NA"
    file: "pages/, components/"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "react-helmet-async installed but not used. Need to add meta tags, structured data, etc."

metadata:
  created_by: "main_agent"
  version: "1.0"
  test_sequence: 0
  run_ui: false

test_plan:
  current_focus:
    - "JWT Authentication"
    - "Password Reset/Forgot Password"
    - "Credit-based Contact Reveal"
    - "Profile Search with Filters"
    - "Bulk Upload"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
  - agent: "main"
    message: |
      Backend implementation complete with:
      - All authentication endpoints (register, login, password reset)
      - User/Profile/Company/Plan CRUD operations
      - Credit-based reveal with unique tracking
      - Data masking for sensitive fields
      - Bulk upload with Celery async processing
      - MongoDB sharding for scalability
      - Rate limiting for security
      - Seed data: 6 users, 3 plans, 1000 companies, 5000 profiles
      
      Credentials:
      - Super Admin: admin@leadgen.com / admin123
      - Test Users: user1@example.com / password123
      
      Next: Need backend testing before starting frontend development.