from fastapi import FastAPI
from app.core.config import settings
from app.core.errors import setup_exception_handlers
from app.modules.items import routes as items_routes

app = FastAPI(title=settings.APP_NAME)
app.include_router(items_routes.router, prefix="/items")
setup_exception_handlers(app)