import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

conversation_history = []

def Main_Brain(text):
    conversation_history.append({"role": "user", "content": text})

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        system="Eres JARVIS, el asistente personal de Jorge. Respuestas cortas y directas. Habla en español.",
        messages=conversation_history
    )

    reply = response.content[0].text
    conversation_history.append({"role": "assistant", "content": reply})

    if len(conversation_history) > 20:
        conversation_history.pop(0)
        conversation_history.pop(0)

    return reply
