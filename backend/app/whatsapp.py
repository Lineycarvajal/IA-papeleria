from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from . import models, schemas, database
from .prediction import predict_demand
from datetime import datetime
import json

router = APIRouter()

# Simulación de recepción de mensajes de WhatsApp
@router.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request, db: Session = Depends(database.SessionLocal)):
    data = await request.json()

    # Simular mensaje de WhatsApp
    message = data.get("message", "")
    sender = data.get("sender", "")

    # Procesar el mensaje (lógica básica)
    response = process_message(message, sender, db)

    return {"response": response}

def process_message(message: str, sender: str, db: Session):
    message = message.lower()
    
    if "disponibilidad" in message or "tienen" in message:
        # Buscar productos
        products = db.query(models.Product).filter(models.Product.stock > 0).all()
        product_list = [f"{p.name}: {p.stock} unidades" for p in products[:5]]
        return f"Productos disponibles: {', '.join(product_list)}"
    
    elif "venta" in message or "vendí" in message:
        # Registrar venta (simplificado)
        # Aquí se debería parsear el mensaje para extraer producto y cantidad
        return "Venta registrada. ¿Necesitas algo más?"
    
    elif "predicción" in message or "demanda" in message:
        # Obtener predicción para un producto (ejemplo)
        product = db.query(models.Product).first()
        if product:
            prediction = predict_demand(product.id, db, 30)
            return f"Predicción para {product.name}: {prediction['predicted_demand']} unidades en 30 días."
        return "No hay productos para predecir."
    
    else:
        return "¡Hola! Soy PapelBot. ¿En qué puedo ayudarte? Puedo informarte sobre disponibilidad, registrar ventas o dar predicciones de demanda."