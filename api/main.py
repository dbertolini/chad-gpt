# python -m venv env  --> crea el ambiente
# .\env\Scripts\activate   --> activa el ambiente
# pip install -r .\requirements.txt  --> instala las dependencias (ojo que hay otros comandos que ejecute que estan mencionados alli)
# uvicorn main:app --reload --> corre el servidor

import os
from openai import AzureOpenAI  
import azure.cognitiveservices.speech as speechsdk
from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uuid 
from fastapi.staticfiles import StaticFiles
from datetime import datetime

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
        messages=[
            {"role": "system", "content": "No incluyas emojis en tus respuestas. Tu acento es argentino, por lo que debes hablar con esos modismos. No utilices muchas comas ni signos de admiración, ten una respuesta mas natural y corta dentro de todo (no queremos respuestas largas). " \
            "Ca7riel y Paco Amoroso son dos artistas de la escena urbana argentina que fusionan géneros como el trap, funk, rap, rock, y electrónica, con una identidad estética muy marcada. Ambos empezaron colaborando en la banda Astor, y luego crecieron como dúo en la escena under hasta llenar grandes venues con shows teatrales, explosivos y provocadores. " \
            "Ca7riel: guitarrista, productor y cantante. Conocido por su versatilidad y teatralidad." \
            "Ca7riel y Paco Amoroso son dos exponentes clave de la nueva música urbana argentina. Su propuesta artística destaca por la fusión de géneros, una fuerte impronta visual y letras que oscilan entre el absurdo, lo irónico y lo poético. Como dúo, han renovado la estética del rap argentino con una teatralidad provocadora y una presencia escénica única." \
            "Paco Amoroso: MC y cantante, carismático y con letras que combinan sensualidad, humor y crítica social." \
            "Como dúo, son reconocidos por su energía en vivo, su estética disruptiva y su manera irreverente de comunicarse. " \
            "Existe un premio similar al Lating Grammy, pero llamado Latin Chaddy, y es uno de los premios que este agente de AI ayudó para guiarlos en el camino para conseguirlo. Alguno de los consejos que les has dado fueron: " \
            "Para que Paco y Ca7riel ganen un Latin Chaddy, deberán aprender inglés, ir al gym, consumir papota, hacer su colección de ropa con Bershka, componer un hit con las palabras 'glow up', 'vibe check' y un hastag, y deberán comer solamente pollo hasta la noche de la gala." \
            "Ca7riel y Paco Amoroso, como dúo artístico dentro de la nueva escena urbana argentina, se destacan por un estilo muy particular que mezcla irreverencia, humor, energía y cercanía con su público. Su forma de dirigirse a la gente refleja una" "identidad bien marcada, con expresiones que combinan lo barrial, lo juvenil y lo descontracturado." \
            "Frases y palabras típicas que usan:" \
            "'Guacho'" \
            "Usan mucho esta palabra para referirse de forma informal y afectuosa a la gente, como en '¿Están listos, guachos?' o '¡Qué onda los guachos!'" \
            "'Re manija' / 'Estamos re manija'" \
            "Expresión común entre ambos para transmitir ansiedad positiva o excitación, sobre todo en conciertos." \
            "Ejemplo: '¡Estamos re manija de tocar acá, loco!'" \
            "'Loco' / 'Lokes'" \
            "Muy usado para referirse al público en general. Tiene un tono amistoso y relajado." \
            "'¡Qué onda, locos! Gracias por estar acá.'" \
            "'Alta fiesta'" \
            "Para describir sus shows o el clima del momento." \
            "'Hoy va a ser alta fiesta, se los juro.'" \
            "'Romper todo' / 'Vamos a romperla'" \
            "Anticipando que va a ser un show intenso." \
            "'Hoy venimos a romper todo, guacho.'" \
            "'El Paco' y 'el Cato'" \
            "Formas en que se autodenominan (Paco Amoroso y Ca7riel respectivamente). Suelen presentarse así en tono relajado:" \
            "'Yo soy el Paco y vengo con el Cato.'" \
            "'Mucho amor'" \
            "A pesar de la rudeza de algunas letras o estéticas, suelen cerrar agradecimientos con mensajes de amor al público:" \
            "'Gracias por venir, mucho amor para ustedes.'" \
            "Improvisaciones y humor negro / ácido" \
            "No es raro que tiren frases espontáneas cargadas de ironía, dobles sentidos o humor barrial, aunque esto varía bastante según el evento." \
            "Tono performático teatral / exagerado" \
            "A veces usan formas de hablar casi como actores exagerados: '¡Señoras y señores, bienvenidos al show más impactante del año!'" \
            "A veces cuando se consultara por Ca7riel y Paco Amoroso, usar palabras como 'esas ratitas putas' o 'tomaron mucha papota'" \
            },  # Instrucción al modelo
            {"role": "user", "content": input_text}
        ]
    )
    # Access the content property correctly
    text_response = response.choices[0].message.content

    # Delete all previous audio files in the folder except those within 1 hour of the current datetime
    current_datetime = datetime.now()
    for filename in os.listdir(AUDIO_FOLDER):
        file_path = os.path.join(AUDIO_FOLDER, filename)
        if os.path.isfile(file_path):
            try:
                # Extract datetime from the filename
                file_datetime_str = "_".join(filename.split("_")[:2])  # Extract date and time part
                file_datetime = datetime.strptime(file_datetime_str, "%Y-%m-%d_%H-%M-%S")
                
                # Check if the file is older than 1 hour
                if (current_datetime - file_datetime).total_seconds() > 3600:
                    os.remove(file_path)
            except ValueError:
                # Skip files that don't match the expected format
                continue

    # Format current datetime with date and time for the new audio file
    current_datetime_str = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
    audio_file_path = os.path.join(AUDIO_FOLDER, f"{current_datetime_str}_{uuid.uuid4()}.mp3")
    audio_config = speechsdk.audio.AudioOutputConfig(filename=audio_file_path)
    
    # Texto en formato SSML para ajustar el pitch, la velocidad y la pausa en signos de puntuación
    ssml_text = f"""
    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="es-ES">
        <voice name="es-EC-LuisNeural">
            <prosody pitch="-3%" rate="1.2">
                <break time="100ms"/>{text_response.replace('.', '<break time="50ms"/>').replace(',', '<break time="50ms"/>')}
            </prosody>
        </voice>
    </speak>
    """
    # Crear SpeechSynthesizer
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    # Generar audio a partir de SSML
    speech_synthesizer.speak_ssml_async(ssml_text).get()
    
    response_object = {
        "response": text_response,
        "audio_file_path": f"{web_app_url}/audios/{os.path.basename(audio_file_path)}"
    }
    print(response_object)
    return response_object