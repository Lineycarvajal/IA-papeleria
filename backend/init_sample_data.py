#!/usr/bin/env python3
"""
Script para inicializar datos de muestra en la base de datos
Ejecutar con: python init_sample_data.py
"""

from app.database import SessionLocal, Product, Sale, Customer
from datetime import datetime, timedelta
import random

def init_sample_data():
    """Inicializa datos de muestra para pruebas"""

    db = SessionLocal()
    try:
        # Verificar si ya hay datos
        if db.query(Product).count() > 0:
            print("ADVERTENCIA: La base de datos ya contiene datos. Saltando inicializacion.")
            return

        print("INICIANDO: Inicializando datos de muestra...")

        # Productos de muestra
        sample_products = [
            # Útiles escolares
            {"name": "Cuaderno Norma 100h Ferrocarril", "price": 15000, "stock": 45, "min_stock": 10, "category": "Útiles Escolares", "supplier": "Norma"},
            {"name": "Cuaderno Norma 100h Cuadriculado", "price": 15000, "stock": 32, "min_stock": 8, "category": "Útiles Escolares", "supplier": "Norma"},
            {"name": "Lápiz Mirado #2", "price": 800, "stock": 120, "min_stock": 20, "category": "Útiles Escolares", "supplier": "Mirado"},
            {"name": "Esfero Azul Bic", "price": 1200, "stock": 85, "min_stock": 15, "category": "Útiles Escolares", "supplier": "Bic"},
            {"name": "Esfero Negro Bic", "price": 1200, "stock": 92, "min_stock": 15, "category": "Útiles Escolares", "supplier": "Bic"},
            {"name": "Borrador Milán", "price": 500, "stock": 60, "min_stock": 12, "category": "Útiles Escolares", "supplier": "Milán"},
            {"name": "Sacapuntas Metálico", "price": 2500, "stock": 25, "min_stock": 5, "category": "Útiles Escolares", "supplier": "Maped"},
            {"name": "Regla 30cm", "price": 3500, "stock": 18, "min_stock": 4, "category": "Útiles Escolares", "supplier": "Maped"},
            {"name": "Compás de Precisión", "price": 8500, "stock": 12, "min_stock": 3, "category": "Útiles Escolares", "supplier": "Maped"},
            {"name": "Escuadra 45°", "price": 4200, "stock": 15, "min_stock": 3, "category": "Útiles Escolares", "supplier": "Maped"},

            # Papelería
            {"name": "Resma Papel Carta 75g", "price": 25000, "stock": 8, "min_stock": 3, "category": "Papelería", "supplier": "Panamericana"},
            {"name": "Pegamento en Barra", "price": 1800, "stock": 40, "min_stock": 8, "category": "Útiles Escolares", "supplier": "Pritt"},
            {"name": "Tijeras Escolares", "price": 5500, "stock": 22, "min_stock": 5, "category": "Útiles Escolares", "supplier": "Maped"},
            {"name": "Corrector Líquido", "price": 3200, "stock": 28, "min_stock": 6, "category": "Útiles Escolares", "supplier": "Bic"},

            # Tecnología
            {"name": "Memoria USB 16GB", "price": 25000, "stock": 15, "min_stock": 3, "category": "Tecnología", "supplier": "Kingston"},
            {"name": "Mouse Óptico", "price": 18000, "stock": 12, "min_stock": 2, "category": "Tecnología", "supplier": "Logitech"},
            {"name": "Teclado USB", "price": 35000, "stock": 8, "min_stock": 2, "category": "Tecnología", "supplier": "Logitech"},

            # Artículos varios
            {"name": "Mochila Escolar Grande", "price": 65000, "stock": 6, "min_stock": 2, "category": "Accesorios", "supplier": "JanSport"},
            {"name": "Maletín de Geometría", "price": 28000, "stock": 10, "min_stock": 2, "category": "Accesorios", "supplier": "Maped"},
        ]

        # Agregar productos
        for product_data in sample_products:
            product = Product(**product_data)
            db.add(product)

        print(f"EXITO: Agregados {len(sample_products)} productos de muestra")

        # Clientes de muestra
        sample_customers = [
            {"name": "María González", "phone_number": "+573001234567", "loyalty_points": 450, "membership_level": "Plata"},
            {"name": "Carlos Rodríguez", "phone_number": "+573007654321", "loyalty_points": 120, "membership_level": "Bronce"},
            {"name": "Ana López", "phone_number": "+573005556667", "loyalty_points": 780, "membership_level": "Oro"},
        ]

        for customer_data in sample_customers:
            customer = Customer(**customer_data)
            db.add(customer)

        print(f"EXITO: Agregados {len(sample_customers)} clientes de muestra")

        # Ventas de muestra (últimos 30 días)
        base_date = datetime.now()
        products_ids = [i+1 for i in range(len(sample_products))]

        for i in range(50):  # 50 ventas aleatorias
            days_ago = random.randint(0, 30)
            sale_date = base_date - timedelta(days=days_ago)

            sale = Sale(
                product_id=random.choice(products_ids),
                quantity=random.randint(1, 5),
                sale_date=sale_date,
                total_price=random.randint(1000, 50000)
            )
            db.add(sale)

        print("EXITO: Agregadas 50 ventas de muestra")

        # Confirmar cambios
        db.commit()
        print("FELICITACIONES: Datos de muestra inicializados exitosamente!")
        print("\nCONSEJO: Ahora puedes probar el chatbot preguntando:")
        print("   - '¿Tienen cuadernos?'")
        print("   - 'Stock de lápices'")
        print("   - 'Vendi 3 esferos'")
        print("   - 'productos con poco stock'")

    except Exception as e:
        print(f"ERROR: Error inicializando datos: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_sample_data()