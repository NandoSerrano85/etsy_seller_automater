from fastapi import FastAPI
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

def register_routes(app: FastAPI):
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