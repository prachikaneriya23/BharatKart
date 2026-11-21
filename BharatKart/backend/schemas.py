from datetime import datetime
from decimal import Decimal
import re
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class CityDTO(BaseModel):
    id: int
    name: str
    state: str
    code: str

    @property
    def label(self) -> str:
        return f"{self.name}, {self.state}"


class ProductVariantDTO(BaseModel):
    id: int
    variant_name: str
    variant_value: str
    price_adjustment: Decimal = Decimal("0.00")
    sku_modifier: Optional[str] = None
    stock_quantity: int = 10


class ProductCardDTO(BaseModel):
    id: int
    sku: str
    name: str
    brand: str
    category: str
    description: str
    image_url: str
    price: Decimal
    mrp: Decimal
    discount_percent: int
    rating: Decimal
    is_featured: bool
    city_id: int
    city_name: str
    stock_quantity: int
    shop_id: Optional[int] = None
    shop_name: Optional[str] = None
    shop_code: Optional[str] = None
    variants: List[ProductVariantDTO] = []


class ProductCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    brand: str = Field(min_length=2, max_length=100)
    category: str = Field(min_length=2, max_length=80)
    description: str = Field(min_length=5, max_length=2000)
    price: Decimal = Field(gt=0)
    mrp: Decimal = Field(gt=0)
    image_url: Optional[str] = ""
    initial_stock: int = Field(ge=0, default=10)
    city_id: int
    is_featured: bool = False

    @field_validator("mrp")
    @classmethod
    def validate_mrp(cls, v: Decimal, info) -> Decimal:
        price = info.data.get("price")
        if price is not None and v < price:
            raise ValueError("MRP cannot be less than selling price.")
        return v


