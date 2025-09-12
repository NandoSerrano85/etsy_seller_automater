# Authentication Integration TODO

## Issue

The new multi-tenant routes need to be integrated with the existing authentication system.

## Current State

- ✅ New routes created with full functionality
- ❌ Authentication imports incorrect
- ❌ Routes commented out in main API to prevent startup errors

## Authentication Pattern in Existing Code

### Correct Import Pattern

```python
from server.src.routes.auth.service import CurrentUser
```

### Correct Function Signature

```python
def my_endpoint(
    request_data: MyRequestModel,
    current_user: CurrentUser,  # No Depends() needed
    db: Session = Depends(get_db)
):
```

### Getting User ID

```python
user_id = current_user.get_uuid()
if not user_id:
    raise HTTPException(status_code=401, detail="User not authenticated")
```

## Files Needing Auth Fix

### Route Files

1. `server/src/routes/organizations/routes.py`
2. `server/src/routes/shops/routes.py`
3. `server/src/routes/files/routes.py`
4. `server/src/routes/print_jobs/routes.py`
5. `server/src/routes/events/routes.py`
6. `server/src/routes/printers/routes.py`

### Changes Needed Per File

#### 1. Update Imports

```python
# Remove
from server.src.auth.dependencies import get_current_user
from server.src.entities.user import User

# Add
from server.src.routes.auth.service import CurrentUser
```

#### 2. Update Function Signatures

```python
# Before
def endpoint(
    data: Model,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

# After
def endpoint(
    data: Model,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
```

#### 3. Update User ID Access

```python
# Before
user_id = current_user.id

# After
user_id = current_user.get_uuid()
if not user_id:
    raise HTTPException(status_code=401, detail="User not authenticated")
```

## Multi-Tenant Considerations

### Organization Access

The current auth system doesn't have built-in organization awareness. Need to either:

1. **Option A**: Get user's org_id from database lookup
2. **Option B**: Extend auth system to include org_id in token
3. **Option C**: Add organization middleware

### Recommended Approach (Option A - Quick Fix)

```python
def get_user_with_org(current_user: CurrentUser, db: Session = Depends(get_db)):
    user_id = current_user.get_uuid()
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.org_id:
        raise HTTPException(status_code=400, detail="User not assigned to organization")

    return user

# Usage in endpoints
def my_endpoint(
    data: MyModel,
    user: User = Depends(get_user_with_org),
    db: Session = Depends(get_db)
):
    org_id = user.org_id
    user_id = user.id
    # ... rest of endpoint
```

## Steps to Re-enable Routes

1. **Create auth helper** (`server/src/routes/common/auth.py`):

   ```python
   from fastapi import Depends, HTTPException
   from sqlalchemy.orm import Session
   from server.src.database.core import get_db
   from server.src.routes.auth.service import CurrentUser
   from server.src.entities.user import User

   def get_current_user_with_org(
       current_user: CurrentUser,
       db: Session = Depends(get_db)
   ) -> User:
       user_id = current_user.get_uuid()
       if not user_id:
           raise HTTPException(status_code=401, detail="User not authenticated")

       user = db.query(User).filter(User.id == user_id).first()
       if not user:
           raise HTTPException(status_code=404, detail="User not found")

       if not user.org_id:
           raise HTTPException(status_code=400, detail="User not assigned to organization")

       return user
   ```

2. **Update all route files** to use the helper

3. **Update function signatures** to use the helper:

   ```python
   def endpoint(
       data: MyModel,
       current_user: User = Depends(get_current_user_with_org),
       db: Session = Depends(get_db)
   ):
       org_id = current_user.org_id
       user_id = current_user.id
       # ... endpoint logic
   ```

4. **Uncomment routes** in `server/src/api.py`

5. **Test authentication** flow

## Priority

**Medium** - The core printer and canvas config functionality is implemented and working. The API routes can be enabled later when multi-tenant authentication is properly integrated.

## Current Workaround

The application can start and run normally with existing single-tenant functionality. The new entities and business logic are available for integration into the gangsheet engine even without the API routes being active.
