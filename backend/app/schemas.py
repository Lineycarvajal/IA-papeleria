from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock: int
    min_stock: int
    category: Optional[str] = None
    supplier: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    last_updated: datetime

    class Config:
        from_attributes = True

class ProductUpdateStock(BaseModel):
    quantity: int
    operation: str # "add" or "subtract"

class SaleBase(BaseModel):
    product_id: int
    quantity: int
    total_price: float

class SaleCreate(SaleBase):
    pass

class Sale(SaleBase):
    id: int
    sale_date: datetime

    class Config:
        from_attributes = True

class CustomerBase(BaseModel):
    name: str
    phone_number: str
    loyalty_points: int = 0
    membership_level: str = "Bronce"

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    id: int
    last_purchase: datetime

    class Config:
        from_attributes = True

class SchoolListBase(BaseModel):
    school_name: str
    grade: str
    year: int
    items: str # JSON string

class SchoolListCreate(SchoolListBase):
    pass

class SchoolList(SchoolListBase):
    id: int

    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    customer_id: Optional[int] = None
    order_type: str
    status: str = "Pendiente"
    details: str # JSON string
    total_amount: float
    due_date: Optional[datetime] = None

class OrderCreate(OrderBase):
    pass

class Order(OrderBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True