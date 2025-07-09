from fastapi import Depends
from app.db.session import get_session
from app.modules.items.repository import ItemRepository
from app.modules.items.service import ItemService
from app.modules.categories.repository import CategoryRepository
from app.modules.categories.service import CategoryService
from app.modules.locations.repository import LocationRepository
from app.modules.locations.service import LocationService
from app.modules.suppliers.repository import SupplierRepository
from app.modules.suppliers.service import SupplierService
from app.modules.units_of_measurement.repository import UnitOfMeasurementRepository
from app.modules.units_of_measurement.service import UnitOfMeasurementService
from app.modules.brands.repository import BrandRepository
from app.modules.brands.service import BrandService
from app.modules.customer_addresses.repository import CustomerAddressRepository
from app.modules.customer_addresses.service import CustomerAddressService
from app.modules.inventory_units.repository import InventoryUnitRepository
from app.modules.inventory_units.service import InventoryUnitService
from app.modules.rental_returns.repository import RentalReturnRepository
from app.modules.rental_returns.service import RentalReturnService

async def get_item_repository(session=Depends(get_session)):
    return ItemRepository(session)

async def get_item_service(repo=Depends(get_item_repository)):
    return ItemService(repo)

async def get_category_repository(session=Depends(get_session)):
    return CategoryRepository(session)

async def get_category_service(repo=Depends(get_category_repository)):
    return CategoryService(repo)

async def get_location_repository(session=Depends(get_session)):
    return LocationRepository(session)

async def get_location_service(repo=Depends(get_location_repository)):
    return LocationService(repo)

async def get_supplier_repository(session=Depends(get_session)):
    return SupplierRepository(session)

async def get_supplier_service(repo=Depends(get_supplier_repository)):
    return SupplierService(repo)

async def get_unit_of_measurement_repository(session=Depends(get_session)):
    return UnitOfMeasurementRepository(session)

async def get_unit_of_measurement_service(repo=Depends(get_unit_of_measurement_repository)):
    return UnitOfMeasurementService(repo)

async def get_brand_repository(session=Depends(get_session)):
    return BrandRepository(session)

async def get_brand_service(repo=Depends(get_brand_repository)):
    return BrandService(repo)

async def get_customer_address_repository(session=Depends(get_session)):
    return CustomerAddressRepository(session)

async def get_customer_address_service(repo=Depends(get_customer_address_repository)):
    return CustomerAddressService(repo)

async def get_inventory_unit_repository(session=Depends(get_session)):
    return InventoryUnitRepository(session)

async def get_inventory_unit_service(repo=Depends(get_inventory_unit_repository)):
    return InventoryUnitService(repo)

async def get_rental_return_repository(session=Depends(get_session)):
    return RentalReturnRepository(session)

async def get_rental_return_service(repo=Depends(get_rental_return_repository)):
    return RentalReturnService(repo)