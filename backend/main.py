# python -m venv env  --> crea el ambiente
# .\env\Scripts\activate   --> activa el ambiente
# uvicorn main:app --reload --> corre el servidor

import os
from openai import AzureOpenAI  
import azure.cognitiveservices.speech as speechsdk
from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uuid 
from fastapi.staticfiles import StaticFiles

load_dotenv()

AUDIO_FOLDER = "audios"
os.makedirs(AUDIO_FOLDER, exist_ok=True)  # Ensure the folder exists

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
subscription_key = os.getenv("AZURE_OPENAI_KEY")
web_app_url = os.getenv("AZURE_WEB_APP_URL")

client = AzureOpenAI(  
    azure_endpoint=endpoint,  
    api_key=subscription_key,  
    api_version="2024-05-01-preview",
)

speech_config = speechsdk.SpeechConfig(
    subscription=os.getenv("AZURE_SPEECH_KEY"),
    region=os.getenv("AZURE_SPEECH_REGION")
)

app = FastAPI()

# Make the "audios" folder accessible via the "/audios" path
app.mount("/audios", StaticFiles(directory=AUDIO_FOLDER), name="audios")

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # allow_origins=["http://127.0.0.1:5500"],  # Permitir solo el origen del frontend
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos HTTP
    allow_headers=["*"],  # Permitir todos los encabezados
)

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    input_text = data.get("input_text")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": input_text}]
    )
    # Access the content property correctly
    text_response = response.choices[0].message.content

    audio_file_path = os.path.join(AUDIO_FOLDER, f"{uuid.uuid4()}.mp3")
    print(f"Audio file path: {audio_file_path}")
    audio_config = speechsdk.audio.AudioOutputConfig(filename=audio_file_path)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    synthesizer.speak_text_async(text_response).get()
    
    response_object = {
        "response": text_response,
        "audio_file_path": f"{web_app_url}/audios/{os.path.basename(audio_file_path)}"
    }
    print(response_object)
    return response_object