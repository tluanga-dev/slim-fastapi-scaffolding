from enum import Enum


class AddressType(str, Enum):
    """Address type enumeration for customer addresses."""
    
    BILLING = "BILLING"
    SHIPPING = "SHIPPING"
    MAILING = "MAILING"
    BUSINESS = "BUSINESS"
    HOME = "HOME"
    
    def __str__(self) -> str:
        return self.value
    
    @classmethod
    def get_display_name(cls, address_type: "AddressType") -> str:
        """Get human-readable display name for address type."""
        display_names = {
            cls.BILLING: "Billing Address",
            cls.SHIPPING: "Shipping Address", 
            cls.MAILING: "Mailing Address",
            cls.BUSINESS: "Business Address",
            cls.HOME: "Home Address"
        }
        return display_names.get(address_type, address_type.value)
    
    @classmethod
    def get_description(cls, address_type: "AddressType") -> str:
        """Get description for address type."""
        descriptions = {
            cls.BILLING: "Address used for billing and invoicing purposes",
            cls.SHIPPING: "Address where items are delivered",
            cls.MAILING: "Address for postal correspondence",
            cls.BUSINESS: "Business or office address",
            cls.HOME: "Residential address"
        }
        return descriptions.get(address_type, "")