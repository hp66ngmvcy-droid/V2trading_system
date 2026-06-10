"""Invoice Calculator - Core business logic"""

from typing import List, Optional
from dataclasses import dataclass
from enum import Enum


class PaymentStatus(Enum):
    PAID = "Paid"
    UNPAID = "Unpaid"


@dataclass
class Product:
    name: str
    unit_price: float
    quantity: int
    warranty_months: int = 0
    tax_rate: float = 0.0
    
    @property
    def total_base_price(self) -> float:
        return self.unit_price * self.quantity
    
    @property
    def total_tax(self) -> float:
        return self.total_base_price * self.tax_rate
    
    @property
    def total_with_tax(self) -> float:
        return self.total_base_price + self.total_tax


@dataclass
class Participant:
    name: str
    address: str
    phone: str
    email: Optional[str] = None


@dataclass
class InvoiceInfo:
    title: str
    invoice_id: str
    issue_date: str
    status: PaymentStatus = PaymentStatus.UNPAID


class InvoiceCalculator:
    
    @staticmethod
    def calculate_invoice(
        products: List[Product],
        service_charge: float = 0,
        discount: float = 0
    ) -> dict:
        subtotal = sum(p.total_base_price for p in products)
        tax = sum(p.total_tax for p in products)
        total = subtotal + tax + service_charge - discount
        
        return {
            "subtotal": subtotal,
            "tax": tax,
            "service_charge": service_charge,
            "discount": discount,
            "total": total
        }
    
    @staticmethod
    def generate_line_items(products: List[Product]) -> List[dict]:
        return [
            {
                "name": p.name,
                "unit_price": p.unit_price,
                "quantity": p.quantity,
                "base_total": p.total_base_price,
                "tax_rate": p.tax_rate,
                "tax": p.total_tax,
                "total": p.total_with_tax
            }
            for p in products
        ]


class InvoiceBuilder:
    
    def __init__(self):
        self.invoice_info = None
        self.company = None
        self.customer = None
        self.products = []
        self.service_charge = 0
        self.discount = 0
    
    def set_invoice_info(self, info: InvoiceInfo):
        self.invoice_info = info
        return self
    
    def set_company(self, company: Participant):
        self.company = company
        return self
    
    def set_customer(self, customer: Participant):
        self.customer = customer
        return self
    
    def add_product(self, product: Product):
        self.products.append(product)
        return self
    
    def set_service_charge(self, amount: float):
        self.service_charge = amount
        return self
    
    def set_discount(self, amount: float):
        self.discount = amount
        return self
    
    def build(self) -> dict:
        calculator = InvoiceCalculator()
        totals = calculator.calculate_invoice(self.products, self.service_charge, self.discount)
        
        return {
            "invoice": self.invoice_info.__dict__ if self.invoice_info else {},
            "company": self.company.__dict__ if self.company else {},
            "customer": self.customer.__dict__ if self.customer else {},
            "line_items": calculator.generate_line_items(self.products),
            "totals": totals
        }
