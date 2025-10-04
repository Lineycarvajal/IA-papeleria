#!/usr/bin/env python3
"""
Script para probar las APIs de IA integradas
Ejecutar con: python test_ai_api.py
"""

import os
from app.ai_api import ai_client

def test_ai_apis():
    """Prueba todas las APIs de IA disponibles"""

    print("🤖 Probando APIs de IA para PapelBot\n")
    print("=" * 50)

    # Verificar qué APIs están disponibles
    available_providers = ai_client.get_available_providers()
    print("📊 Estado de APIs:")
    for provider, available in available_providers.items():
        status = "✅ Disponible" if available else "❌ No configurada"
        print(f"  {provider.upper()}: {status}")
    print()

    if not any(available_providers.values()):
        print("❌ Ninguna API de IA configurada.")
        print("Para probar las APIs, configura las claves en el archivo .env")
        print("Ejemplo:")
        print("  OPENAI_API_KEY=tu_clave_openai")
        print("  GROK_API_KEY=tu_clave_grok")
        print("  ANTHROPIC_API_KEY=tu_clave_anthropic")
        return

    # Preguntas de prueba
    test_questions = [
        "¿Qué productos recomiendas para un estudiante de secundaria?",
        "¿Cómo puedo organizar mejor mi papelería?",
        "¿Qué estrategias de venta funcionan mejor en temporada escolar?",
        "Explica el programa de fidelización de la papelería",
        "¿Qué consejos das para manejar inventario en una papelería?"
    ]

    # Contexto de la papelería
    context = """
    Papelería Inteligente Andes - Información del negocio:
    - Ubicación: Andes, Antioquia, Colombia
    - Especialidad: Artículos escolares, útiles de oficina, tecnología básica
    - Servicios: Fotocopias, impresiones, anillados, plastificados
    - Clientes principales: Estudiantes, instituciones educativas, comunidad local
    - Temporada alta: Inicio de año escolar (enero-febrero), junio-julio
    - Temporada baja: Diciembre, vacaciones

    Productos principales: Cuadernos, lápices, esferos, borradores, reglas, compases, papel, carpetas, tecnología básica.

    Información actual del sistema:
    - Total productos: 25
    - Productos con stock bajo: 3
    - Total ventas hoy: $150.000
    """

    print("🧪 Probando respuestas de IA:")
    print("-" * 50)

    for i, question in enumerate(test_questions, 1):
        print(f"\n❓ Pregunta {i}: {question}")

        try:
            response = ai_client.ask_ai(question, context, max_tokens=200)
            if response:
                print(f"🤖 Respuesta: {response[:150]}..." if len(response) > 150 else f"🤖 Respuesta: {response}")
            else:
                print("❌ Error: No se pudo obtener respuesta")
        except Exception as e:
            print(f"❌ Error: {str(e)}")

        print("-" * 30)

    print("\n✅ Pruebas completadas!")

if __name__ == "__main__":
    test_ai_apis()