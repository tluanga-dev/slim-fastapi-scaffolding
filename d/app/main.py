from fastapi import FastAPI
from app.core.config import settings
from app.core.errors import setup_exception_handlers
from app.modules.items import routes as items_routes
from app.modules.categories import routes as categories_routes
from app.modules.locations import routes as locations_routes
from app.modules.suppliers import routes as suppliers_routes
from app.modules.units_of_measurement import routes as units_routes
from app.modules.brands import routes as brands_routes
from app.modules.customer_addresses import routes as customer_addresses_routes
from app.modules.inventory_units import routes as inventory_units_routes
from app.modules.rental_returns import routes as rental_returns_routes

app = FastAPI(title=settings.APP_NAME)
app.include_router(items_routes.router, prefix="/items")
app.include_router(categories_routes.router, prefix="/categories")
app.include_router(locations_routes.router, prefix="/locations")
app.include_router(suppliers_routes.router, prefix="/suppliers")
app.include_router(units_routes.router, prefix="/units-of-measurement")
app.include_router(brands_routes.router, prefix="/brands")
app.include_router(customer_addresses_routes.router, prefix="/customer-addresses")
app.include_router(inventory_units_routes.router, prefix="/inventory-units")
app.include_router(rental_returns_routes.router, prefix="/rental-returns")
setup_exception_handlers(app)