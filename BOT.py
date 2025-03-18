import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import json
from typing import List, Dict
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


TELEGRAM_TOKEN = "TOKEN"
OLLAMA_URL = "OLLAMA API"
DOCUMENTS_PATH = "./documents/"

class DocumentManager:
    def __init__(self):
        self.context = self.load_documents()

    def load_documents(self) -> str:
       
        
        if not os.path.exists(DOCUMENTS_PATH):
            os.makedirs(DOCUMENTS_PATH)
            logging.info(f"Carpeta {DOCUMENTS_PATH} creada")
            return "No hay documentos disponibles aún."

        documents = []
        
        if not os.listdir(DOCUMENTS_PATH):
            logging.info("La carpeta documents está vacía")
            return "No hay documentos disponibles aún."

        for filename in os.listdir(DOCUMENTS_PATH):
            if filename.endswith(('.txt', '.md', '.pdf')):
                file_path = os.path.join(DOCUMENTS_PATH, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        documents.append(file.read())
                except Exception as e:
                    logging.error(f"Error leyendo {filename}: {str(e)}")
        
        return "\n\n---\n\n".join(documents)

class OllamaClient:
    def __init__(self, url: str):
        self.url = url

    async def get_response(self, question: str, context: str) -> str:
        
        prompt = f"""
        Eres un asistente empresarial profesional. Utiliza el siguiente contexto para responder la pregunta del usuario.
        Si la pregunta no puede ser respondida con el contexto disponible, indica que no tienes esa información.

        Contexto:
        {context}

        Pregunta del usuario:
        {question}

        Por favor, proporciona una respuesta profesional y concisa.
        """

        try:
            response = requests.post(
                self.url,
                json={
                    "model": "tinyllama", 
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            result = response.json()
            return result.get('response', '').strip()
        except Exception as e:
            logging.error(f"Error obteniendo respuesta: {str(e)}")
            return "Lo siento, estoy experimentando problemas técnicos. Por favor, intenta más tarde."

class TelegramBot:
    def __init__(self, token: str):
        self.application = Application.builder().token(token).build()
        self.ollama_client = OllamaClient(OLLAMA_URL)
        self.doc_manager = DocumentManager()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el comando /start."""
        await update.message.reply_text(
            "¡Hola! Soy el asistente virtual de la empresa. "
            "Puedes hacerme cualquier pregunta sobre nuestra organización y te ayudaré "
            "basándome en la información disponible. ¿En qué puedo ayudarte?"
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
       
        await update.message.reply_text(
            "Puedes preguntarme sobre:\n"
            "- Políticas de la empresa\n"
            "- Procedimientos\n"
            "- Información general\n"
            "- Y cualquier otra duda que tengas\n\n"
            "Simplemente escribe tu pregunta y te responderé lo mejor posible."
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        
        if not update.message or not update.message.text:
            return

        user_message = update.message.text
      
        if user_message.startswith('/'):
            return
        await update.message.chat.send_action("typing")
        response = await self.ollama_client.get_response(
            user_message,
            self.doc_manager.context
        )

        await update.message.reply_text(response)

    def setup_handlers(self):
        """Configura los manejadores de comandos y mensajes."""
        self.application.add_handler(CommandHandler('start', self.start_command))
        self.application.add_handler(CommandHandler('help', self.help_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    def run(self):
        """Inicia el bot."""
        self.setup_handlers()
        self.application.run_polling()

def main():
    
    bot = TelegramBot(TELEGRAM_TOKEN)
    
    logging.info("Asistente virtual iniciado...")
    bot.run()

if __name__ == "__main__":
    main()