class ProductUpdateRequest(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    mrp: Optional[Decimal] = None
    image_url: Optional[str] = None
    is_featured: Optional[bool] = None


class CartItemInput(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    variant_info: Optional[str] = None


class CheckoutRequest(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=64)
    city_id: int
    customer_name: str = Field(min_length=2, max_length=150)
    customer_email: str = Field(min_length=5, max_length=150)
    customer_phone: str = Field(min_length=10, max_length=15)
    shipping_address: str = Field(min_length=8, max_length=500)
    pincode: str = Field(min_length=6, max_length=6)
    items: List[CartItemInput] = Field(min_length=1)

    @field_validator("customer_name", "shipping_address")
    @classmethod
    def strip_text(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Field cannot be blank.")
        return cleaned

    @field_validator("customer_email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("Please enter a valid email address.")
        return v

    @field_validator("customer_phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        if len(digits) == 12 and digits.startswith("91"):
            digits = digits[2:]
        if not re.match(r"^[6-9]\d{9}$", digits):
            raise ValueError("Enter a valid 10-digit Indian mobile number.")
        return digits

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^[1-9]\d{5}$", v):
            raise ValueError("Enter a valid 6-digit Indian pincode.")
        return v


class CustomerRegistrationRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: str = Field(min_length=5, max_length=150)
    phone: str = Field(min_length=10, max_length=15)
    password: Optional[str] = Field(default="Bharat@123", min_length=6)
    default_city_id: int
    default_address: str = Field(min_length=8, max_length=500)
    pincode: str = Field(min_length=6, max_length=6)

    @field_validator("full_name", "default_address")
    @classmethod
    def clean_cust_str(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("This field cannot be blank.")
        return cleaned

    @field_validator("email")
    @classmethod
    def validate_cust_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("Please enter a valid email address.")
        return v

    @field_validator("phone")
    @classmethod
    def validate_cust_phone(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        if len(digits) == 12 and digits.startswith("91"):
            digits = digits[2:]
        if not re.match(r"^[6-9]\d{9}$", digits):
            raise ValueError("Enter a valid 10-digit Indian mobile number.")
        return digits

    @field_validator("pincode")
    @classmethod
    def validate_cust_pin(cls, v: str) -> str:
        pin = v.strip()
        if not re.match(r"^[1-9]\d{5}$", pin):
            raise ValueError("Enter a valid 6-digit Indian pincode.")
        return pin


class CustomerDTO(BaseModel):
    id: int
    user_id: Optional[int] = None
    full_name: str
    email: str
    phone: str
    default_city_id: int
    city_name: str
    default_address: str
    pincode: str


class UserDTO(BaseModel):
    id: int
    email: str
    role: str
    full_name: str
    phone: Optional[str] = None
    is_active: bool = True
    shop_id: Optional[int] = None
    shop_code: Optional[str] = None


class UserLoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=150)
    password: str = Field(min_length=4)


class ShopRegistrationRequest(BaseModel):
    shop_name: str = Field(min_length=3, max_length=180)
    owner_name: str = Field(min_length=2, max_length=150)
    owner_email: str = Field(min_length=5, max_length=150)
    owner_phone: str = Field(min_length=10, max_length=15)
    password: Optional[str] = Field(default="Seller@123", min_length=6)
    business_type: str = Field(min_length=2, max_length=80)
    primary_category: str = Field(min_length=2, max_length=80)
    gstin: Optional[str] = ""
    pan_number: str = Field(min_length=10, max_length=10)
    fssai_license: Optional[str] = ""
    city_id: int
    shop_address: str = Field(min_length=8, max_length=500)
    pincode: str = Field(min_length=6, max_length=6)
    pickup_slot: str = Field(min_length=3, max_length=80)
    bank_account_holder: str = Field(min_length=2, max_length=150)
    bank_account_number: str = Field(min_length=9, max_length=18)
    bank_ifsc: str = Field(min_length=11, max_length=11)
    upi_id: Optional[str] = ""
    shop_description: Optional[str] = ""

    @field_validator("shop_name", "owner_name", "shop_address", "bank_account_holder")
    @classmethod
    def clean_required_str(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("This field cannot be empty.")
        return cleaned

    @field_validator("owner_email")
    @classmethod
    def validate_owner_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("Enter a valid business email address.")
        return v

    @field_validator("owner_phone")
    @classmethod
    def validate_owner_phone(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        if len(digits) == 12 and digits.startswith("91"):
            digits = digits[2:]
        if not re.match(r"^[6-9]\d{9}$", digits):
            raise ValueError("Enter a valid 10-digit Indian mobile number.")
        return digits

    @field_validator("pan_number")
    @classmethod
    def validate_pan(cls, v: str) -> str:
        pan = v.strip().upper()
        if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$", pan):
            raise ValueError("Enter a valid 10-character PAN (e.g., ABCDE1234F).")
        return pan

    @field_validator("gstin")
    @classmethod
    def validate_gstin(cls, v: Optional[str]) -> str:
        if not v or not v.strip():
            return ""
        gst = v.strip().upper()
        if not re.match(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$", gst):
            raise ValueError("Enter a valid 15-character GSTIN or leave blank if exempted.")
        return gst

    @field_validator("fssai_license")
    @classmethod
    def validate_fssai(cls, v: Optional[str]) -> str:
        if not v or not v.strip():
            return ""
        digits = re.sub(r"\D", "", v)
        if len(digits) != 14:
            raise ValueError("FSSAI license number must be exactly 14 digits.")
        return digits

    @field_validator("pincode")
    @classmethod
    def validate_shop_pincode(cls, v: str) -> str:
        pin = v.strip()
        if not re.match(r"^[1-9]\d{5}$", pin):
            raise ValueError("Enter a valid 6-digit Indian pincode.")
        return pin

    @field_validator("bank_account_number")
    @classmethod
    def validate_bank_acc(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        if not (9 <= len(digits) <= 18):
            raise ValueError("Bank account number must be 9 to 18 digits.")
        return digits

    @field_validator("bank_ifsc")
    @classmethod
    def validate_ifsc(cls, v: str) -> str:
        ifsc = v.strip().upper()
        if not re.match(r"^[A-Z]{4}0[A-Z0-9]{6}$", ifsc):
            raise ValueError("Enter a valid 11-character IFSC code (e.g., HDFC0001234).")
        return ifsc


class ShopDTO(BaseModel):
    id: int
    user_id: Optional[int] = None
    shop_code: str
    shop_name: str
    owner_name: str
    owner_email: str
    owner_phone: str
    business_type: str
    primary_category: str
    gstin: str
    pan_number: str
    fssai_license: str
    city_id: int
    city_name: str
    shop_address: str
    pincode: str
    pickup_slot: str
    bank_account_holder: str
    bank_account_masked: str
    bank_ifsc: str
    upi_id: str
    shop_description: str
    status: str
    created_at: datetime


class OrderItemDTO(BaseModel):
    product_id: int
    product_name: str
    variant_info: Optional[str] = None
    unit_price: Decimal
    quantity: int
    line_total: Decimal
    shop_id: Optional[int] = None
    shop_name: Optional[str] = None


class SubOrderDTO(BaseModel):
    id: int
    suborder_number: str
    shop_id: int
    shop_name: str
    shop_code: str
    subtotal: Decimal
    status: str
    created_at: datetime
    items: List[OrderItemDTO] = []


class OrderConfirmationDTO(BaseModel):
    order_id: int
    order_number: str
    city_name: str
    customer_name: str
    customer_email: str
    customer_phone: str
    shipping_address: str
    pincode: str
    subtotal_amount: Decimal
    shipping_fee: Decimal
    total_amount: Decimal
    status: str
    created_at: datetime
    items: List[OrderItemDTO]
    suborders: List[SubOrderDTO] = []
    outbox_event_id: Optional[str] = None
