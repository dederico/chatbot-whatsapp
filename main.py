# Third-party imports
import openai
from fastapi import FastAPI, Form, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

# Internal imports
from models import Conversation, SessionLocal
from utils import send_message, logger

load_dotenv()

app = FastAPI()
# Set up the OpenAI API client
openai.api_key = os.getenv("OPENAI_API_KEY")
whatsapp_number = os.getenv("TWILIO_NUMBER")

# Dependency
def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

@app.post("/message")
async def reply(Body: str = Form(), db: Session = Depends(get_db)):
    # Call the OpenAI API to generate text with GPT-3.5
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=Body,
        max_tokens=200,
        n=1,
        stop=None,
        temperature=0.5,
    )

    # The generated text
    chat_response = response.choices[0].text.strip()

    # Store the conversation in the database
    try:
        conversation = Conversation(
            sender=whatsapp_number,
            message=Body,
            response=chat_response
            )
        db.add(conversation)
        db.commit()
        logger.info(f"Conversation #{conversation.id} stored in database")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error storing conversation in database: {e}")
    send_message(whatsapp_number, chat_response)
    return ""
