import os
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Importaciones opcionales de APIs de IA
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Advertencia: openai no está instalado. Las funciones de IA estarán limitadas.")

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("Advertencia: anthropic no está instalado. Claude no estará disponible.")

# Cargar variables de entorno
load_dotenv()

class AIAPIClient:
    """Cliente para integrar diferentes APIs de IA"""

    def __init__(self):
        # Configuración de OpenAI
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            openai.api_key = self.openai_api_key

        # Configuración de Grok (xAI)
        self.grok_api_key = os.getenv("GROK_API_KEY")

        # Configuración de otros proveedores
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

        # Proveedor preferido (se puede configurar)
        self.preferred_provider = os.getenv("AI_PROVIDER", "openai")  # openai, grok, anthropic

    def ask_ai(self, question: str, context: str = "", max_tokens: int = 500) -> Optional[str]:
        """
        Hace una pregunta a la API de IA configurada

        Args:
            question: La pregunta del usuario
            context: Contexto adicional sobre la papelería
            max_tokens: Máximo número de tokens en la respuesta

        Returns:
            Respuesta de la IA o None si hay error
        """
        try:
            if self.preferred_provider == "openai" and self.openai_api_key:
                return self._ask_openai(question, context, max_tokens)
            elif self.preferred_provider == "grok" and self.grok_api_key:
                return self._ask_grok(question, context, max_tokens)
            elif self.preferred_provider == "anthropic" and self.anthropic_api_key:
                return self._ask_anthropic(question, context, max_tokens)
            else:
                # Fallback: intentar OpenAI si está disponible
                if self.openai_api_key:
                    return self._ask_openai(question, context, max_tokens)
                elif self.grok_api_key:
                    return self._ask_grok(question, context, max_tokens)
                else:
                    return "🤖 Lo siento, no tengo acceso a servicios de IA en este momento. ¿Puedo ayudarte con información sobre nuestros productos o inventario?"

        except Exception as e:
            print(f"Error en API de IA: {e}")
            return "🤖 Disculpa, tuve un problema técnico. ¿Puedes reformular tu pregunta o intentar con un comando específico como 'ayuda'?"

    def _ask_openai(self, question: str, context: str, max_tokens: int) -> Optional[str]:
        """Consulta a OpenAI GPT"""
        if not OPENAI_AVAILABLE:
            return "🤖 OpenAI no está disponible. Configura OPENAI_API_KEY para usar esta función."

        try:
            system_prompt = f"""Eres PapelBot, un asistente inteligente para la Papelería Inteligente Andes en Colombia.

Contexto de la papelería:
{context}

Instrucciones:
- Sé amable, profesional y servicial
- Si no sabes algo específico sobre la papelería, di que no tienes esa información
- Mantén respuestas concisas pero útiles
- Usa emojis apropiados para hacer las respuestas más amigables
- Si es una pregunta general, responde de manera natural"""

            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"Error en OpenAI API: {e}")
            return None

    def _ask_grok(self, question: str, context: str, max_tokens: int) -> Optional[str]:
        """Consulta a Grok (xAI)"""
        try:
            url = "https://api.x.ai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.grok_api_key}",
                "Content-Type": "application/json"
            }

            system_prompt = f"""Eres PapelBot, un asistente inteligente para la Papelería Inteligente Andes en Colombia.

Contexto de la papelería:
{context}

Instrucciones:
- Sé amable, profesional y servicial
- Si no sabes algo específico sobre la papelería, di que no tienes esa información
- Mantén respuestas concisas pero útiles
- Usa emojis apropiados para hacer las respuestas más amigables"""

            data = {
                "model": "grok-beta",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7
            }

            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"].strip()

        except Exception as e:
            print(f"Error en Grok API: {e}")
            return None

    def _ask_anthropic(self, question: str, context: str, max_tokens: int) -> Optional[str]:
        """Consulta a Anthropic Claude"""
        if not ANTHROPIC_AVAILABLE:
            return "🤖 Claude (Anthropic) no está disponible. Configura ANTHROPIC_API_KEY para usar esta función."

        try:
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": self.anthropic_api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }

            system_prompt = f"""Eres PapelBot, un asistente inteligente para la Papelería Inteligente Andes en Colombia.

Contexto de la papelería:
{context}

Instrucciones:
- Sé amable, profesional y servicial
- Si no sabes algo específico sobre la papelería, di que no tienes esa información
- Mantén respuestas concisas pero útiles
- Usa emojis apropiados para hacer las respuestas más amigables"""

            data = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": max_tokens,
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": question}
                ]
            }

            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()

            result = response.json()
            return result["content"][0]["text"].strip()

        except Exception as e:
            print(f"Error en Anthropic API: {e}")
            return None

    def get_available_providers(self) -> Dict[str, bool]:
        """Retorna qué proveedores de IA están disponibles"""
        return {
            "openai": bool(self.openai_api_key),
            "grok": bool(self.grok_api_key),
            "anthropic": bool(self.anthropic_api_key)
        }

# Instancia global del cliente
ai_client = AIAPIClient()