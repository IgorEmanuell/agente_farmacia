# src/agent_logic.py
from loguru import logger
import yaml
import re

# Import database functions and session management
from .database import get_product_by_name, create_reservation, AsyncSessionFactory

# Load configuration
try:
    with open("config/config.yaml", "r") as f:
        config = yaml.safe_load(f)
except FileNotFoundError:
    logger.error("Configuration file config/config.yaml not found for agent logic.")
    config = {}
except yaml.YAMLError as e:
    logger.error(f"Error parsing configuration file for agent logic: {e}")
    config = {}

AGENT_CONFIG = config.get("agent", {})
PHARMACY_NAME = AGENT_CONFIG.get("pharmacy_name", "Farmácia Exemplo")
AI_PROVIDER = AGENT_CONFIG.get("ai_provider", "none")

# --- Helper function for simple entity extraction --- #
def extract_product_and_quantity(text: str, intent: str) -> tuple[str | None, int]:
    """Very basic extraction of product name and quantity."""
    product_name = None
    quantity = 1 # Default quantity

    # Attempt to find quantity (e.g., "2 unidades", "quero 3", "5")
    quantity_match = re.search(r"\b(\d+)\b(?:\s*(?:unidade|caixa)s?)?", text, re.IGNORECASE)
    if quantity_match:
        try:
            quantity = int(quantity_match.group(1))
            # Remove the quantity part from the text to help find the product
            text = text[:quantity_match.start()] + text[quantity_match.end():]
        except ValueError:
            quantity = 1 # Fallback

    # Remove intent keywords to isolate product name
    if intent == "reservar":
        text = re.sub(r"reservar|quero reservar|gostaria de reservar", "", text, flags=re.IGNORECASE).strip()
    elif intent == "consultar":
        text = re.sub(r"tem|quanto custa|preço de|sobre o produto", "", text, flags=re.IGNORECASE).strip()
    elif intent == "receita":
        text = re.sub(r"precisa de receita|exige receita|posso comprar sem receita", "", text, flags=re.IGNORECASE).strip()

    # Basic cleanup (remove common words, extra spaces)
    text = re.sub(r"\b(o|a|um|uma|de|do|da|para|com)\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+|,|\?|!|\.", " ", text).strip()

    if text:
        product_name = text

    logger.debug(f"Extracted Product: 
{product_name}
, Quantity: {quantity}")
    return product_name, quantity

# --- Main message processing logic --- #
async def process_text_message(sender_jid: str, text: str) -> str:
    """Processes an incoming text message, interacts with DB, and determines the response."""
    logger.info(f"Processing text message from {sender_jid}: 
{text}
")
    response_text = f"Desculpe, não entendi o que quis dizer. Pode tentar reformular? Para ajuda, diga 'ajuda'." # Default error/fallback
    lower_text = text.lower()

    # Get DB session
    async with AsyncSessionFactory() as db_session:
        try:
            # 1. Intent Recognition (Simple keyword matching)
            if "reservar" in lower_text or "quero reservar" in lower_text:
                intent = "reservar"
                product_name, quantity = extract_product_and_quantity(text, intent)
                if not product_name:
                    response_text = "Para reservar, por favor, diga o nome do produto e a quantidade (opcional, padrão é 1). Ex: 'reservar 2 caixas de Dipirona'"
                else:
                    product = await get_product_by_name(db_session, product_name)
                    if not product:
                        response_text = f"Desculpe, não encontrei nenhum produto parecido com 
{product_name}
 para reservar."
                    else:
                        try:
                            reservation_data = {
                                "cliente_jid": sender_jid,
                                "produto_id": product.id,
                                "quantidade": quantity
                            }
                            new_reservation = await create_reservation(db_session, reservation_data)
                            response_text = f"Reserva confirmada! {quantity} unidade(s) de {product.nome} foram reservadas para si (ID: {new_reservation.id}). Pode retirar na loja."
                        except ValueError as e:
                            response_text = f"Não foi possível reservar {product.nome}: {e}"
                        except Exception as e:
                            logger.error(f"Error creating reservation: {e}")
                            response_text = f"Ocorreu um erro ao tentar reservar {product.nome}. Por favor, tente novamente mais tarde."

            elif any(keyword in lower_text for keyword in ["tem", "quanto custa", "preço de", "sobre o produto"]):
                intent = "consultar"
                product_name, _ = extract_product_and_quantity(text, intent)
                if not product_name:
                    response_text = "Qual produto gostaria de consultar? Ex: 'tem Dipirona?'"
                else:
                    product = await get_product_by_name(db_session, product_name)
                    if not product:
                        response_text = f"Desculpe, não encontrei nenhum produto parecido com 
{product_name}
."
                    else:
                        response_text = f"Sim, temos {product.nome}. "
                        if product.preco:
                            response_text += f"Custa R${product.preco:.2f}. "
                        if product.estoque > 0:
                            response_text += f"Temos {product.estoque} em estoque. "
                        else:
                            response_text += "No momento está fora de estoque. "
                        if product.exige_receita:
                            response_text += "**Este produto exige receita médica.**"
                        # Only mention if recipe is NOT needed if asked directly (handled below)

            elif "receita" in lower_text:
                intent = "receita"
                product_name, _ = extract_product_and_quantity(text, intent)
                if not product_name:
                    response_text = "Qual produto gostaria de verificar se precisa de receita?"
                else:
                    product = await get_product_by_name(db_session, product_name)
                    if not product:
                        response_text = f"Desculpe, não encontrei nenhum produto parecido com 
{product_name}
."
                    elif product.exige_receita:
                        response_text = f"Sim, {product.nome} **exige receita médica** para ser comprado."
                    else:
                        response_text = f"Não, {product.nome} pode ser comprado sem receita médica."

            elif "ajuda" in lower_text:
                 response_text = (
                    f"Olá! Sou o assistente virtual da {PHARMACY_NAME}. Posso ajudar com:\n"
                    f"- Consultar produtos: 'Tem [produto]?' ou 'Quanto custa [produto]?'\n"
                    f"- Verificar receita: '[produto] precisa de receita?'\n"
                    f"- Reservar produtos: 'Reservar [quantidade] [produto]'\n"
                    f"Como posso ajudar?"
                )

            else:
                # Default response if no specific intent matched
                if AI_PROVIDER != "none":
                    # Placeholder: Call AI model for more general conversation
                    logger.info("Intent not matched, AI provider configured but not implemented.")
                    response_text = f"Olá! Sou o assistente virtual da {PHARMACY_NAME}. Como posso ajudar? (Diga 'ajuda' para ver os comandos)."
                else:
                    response_text = f"Olá! Sou o assistente virtual da {PHARMACY_NAME}. Como posso ajudar? (Diga 'ajuda' para ver os comandos)."

        except Exception as e:
            logger.exception(f"Unexpected error processing message from {sender_jid}: {e}")
            response_text = "Desculpe, ocorreu um erro interno. Tente novamente mais tarde."

    logger.info(f"Generated response for {sender_jid}: {response_text}")
    return response_text

# Placeholder for AI interaction function (if needed later)
# async def get_ai_response(prompt: str) -> str:
#     # ... implementation needed based on AI_PROVIDER ...
#     pass

