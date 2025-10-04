from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas, database
from .prediction import predict_demand
from .whatsapp import router as whatsapp_router

app = FastAPI()

# Incluir routers
app.include_router(whatsapp_router)

# Dependency para obtener la sesión de la base de datos
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def on_startup():
    database.create_db_and_tables()

@app.get("/")
def read_root():
    return {"message": "Bienvenido al Agente de Gestión Inteligente para Papelerías"}

# Endpoints CRUD para productos
@app.post("/products/", response_model=schemas.Product, status_code=status.HTTP_201_CREATED)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    db_product = models.Product(
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock,
        min_stock=product.min_stock,
        category=product.category,
        supplier=product.supplier
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/products/", response_model=List[schemas.Product])
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    products = db.query(models.Product).offset(skip).limit(limit).all()
    return products

@app.get("/products/{product_id}", response_model=schemas.Product)
def read_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product

@app.put("/products/{product_id}", response_model=schemas.Product)
def update_product(product_id: int, product: schemas.ProductCreate, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    for key, value in product.model_dump().items():
        setattr(db_product, key, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/products/low-stock/", response_model=List[schemas.Product])
def get_low_stock_products(db: Session = Depends(get_db)):
    low_stock_products = db.query(models.Product).filter(models.Product.stock < models.Product.min_stock).all()
    return low_stock_products

@app.get("/products/low-rotation/", response_model=List[schemas.Product])
def get_low_rotation_products(db: Session = Depends(get_db)):
    sixty_days_ago = datetime.utcnow() - timedelta(days=60)
    
    # Subconsulta para obtener los product_id que han tenido ventas en los últimos 60 días
    recent_sales_product_ids = db.query(models.Sale.product_id).filter(
        models.Sale.sale_date >= sixty_days_ago
    ).distinct().subquery()

    # Productos que no están en la lista de productos con ventas recientes
    low_rotation_products = db.query(models.Product).filter(
        ~models.Product.id.in_(recent_sales_product_ids)
    ).all()
    
    return low_rotation_products

@app.get("/products/{product_id}/reorder-suggestion", response_model=dict)
def get_reorder_suggestion(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    suggested_quantity = 0
    if product.stock < product.min_stock:
        suggested_quantity = product.min_stock * 2 # Simple heuristic for now

    return {
        "product_id": product.id,
        "product_name": product.name,
        "current_stock": product.stock,
        "min_stock": product.min_stock,
        "suggested_reorder_quantity": suggested_quantity,
        "message": "Cantidad sugerida basada en el doble del stock mínimo si el stock actual es bajo."
    }

@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    db.delete(db_product)
    db.commit()
    return {"message": "Producto eliminado exitosamente"}

@app.post("/products/{product_id}/stock", response_model=schemas.Product)
def update_product_stock(product_id: int, stock_update: schemas.ProductUpdateStock, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    if stock_update.operation == "add":
        db_product.stock += stock_update.quantity
    elif stock_update.operation == "subtract":
        if db_product.stock < stock_update.quantity:
            raise HTTPException(status_code=400, detail="No hay suficiente stock para esta operación")
        db_product.stock -= stock_update.quantity
    else:
        raise HTTPException(status_code=400, detail="Operación de stock no válida. Use 'add' o 'subtract'.")
    
    db_product.last_updated = datetime.utcnow()
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/products/{product_id}/demand-prediction", response_model=dict)
def get_demand_prediction(product_id: int, days_ahead: int = 30, db: Session = Depends(get_db)):
    prediction = predict_demand(product_id, db, days_ahead)
    return prediction

@app.get("/products/demand-alerts", response_model=List[dict])
def get_demand_alerts(db: Session = Depends(get_db)):
    products = db.query(models.Product).all()
    alerts = []
    
    for product in products:
        prediction = predict_demand(product.id, db, 30)
        predicted_demand = prediction.get("predicted_demand", 0)
        
        if predicted_demand > product.stock:
            alerts.append({
                "product_id": product.id,
                "product_name": product.name,
                "current_stock": product.stock,
                "predicted_demand": predicted_demand,
                "alert_type": "Demanda alta prevista",
                "message": f"Se espera vender {predicted_demand} unidades en los próximos 30 días, pero solo hay {product.stock} en stock."
            })
    
    return alerts