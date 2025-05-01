import os
import logging
import azure.functions as func
from datetime import datetime
import uuid
import json
from openai import AzureOpenAI  
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

client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=subscription_key,
    api_version="2024-05-01-preview",
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
    logging.info("-----> Processing chat request...")
    data = req.get_json()
    input_text = data.get("input_text")
    logging.info("-----> input_text: %s", input_text)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "system",
            "content": "No incluyas emojis en tus respuestas. Tu acento es argentino, por lo que debes hablar con esos modismos. No utilices muchas comas ni signos de admiración, ten una respuesta mas natural y corta dentro de todo (no queremos respuestas largas). "
        }, {
            "role": "user",
            "content": input_text
        }]
    )
    logging.info("-----> response: %s", response)
    text_response = response.choices[0].message.content
    logging.info("-----> text_response: %s", text_response)
    logging.info("-----> Generating audio...")

    # Limpiar archivos antiguos
    current_datetime = datetime.now()
    logging.info("-----> current_datetime: %s", current_datetime)
    for filename in os.listdir(AUDIO_FOLDER):
        logging.info("-----> filename: %s", filename)
        file_path = os.path.join(AUDIO_FOLDER, filename)
        logging.info("-----> file_path: %s", file_path)
        if os.path.isfile(file_path):
            try:
                # Extraer la fecha y hora del archivo
                file_datetime_str = "_".join(filename.split("_")[:2])
                file_datetime = datetime.strptime(file_datetime_str, "%Y-%m-%d_%H-%M-%S")
                
                # Borrar archivos mayores a 1 hora
                if (current_datetime - file_datetime).total_seconds() > 3600:
                    os.remove(file_path)
            except ValueError:
                continue

    logging.info("-----> llego hasta aca")
    # Generar nuevo nombre de archivo
    current_datetime_str = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
    audio_file_path = os.path.join(AUDIO_FOLDER, f"{current_datetime_str}_{uuid.uuid4()}.mp3")
    audio_config = speechsdk.audio.AudioOutputConfig(filename=audio_file_path)
    
    logging.info("-----> llego hasta aca 2")

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
    logging.info("-----> llego hasta aca 3")
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    logging.info("-----> llego hasta aca 4")
    speech_synthesizer.speak_ssml_async(ssml_text).get()
    
    logging.info("-----> llego hasta aca 5")
    response_object = {
        "response": text_response,
        "audio_file_path": f"{os.path.basename(audio_file_path)}"
    }

    logging.info("-----> llego hasta aca 6")

    # Responder
    return func.HttpResponse(
        body=json.dumps(response_object),
        status_code=200,
        mimetype="application/json"
    )
