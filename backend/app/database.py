from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Configuración de la base de datos
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db" # Usaremos SQLite por simplicidad inicial

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Modelos de la base de datos
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    price = Column(Float, default=0.0)
    stock = Column(Integer, default=0)
    min_stock = Column(Integer, default=10) # Punto de reorden
    category = Column(String, nullable=True)
    supplier = Column(String, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)

class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, index=True)
    quantity = Column(Integer, default=1)
    sale_date = Column(DateTime, default=datetime.utcnow)
    total_price = Column(Float, default=0.0)

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    phone_number = Column(String, unique=True, index=True)
    loyalty_points = Column(Integer, default=0)
    membership_level = Column(String, default="Bronce")
    last_purchase = Column(DateTime, default=datetime.utcnow)

class SchoolList(Base):
    __tablename__ = "school_lists"

    id = Column(Integer, primary_key=True, index=True)
    school_name = Column(String, index=True)
    grade = Column(String, index=True)
    year = Column(Integer, default=datetime.utcnow().year)
    items = Column(String) # JSON string of items and quantities

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, nullable=True)
    order_type = Column(String) # 'impresion', 'producto', 'lista_escolar'
    status = Column(String, default="Pendiente")
    details = Column(String) # JSON string of order details
    total_amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)

# Función para crear las tablas en la base de datos
def create_db_and_tables():
    Base.metadata.create_all(bind=engine)