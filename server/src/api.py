from fastapi import FastAPI
from fastapi.responses import JSONResponse
from server.src.routes.auth.controller import router as auth_router
from server.src.routes.third_party.controller import router as third_party_router
from server.src.routes.user.controller import router as user_router
from server.src.routes.templates.controller import router as template_router
from server.src.routes.canvas_sizes.controller import router as canvas_config_router
from server.src.routes.dashboard.controller import router as dashboard_router
from server.src.routes.size_config.controller import router as size_config_router
from server.src.routes.orders.controller import router as order_router
from server.src.routes.designs.controller import router as design_router
from server.src.routes.mockups.controller import router as mockup_router
from server.src.routes.third_party_listings.controller import router as third_party_listings_router
from server.src.routes.shopify.shopify_oauth import router as shopify_router
from server.src.routes.template_editor.controller import router as template_editor_router
from server.src.routes.platform_connections.controller import router as platform_connections_router
from server.src.routes.admin.nas_migration import router as admin_router
from server.src.routes.cache.controller import router as cache_router
from server.src.routes.oauth_tokens import router as oauth_tokens_router

# Multi-tenant routes - conditionally imported if multi-tenant is enabled
def get_multi_tenant_routers():
    """Import multi-tenant routers only if multi-tenant is enabled"""
    routers = []
    if os.getenv('ENABLE_MULTI_TENANT', 'false').lower() == 'true':
        print("🔄 Multi-tenant enabled, attempting to import routers...")
        try:
            print("📋 Importing organization router...")
            from server.src.routes.organizations.routes import router as organization_router
            routers.append(organization_router)
            print("✅ Organization router imported successfully")

            print("📋 Importing printer router...")
            from server.src.routes.printers.routes import router as printer_router
            routers.append(printer_router)
            print("✅ Printer router imported successfully")

            print(f"✅ Successfully imported {len(routers)} multi-tenant routers")
        except ImportError as e:
            print(f"❌ Warning: Could not import multi-tenant routers: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("⚠️  Multi-tenant features disabled")
    return routers
import os
import time
import psutil

def register_routes(app: FastAPI):
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Minimal health check for deployment - always returns healthy if API is running"""
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "timestamp": int(time.time()),
                "version": "1.0.0",
                "environment": os.getenv("DOCKER_ENV", "development")
            }
        )

    @app.get("/health/detailed")
    async def detailed_health_check():
        """Detailed health check with system metrics - slower but more comprehensive"""
        try:
            # Check system resources (non-blocking)
            cpu_percent = psutil.cpu_percent(interval=0)  # Non-blocking
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Check database connection
            db_status = "unknown"
            try:
                from server.src.database.core import engine
                from sqlalchemy import text
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                    db_status = "healthy"
            except Exception:
                db_status = "unhealthy"

            return JSONResponse(
                status_code=200,
                content={
                    "status": "healthy",
                    "timestamp": int(time.time()),
                    "version": "1.0.0",
                    "environment": os.getenv("DOCKER_ENV", "development"),
                    "system": {
                        "cpu_percent": cpu_percent,
                        "memory_percent": memory.percent,
                        "memory_available": memory.available,
                        "disk_percent": (disk.used / disk.total) * 100,
                        "disk_free": disk.free
                    },
                    "services": {
                        "database": db_status,
                        "api": "healthy"
                    }
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "timestamp": int(time.time()),
                    "error": str(e)
                }
            )
    
    # Simple ping endpoint
    @app.get("/ping")
    async def ping():
        """Simple ping endpoint"""
        return {"status": "ok", "timestamp": int(time.time())}

    # Readiness endpoint for Railway
    @app.get("/ready")
    async def ready():
        """Readiness check for Railway"""
        return {"status": "ready", "timestamp": int(time.time())}

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "message": "CraftFlow API is running",
            "status": "healthy",
            "timestamp": int(time.time()),
            "version": "1.0.0"
        }
    
    # Include all application routes
    app.include_router(auth_router)
    app.include_router(third_party_router)
    app.include_router(user_router)
    app.include_router(template_router)
    app.include_router(canvas_config_router)
    app.include_router(dashboard_router)
    app.include_router(size_config_router)
    app.include_router(order_router)
    app.include_router(design_router)
    app.include_router(mockup_router)
    app.include_router(third_party_listings_router)
    app.include_router(shopify_router)
    app.include_router(template_editor_router, prefix="/api")
    app.include_router(platform_connections_router)
    app.include_router(admin_router)
    app.include_router(cache_router, prefix="/api")
    app.include_router(oauth_tokens_router)

    # Multi-tenant routes - only enabled if multi-tenant is enabled
    multi_tenant_routers = get_multi_tenant_routers()
    for router in multi_tenant_routers:
        app.include_router(router, prefix="/api")