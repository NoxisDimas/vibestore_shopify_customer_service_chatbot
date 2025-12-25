from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any

class ProductResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    price_amount: float
    price_currency: str
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    variants: List[Dict[str, Any]] = []

class TrackingInfo(BaseModel):
    number: Optional[str] = None
    url: Optional[str] = None
    company: Optional[str] = None

class Fulfillment(BaseModel):
    status: Optional[str] = None
    tracking_info: List[TrackingInfo] = []

class LineItem(BaseModel):
    title: str
    quantity: int
    amount: float
    currency: str

class OrderResponse(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    total_price: float
    currency: str

    # line_items fields
    line_items: List[LineItem] = []

    # optional fulfillment&financial (ditampilkan)
    display_fulfillment_status: Optional[str] = None
    display_financial_status: Optional[str] = None

    # detail fulfillments
    fulfillments: List[Fulfillment] = []

class PolicyItem(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    url: Optional[str] = None

class PolicyResponse(BaseModel):
    privacyPolicy: Optional[PolicyItem] = PolicyItem()
    termsOfService: Optional[PolicyItem] = PolicyItem()
    refundPolicy: Optional[PolicyItem] = PolicyItem()
    shippingPolicy: Optional[PolicyItem] = PolicyItem()


class ShopPrimaryDomain(BaseModel):
    host: Optional[str]


class ShopBillingAddress(BaseModel):
    address1: Optional[str]
    address2: Optional[str]
    city: Optional[str]
    province: Optional[str]
    country: Optional[str]
    zip: Optional[str]
    phone: Optional[str]


class ShopInfo(BaseModel):
    name: Optional[str]
    email: Optional[str]
    myshopifyDomain: Optional[str]
    contactEmail: Optional[str]
    primaryDomain: Optional[ShopPrimaryDomain]
