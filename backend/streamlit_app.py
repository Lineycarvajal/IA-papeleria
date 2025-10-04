import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import SessionLocal, Product, Sale, Customer
from app.prediction import predict_demand
from app.ai_api import ai_client
from datetime import datetime, timezone

# Configuración de la página
st.set_page_config(
    page_title="Agente de Gestión Inteligente para Papelerías",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Agente de Gestión Inteligente para Papelerías")
st.markdown("Sistema inteligente para optimizar la gestión de papelerías en Andes, Antioquia")

# Logo de la Papelería
st.markdown("""
<div style="text-align: center; margin: 20px 0;">
    <h2 style="color: #FF6B35; font-size: 2.5em;">📚 Papelería Inteligente Andes</h2>
    <p style="font-size: 1.2em; color: #666;">Centro de Suministros Escolares</p>
    <div style="font-size: 4em;">🏫✏️📝</div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Función para obtener sesión de BD
def get_db():
    return SessionLocal()

# Sidebar con navegación
st.sidebar.title("📋 Menú Principal")
page = st.sidebar.radio(
    "Selecciona una opción:",
    ["🏠 Dashboard", "📦 Inventario", "📊 Predicciones", "💬 Chatbot Inteligente", "⚠️ Alertas"]
)

# Dashboard principal
if page == "🏠 Dashboard":
    st.header("🏠 Dashboard Principal")

    db = get_db()
    try:
        # Estadísticas generales
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_products = db.query(Product).count()
            st.metric("Total Productos", total_products)

        with col2:
            total_stock = db.query(func.sum(Product.stock)).scalar() or 0
            st.metric("Stock Total", int(total_stock))

        with col3:
            low_stock = db.query(Product).filter(Product.stock < Product.min_stock).count()
            st.metric("Productos con Stock Bajo", low_stock)

        with col4:
            total_sales = db.query(Sale).count()
            st.metric("Total Ventas", total_sales)

        # Productos más vendidos (últimos 30 días)
        st.subheader("📈 Productos Más Vendidos (Últimos 30 días)")
        thirty_days_ago = datetime.now(timezone.utc) - pd.Timedelta(days=30)

        sales_data = db.query(
            Product.name,
            func.sum(Sale.quantity).label('total_quantity')
        ).join(Sale, Product.id == Sale.product_id).filter(
            Sale.sale_date >= thirty_days_ago
        ).group_by(Product.id).order_by(func.sum(Sale.quantity).desc()).limit(10).all()

        if sales_data:
            df_sales = pd.DataFrame(sales_data, columns=['Producto', 'Cantidad Vendida'])
            st.bar_chart(df_sales.set_index('Producto'))
        else:
            st.info("No hay datos de ventas recientes")

    finally:
        db.close()

# Gestión de Inventario
elif page == "📦 Inventario":
    st.header("📦 Gestión de Inventario")

    db = get_db()
    try:
        # Lista de productos
        st.subheader("Lista de Productos")
        products = db.query(Product).all()

        if products:
            df_products = pd.DataFrame([{
                'ID': p.id,
                'Nombre': p.name,
                'Precio': f"${p.price:,.0f}",
                'Stock': p.stock,
                'Stock Mínimo': p.min_stock,
                'Categoría': p.category or 'N/A',
                'Proveedor': p.supplier or 'N/A'
            } for p in products])

            st.dataframe(df_products, width='stretch')

            # Agregar nuevo producto
            st.subheader("➕ Agregar Nuevo Producto")
            with st.form("new_product"):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("Nombre del producto")
                    price = st.number_input("Precio", min_value=0.0, step=0.01)
                    stock = st.number_input("Stock inicial", min_value=0, step=1)
                with col2:
                    min_stock = st.number_input("Stock mínimo", min_value=0, step=1)
                    category = st.text_input("Categoría")
                    supplier = st.text_input("Proveedor")

                submitted = st.form_submit_button("Agregar Producto")
                if submitted and name:
                    # Verificar si el producto ya existe
                    existing_product = db.query(Product).filter(Product.name == name).first()
                    if existing_product:
                        st.error(f"El producto '{name}' ya existe en el inventario.")
                    else:
                        new_product = Product(
                            name=name,
                            price=price,
                            stock=stock,
                            min_stock=min_stock,
                            category=category if category else None,
                            supplier=supplier if supplier else None
                        )
                        db.add(new_product)
                        db.commit()
                        st.success("Producto agregado exitosamente!")
                        st.rerun()
        else:
            st.info("No hay productos registrados. Agrega el primero!")

    finally:
        db.close()

# Predicciones de Demanda
elif page == "📊 Predicciones":
    st.header("📊 Predicciones de Demanda")

    db = get_db()
    try:
        products = db.query(Product).all()

        if products:
            product_names = {p.id: p.name for p in products}
            selected_product = st.selectbox(
                "Selecciona un producto para predecir demanda:",
                options=list(product_names.keys()),
                format_func=lambda x: product_names[x]
            )

            if selected_product:
                days_ahead = st.slider("Días hacia adelante", 7, 90, 30)

                if st.button("Generar Predicción"):
                    prediction = predict_demand(selected_product, db, days_ahead)

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Demanda Predicha", f"{prediction['predicted_demand']:.1f} unidades")
                    with col2:
                        st.metric("Período", f"{days_ahead} días")
                    with col3:
                        st.metric("Confianza", prediction.get('message', 'N/A'))

                    # Mostrar datos históricos si existen
                    sales = db.query(Sale).filter(Sale.product_id == selected_product).order_by(Sale.sale_date).all()
                    if sales:
                        st.subheader("📈 Historial de Ventas")
                        df_history = pd.DataFrame([{
                            'Fecha': s.sale_date.strftime('%Y-%m-%d'),
                            'Cantidad': s.quantity
                        } for s in sales])

                        st.line_chart(df_history.set_index('Fecha'))
        else:
            st.warning("No hay productos registrados para hacer predicciones")

    finally:
        db.close()

# Chatbot Inteligente Interno
elif page == "💬 Chatbot Inteligente":
    st.header("💬 Chatbot Inteligente PapelBot")

    # Información de comandos disponibles
    with st.expander("📋 Comandos Disponibles"):
        st.markdown("""
        **Consultas de Inventario:**
        - "¿Tienen [producto]?" - Verificar disponibilidad
        - "Stock de [producto]" - Ver cantidad disponible
        - "Productos con poco stock" - Ver alertas de inventario

        **Gestión de Ventas:**
        - "Vendi [cantidad] [producto]" - Registrar venta
        - "Venta de [producto] hoy" - Ver ventas del día

        **Predicciones:**
        - "Predice demanda de [producto]" - Predecir demanda futura
        - "Alertas de demanda" - Ver productos con demanda alta

        **Información General:**
        - "Hola" o "Buenos días" - Saludo
        - "Horarios" - Información de atención
        - "Ubicación" - Dirección de la papelería
        - "Ayuda" - Ver comandos disponibles
        """)

    # Estado de APIs de IA
    with st.expander("🤖 Estado de APIs de IA"):
        available_providers = ai_client.get_available_providers()
        st.markdown("**Proveedores de IA disponibles:**")

        col1, col2, col3 = st.columns(3)
        with col1:
            if available_providers.get('openai', False):
                st.success("✅ OpenAI GPT")
            else:
                st.warning("❌ OpenAI GPT (configurar OPENAI_API_KEY)")

        with col2:
            if available_providers.get('grok', False):
                st.success("✅ Grok (xAI)")
            else:
                st.warning("❌ Grok (configurar GROK_API_KEY)")

        with col3:
            if available_providers.get('anthropic', False):
                st.success("✅ Claude (Anthropic)")
            else:
                st.warning("❌ Claude (configurar ANTHROPIC_API_KEY)")

        if not any(available_providers.values()):
            st.error("⚠️ **Ninguna API de IA configurada.** El chatbot solo responderá consultas básicas.")
            st.info("Para habilitar respuestas inteligentes, configura al menos una API en el archivo `.env`")
        else:
            st.info("🎉 **Chatbot con IA habilitado!** Puede responder preguntas generales y complejas.")

    # Simular conversación
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # Mostrar historial de chat
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history[-20:]:  # Mostrar últimas 20 mensajes
            if message['sender'] == 'user':
                st.markdown(f"**👤 Tú:** {message['text']}")
            else:
                st.markdown(f"**🤖 PapelBot:** {message['text']}")

    # Función para procesar mensajes del chatbot interno
    def process_internal_message(message, db):
        message = message.lower().strip()

        # Saludos
        if any(word in message for word in ['hola', 'buenos días', 'buenas tardes', 'buenas noches', 'saludos']):
            return "¡Hola! 👋 Soy PapelBot, tu asistente inteligente de la Papelería Andes. ¿En qué puedo ayudarte hoy?\n\n💡 Escribe 'ayuda' para ver todos los comandos disponibles."

        # Ayuda
        if 'ayuda' in message or 'comandos' in message:
            return """📋 **COMANDOS DISPONIBLES:**

**🏪 Consultas de Inventario:**
• "¿Tienen cuadernos?" - Verificar disponibilidad
• "Stock de lápices" - Ver cantidad disponible
• "Productos con poco stock" - Ver alertas

**💰 Gestión de Ventas:**
• "Vendi 5 cuadernos" - Registrar venta
• "Venta de esferos hoy" - Ver ventas del día

**🔮 Predicciones:**
• "Predice demanda de cuadernos" - Predecir demanda
• "Alertas de demanda" - Ver productos críticos

**ℹ️ Información General:**
• "Horarios" - Horario de atención
• "Ubicación" - Dirección de la papelería
• "Precios" - Información de precios"""

        # Horarios
        if 'horario' in message or 'hora' in message:
            return "🕐 **HORARIOS DE ATENCIÓN:**\n\n• Lunes a Viernes: 7:00 AM - 6:00 PM\n• Sábados: 8:00 AM - 4:00 PM\n• Domingos: 9:00 AM - 2:00 PM\n\n📍 Ubicados en el centro de Andes, Antioquia"

        # Ubicación
        if 'ubicacion' in message or 'direccion' in message or 'donde' in message:
            return "📍 **UBICACIÓN:**\n\nPapelería Inteligente Andes\nCarrera 5 # 8-45, Centro\nAndes, Antioquia, Colombia\n\n📞 Teléfono: (604) 855-1234\n📧 Email: info@papeleriaandes.com"

        # Consultas de disponibilidad - Mejorado con IA
        if 'tienen' in message or 'hay' in message or 'disponible' in message:
            # Primero intentar con lógica local mejorada
            all_products = db.query(Product).all()
            found_products = []

            # Buscar productos con mejor coincidencia
            message_lower = message.lower()
            for product in all_products:
                product_lower = product.name.lower()
                # Coincidencia exacta o parcial
                if product_lower in message_lower or any(word in product_lower for word in message_lower.split()):
                    found_products.append(product)

            # Si no encontró productos específicos, buscar por categorías comunes
            if not found_products:
                category_keywords = {
                    'cuaderno': ['cuaderno', 'cuadernos', 'libreta', 'libretas'],
                    'lapiz': ['lápiz', 'lapices', 'lápices', 'pencil'],
                    'esfero': ['esfero', 'esferos', 'bolígrafo', 'bolígrafos', 'pluma'],
                    'borrador': ['borrador', 'borradores', 'goma'],
                    'regla': ['regla', 'reglas', 'escuadra'],
                    'papel': ['papel', 'resma', 'hojas'],
                    'mochila': ['mochila', 'maletín', 'maletin'],
                    'pegamento': ['pegamento', 'cola', 'glue']
                }

                for category, keywords in category_keywords.items():
                    if any(keyword in message_lower for keyword in keywords):
                        # Buscar productos que contengan la categoría
                        for product in all_products:
                            if category in product.name.lower() or category in (product.category or '').lower():
                                found_products.append(product)
                        break

            if found_products:
                # Si encontró productos, mostrar el más relevante
                product = found_products[0]  # Tomar el primero encontrado
                if product.stock > 0:
                    return f"✅ **SÍ TENEMOS {product.name.upper()}**\n\n📦 Stock disponible: {product.stock} unidades\n💰 Precio: ${product.price:,.0f}\n🏷️ Categoría: {product.category or 'General'}"
                else:
                    return f"❌ **NO HAY STOCK** de {product.name}\n\n📅 Fecha estimada de llegada: Consultar con proveedor\n💡 ¿Te gustaría que te avise cuando llegue?"
            else:
                # Si no encontró con lógica local, usar IA con contexto completo
                products_list = "\n".join([f"- {p.name} (${p.price:,.0f}, stock: {p.stock})" for p in all_products[:20]])  # Primeros 20 productos

                ai_context = f"""
Papelería Inteligente Andes - Catálogo de Productos Disponibles:
{products_list}

Instrucciones específicas:
- Si el usuario pregunta por un producto, busca en la lista de arriba
- Si no está en la lista, sugiere alternativas similares
- Sé específico con precios y stock disponible
- Si no hay stock, sugiere cuándo podría llegar
"""

                ai_response = ai_client.ask_ai(f"Usuario pregunta: '{message}'. Basándote en nuestro catálogo, ¿tenemos este producto?", ai_context, max_tokens=200)
                if ai_response:
                    return f"🤖 **Respuesta Inteligente:** {ai_response}\n\n💡 *Respuesta generada con IA basada en nuestro catálogo*"
                else:
                    return "🤔 No pude identificar qué producto buscas. ¿Podrías mencionar el nombre específico? (ej: '¿Tienen cuadernos?')"

        # Consultas de stock
        if 'stock' in message:
            if 'poco' in message or 'bajo' in message:
                low_stock_products = db.query(Product).filter(Product.stock < Product.min_stock).all()
                if low_stock_products:
                    response = "⚠️ **PRODUCTOS CON STOCK BAJO:**\n\n"
                    for product in low_stock_products[:5]:  # Máximo 5 productos
                        response += f"• {product.name}: {product.stock}/{product.min_stock} unidades\n"
                    response += "\n📞 Recomiendo contactar al proveedor para reabastecer."
                    return response
                else:
                    return "✅ **EXCELENTE:** Todos los productos tienen stock suficiente. ¡Ninguna alerta de inventario!"
            else:
                # Buscar producto específico
                for product in db.query(Product).all():
                    if product.name.lower() in message:
                        return f"📊 **STOCK DE {product.name.upper()}:**\n\n📦 Unidades disponibles: {product.stock}\n🎯 Stock mínimo: {product.min_stock}\n📈 Estado: {'✅ Suficiente' if product.stock >= product.min_stock else '⚠️ Bajo'}"

                return "🤔 ¿De qué producto quieres saber el stock? (ej: 'Stock de cuadernos')"

        # Registrar ventas
        if 'vendi' in message or 'vendí' in message:
            try:
                # Extraer cantidad y producto
                words = message.split()
                quantity = None
                product_name = None

                for i, word in enumerate(words):
                    if word.isdigit():
                        quantity = int(word)
                        # El siguiente texto debería ser el producto
                        product_name = ' '.join(words[i+1:])
                        break

                if quantity and product_name:
                    product = db.query(Product).filter(Product.name.ilike(f'%{product_name}%')).first()
                    if product:
                        if product.stock >= quantity:
                            # Registrar venta
                            sale = Sale(
                                product_id=product.id,
                                quantity=quantity,
                                total_price=product.price * quantity
                            )
                            db.add(sale)
                            product.stock -= quantity
                            db.commit()

                            return f"✅ **VENTA REGISTRADA**\n\n📦 Producto: {product.name}\n🔢 Cantidad: {quantity} unidades\n💰 Total: ${product.price * quantity:,.0f}\n📊 Stock restante: {product.stock} unidades"
                        else:
                            return f"❌ **STOCK INSUFICIENTE**\n\n📦 {product.name} tiene solo {product.stock} unidades disponibles\n💡 No se puede vender {quantity} unidades."
                    else:
                        return f"❓ No encontré el producto '{product_name}' en el catálogo."
                else:
                    return "🤔 Formato incorrecto. Usa: 'Vendi [cantidad] [producto]' (ej: 'Vendi 3 cuadernos')"
            except Exception as e:
                return f"❌ Error al procesar la venta: {str(e)}\n\n💡 Formato correcto: 'Vendi [cantidad] [producto]'"

        # Predicciones de demanda
        if 'predic' in message or 'demanda' in message:
            if 'alertas' in message:
                # Mostrar productos con demanda crítica
                products = db.query(Product).all()
                alerts = []

                for product in products:
                    prediction = predict_demand(product.id, db, 30)
                    predicted_demand = prediction.get("predicted_demand", 0)

                    if predicted_demand > product.stock:
                        alerts.append({
                            'name': product.name,
                            'stock': product.stock,
                            'predicted': predicted_demand
                        })

                if alerts:
                    response = "🚨 **ALERTAS DE DEMANDA CRÍTICA:**\n\n"
                    for alert in alerts[:5]:
                        response += f"• {alert['name']}: Stock {alert['stock']} vs Demanda {alert['predicted']:.1f}\n"
                    response += "\n📞 Recomiendo reabastecer estos productos urgentemente."
                    return response
                else:
                    return "✅ **SIN ALERTAS:** Todos los productos tienen stock suficiente para la demanda predicha."
            else:
                # Predicción específica
                for product in db.query(Product).all():
                    if product.name.lower() in message:
                        prediction = predict_demand(product.id, db, 30)
                        predicted_demand = prediction.get("predicted_demand", 0)

                        return f"🔮 **PREDICCIÓN DE DEMANDA**\n\n📦 Producto: {product.name}\n📊 Demanda predicha (30 días): {predicted_demand:.1f} unidades\n📦 Stock actual: {product.stock}\n⚠️ Estado: {'✅ Suficiente' if product.stock >= predicted_demand else '🚨 Reabastecer'}"

                return "🤔 ¿De qué producto quieres la predicción? (ej: 'Predice demanda de cuadernos')"

        # Ventas del día
        if 'venta' in message and 'hoy' in message:
            today = datetime.now(timezone.utc).date()
            today_sales = db.query(func.sum(Sale.total_price)).filter(
                func.date(Sale.sale_date) == today
            ).scalar() or 0

            sales_count = db.query(func.count(Sale.id)).filter(
                func.date(Sale.sale_date) == today
            ).scalar() or 0

            return f"💰 **VENTAS DE HOY**\n\n📊 Número de ventas: {sales_count}\n💵 Total vendido: ${today_sales:,.0f}\n📈 Promedio por venta: ${today_sales/sales_count if sales_count > 0 else 0:,.0f}"

        # Si no pudo responder con lógica local, intentar con IA con contexto completo
        all_products = db.query(Product).all()
        products_catalog = "\n".join([f"- {p.name}: ${p.price:,.0f} (stock: {p.stock})" for p in all_products])

        recent_sales = db.query(Sale).order_by(Sale.sale_date.desc()).limit(5).all()
        sales_summary = "\n".join([f"- {s.quantity} x Producto ID {s.product_id}: ${s.total_price:,.0f}" for s in recent_sales])

        context = f"""
PAPELERÍA INTELIGENTE ANDES - CONTEXTO COMPLETO:

📍 INFORMACIÓN DEL NEGOCIO:
- Ubicación: Andes, Antioquia, Colombia
- Especialidad: Artículos escolares, útiles de oficina, tecnología básica
- Servicios: Fotocopias, impresiones, anillados, plastificados
- Clientes: Estudiantes, instituciones educativas, comunidad local
- Temporada alta: Inicio de año escolar (enero-febrero), junio-julio

🏪 CATÁLOGO COMPLETO DE PRODUCTOS:
{products_catalog}

📊 INFORMACIÓN ACTUAL DEL SISTEMA:
- Total productos registrados: {len(all_products)}
- Productos con stock bajo: {len([p for p in all_products if p.stock < p.min_stock])}
- Ventas recientes: {sales_summary}
- Total ventas hoy: ${db.query(func.sum(Sale.total_price)).filter(func.date(Sale.sale_date) == datetime.now(timezone.utc).date()).scalar() or 0:,.0f}

🎯 INSTRUCCIONES PARA RESPONDER:
- Si preguntan por productos, busca en el catálogo de arriba
- Sé específico con precios y stock disponible
- Para consultas generales, usa el contexto del negocio
- Mantén respuestas útiles y amigables
- Si no sabes algo específico, admítelo y sugiere alternativas
"""

        ai_response = ai_client.ask_ai(f"Pregunta del cliente: '{question}'", context, max_tokens=400)
        if ai_response:
            return f"🤖 **PapelBot IA:** {ai_response}\n\n💡 *Respuesta inteligente generada con IA*"
        else:
            return "🤔 Lo siento, no pude procesar tu consulta. ¿Podrías intentar con un comando específico como 'ayuda' o reformular tu pregunta?"

    # Input para nuevo mensaje
    col1, col2 = st.columns([4, 1])
    with col1:
        user_message = st.text_input("Escribe tu mensaje a PapelBot:", key="user_input", placeholder="Ej: ¿Tienen cuadernos?")
    with col2:
        send_button = st.button("📤 Enviar", use_container_width=True)

    if send_button and user_message:
        # Agregar mensaje del usuario
        st.session_state.chat_history.append({'sender': 'user', 'text': user_message})

        # Generar respuesta del bot
        db = get_db()
        try:
            bot_response = process_internal_message(user_message, db)
            st.session_state.chat_history.append({'sender': 'bot', 'text': bot_response})
        finally:
            db.close()

        st.rerun()

    # Botones rápidos para comandos comunes
    st.markdown("---")
    st.markdown("### 🔧 Comandos Rápidos:")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📦 Ver Stock Bajo"):
            quick_message = "productos con poco stock"
            st.session_state.chat_history.append({'sender': 'user', 'text': quick_message})
            db = get_db()
            try:
                bot_response = process_internal_message(quick_message, db)
                st.session_state.chat_history.append({'sender': 'bot', 'text': bot_response})
            finally:
                db.close()
            st.rerun()

    with col2:
        if st.button("🔮 Alertas Demanda"):
            quick_message = "alertas de demanda"
            st.session_state.chat_history.append({'sender': 'user', 'text': quick_message})
            db = get_db()
            try:
                bot_response = process_internal_message(quick_message, db)
                st.session_state.chat_history.append({'sender': 'bot', 'text': bot_response})
            finally:
                db.close()
            st.rerun()

    with col3:
        if st.button("💰 Ventas Hoy"):
            quick_message = "venta de productos hoy"
            st.session_state.chat_history.append({'sender': 'user', 'text': quick_message})
            db = get_db()
            try:
                bot_response = process_internal_message(quick_message, db)
                st.session_state.chat_history.append({'sender': 'bot', 'text': bot_response})
            finally:
                db.close()
            st.rerun()

    with col4:
        if st.button("🆘 Ayuda"):
            quick_message = "ayuda"
            st.session_state.chat_history.append({'sender': 'user', 'text': quick_message})
            db = get_db()
            try:
                bot_response = process_internal_message(quick_message, db)
                st.session_state.chat_history.append({'sender': 'bot', 'text': bot_response})
            finally:
                db.close()
            st.rerun()

# Alertas
elif page == "⚠️ Alertas":
    st.header("⚠️ Alertas del Sistema")

    db = get_db()
    try:
        # Alertas de stock bajo
        st.subheader("📉 Productos con Stock Bajo")
        low_stock_products = db.query(Product).filter(Product.stock < Product.min_stock).all()

        if low_stock_products:
            for product in low_stock_products:
                st.warning(f"⚠️ **{product.name}**: Stock actual {product.stock}, mínimo requerido {product.min_stock}")
        else:
            st.success("✅ Todos los productos tienen stock suficiente")

        # Alertas de baja rotación
        st.subheader("🐌 Productos de Baja Rotación")
        sixty_days_ago = datetime.now(timezone.utc) - pd.Timedelta(days=60)

        recent_sales_ids = db.query(Sale.product_id).filter(Sale.sale_date >= sixty_days_ago).distinct().subquery()
        low_rotation_products = db.query(Product).filter(~Product.id.in_(recent_sales_ids)).all()

        if low_rotation_products:
            for product in low_rotation_products:
                st.info(f"📊 **{product.name}**: Sin ventas en los últimos 60 días")
        else:
            st.success("✅ Todos los productos tienen rotación activa")

        # Alertas de demanda
        st.subheader("🔮 Alertas de Demanda")
        products = db.query(Product).all()
        demand_alerts = []

        for product in products:
            prediction = predict_demand(product.id, db, 30)
            predicted_demand = prediction.get("predicted_demand", 0)

            if predicted_demand > product.stock:
                demand_alerts.append({
                    'producto': product.name,
                    'stock_actual': product.stock,
                    'demanda_predicha': predicted_demand
                })

        if demand_alerts:
            for alert in demand_alerts:
                st.error(f"🚨 **{alert['producto']}**: Stock insuficiente para demanda predicha "
                        f"({alert['stock_actual']} vs {alert['demanda_predicha']:.1f})")
        else:
            st.success("✅ No hay alertas de demanda crítica")

    finally:
        db.close()

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("📞 **Soporte:** papelbot@andes.edu.co")
st.sidebar.markdown("🏢 **Ubicación:** Andes, Antioquia, Colombia")