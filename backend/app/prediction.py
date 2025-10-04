from sklearn.linear_model import LinearRegression
import pandas as pd
from datetime import datetime, timedelta
from . import models
from sqlalchemy.orm import Session

def predict_demand(product_id: int, db: Session, days_ahead: int = 30):
    """
    Predice la demanda futura para un producto basado en datos históricos de ventas.
    Usa un modelo de regresión lineal simple.
    """
    # Obtener datos históricos de ventas para el producto
    sales = db.query(models.Sale).filter(models.Sale.product_id == product_id).all()
    
    if len(sales) < 2:
        # Si no hay suficientes datos, devolver una predicción básica
        return {"predicted_demand": 0, "message": "No hay suficientes datos históricos para predicción precisa."}
    
    # Preparar datos para el modelo
    df = pd.DataFrame([{
        'date': sale.sale_date,
        'quantity': sale.quantity
    } for sale in sales])
    
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    df['days_since_start'] = (df['date'] - df['date'].min()).dt.days
    
    # Modelo de regresión lineal
    X = df[['days_since_start']]
    y = df['quantity']
    
    model = LinearRegression()
    model.fit(X, y)
    
    # Predicción para los próximos días
    future_days = (df['days_since_start'].max() + days_ahead)
    predicted_demand = model.predict([[future_days]])[0]
    
    return {
        "predicted_demand": max(0, predicted_demand),  # No permitir valores negativos
        "days_ahead": days_ahead,
        "message": f"Predicción basada en {len(sales)} ventas históricas."
    }