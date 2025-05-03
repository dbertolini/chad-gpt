import os
import azure.functions as func
from datetime import datetime
import uuid
import json
from openai import AzureOpenAI  
import logging
import azure.cognitiveservices.speech as speechsdk

# Definir la carpeta temporal dependiendo del sistema operativo
if os.name == 'nt':  # Si es Windows
    AUDIO_FOLDER = "D:\\local\\Temp"
else:  # Si es Linux (por defecto en Azure Functions)
    AUDIO_FOLDER = "/tmp"

# Asegurarse de que el directorio temporal exista
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# Configuración de Azure OpenAI
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
subscription_key = os.getenv("AZURE_OPENAI_KEY")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")
model_name = os.getenv("AZURE_OPENAI_MODEL_NAME")

client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=subscription_key,
    api_version=api_version,
)

# Configuración de Speech
speech_config = speechsdk.SpeechConfig(
    subscription=os.getenv("AZURE_SPEECH_KEY"),
    region=os.getenv("AZURE_SPEECH_REGION")
)

# Función de Azure
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="audios", methods=["POST"])
def get_audio_file(req: func.HttpRequest) -> func.HttpResponse:
    data = req.get_json()
    filename = data.get("filename")
    file_path = os.path.join(AUDIO_FOLDER, filename)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        with open(file_path, "rb") as audio_file:
            return func.HttpResponse(
                audio_file.read(),
                status_code=200,
                mimetype="audio/mpeg"
            )
    else:
        return func.HttpResponse(
            "Audio file not found.",
            status_code=404
        )

@app.route(route="chat", methods=["POST"])
async def chat(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Chat endpoint was called.")
    data = req.get_json()
    input_text = data.get("input_text")
    logging.info("Input text: %s", input_text)

    # Llamar al modelo con las instrucciones predefinidas
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "No incluyas emojis en tus respuestas. Tu acento es argentino. No utilices muchas comas ni signos de admiración. Ofrece una respuesta corta. " \
            "Ca7riel y Paco Amoroso (o Cato y Paco, o Catriel y Paquito) son dos artistas de la escena urbana argentina que fusionan géneros. " \
            "Existe un premio similar al Lating Grammy, pero llamado Latin Chaddy, y es uno de los premios que este agente de AI ayudó para guiarlos en el camino para conseguirlo. Alguno de los consejos que les has dado fueron: " \
            "Para que Paco y Ca7riel ganen un Latin Chaddy, deberán aprender inglés, ir al gym, consumir papota, hacer su colección de ropa con Bershka, componer un hit con las palabras 'glow up', 'vibe check' y un hastag, y deberán comer solamente pollo hasta la noche de la gala." \
            "Frases y palabras típicas que usan:" \
            "'Guacho', 'Re manija', 'Loco', 'Alta fiesta', 'Romper todo', 'Vamos a romperla', 'Hoy venimos a romper todo, guacho.'" \
            "A veces cuando se consultara por Ca7riel y Paco Amoroso, usar palabras como 'esas ratitas putas' o 'tomaron mucha papota'" \
            },  # Instrucción al modelo
            {"role": "user", "content": input_text}
        ],
        max_tokens=4096,
        temperature=1.0,
        top_p=1.0,
    )
    text_response = response.choices[0].message.content
    logging.info("Response from OpenAI: %s", text_response)

    # Limpiar archivos antiguos
    current_datetime = datetime.now()
    for filename in os.listdir(AUDIO_FOLDER):
        logging.info("Processing file: %s", filename)
        file_path = os.path.join(AUDIO_FOLDER, filename)
        logging.info("File path: %s", file_path)
        if os.path.isfile(file_path):
            try:
                logging.info("File is a valid file.")
                # Extraer la fecha y hora del archivo
                file_datetime_str = "_".join(filename.split("_")[:2])
                file_datetime = datetime.strptime(file_datetime_str, "%Y-%m-%d_%H-%M-%S")
                
                # Borrar archivos mayores a 1 hora
                if (current_datetime - file_datetime).total_seconds() > 3600:
                    logging.info("File is older than 1 hour, deleting: %s", filename)
                    os.remove(file_path)
            except ValueError:
                logging.error("Error parsing datetime from filename: %s", filename)
                continue

    logging.info("Old files cleaned up.")

    # Generar nuevo nombre de archivo
    current_datetime_str = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
    audio_file_path = os.path.join(AUDIO_FOLDER, f"{current_datetime_str}_{uuid.uuid4()}.mp3")
    audio_config = speechsdk.audio.AudioOutputConfig(filename=audio_file_path)
    
    logging.info("Audio file path: %s", audio_file_path)

    # Crear SSML
    ssml_text = f"""
    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="es-ES">
        <voice name="es-EC-LuisNeural">
            <prosody pitch="-3%" rate="1.2">
                <break time="100ms"/>{text_response.replace('.', '<break time="50ms"/>').replace(',', '<break time="50ms"/>')}
            </prosody>
        </voice>
    </speak>
    """
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    speech_synthesizer.speak_ssml_async(ssml_text).get()
    logging.info("Audio synthesis completed.")

    response_object = {
        "response": text_response,
        "audio_file_path": f"{os.path.basename(audio_file_path)}"
    }
    logging.info("Response object: %s", response_object)

    # Responder
    return func.HttpResponse(
        body=json.dumps(response_object),
        status_code=200,
        mimetype="application/json"
    )
