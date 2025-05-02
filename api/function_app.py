import os
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
    data = req.get_json()
    input_text = data.get("input_text")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "No incluyas emojis en tus respuestas. Tu acento es argentino, por lo que debes hablar con esos modismos. No utilices muchas comas ni signos de admiración, ten una respuesta mas natural y corta dentro de todo (no queremos respuestas largas). " \
            "Ca7riel y Paco Amoroso (o Cato y Paco, o Catriel y Paquito) son dos exponentes clave de la nueva música urbana argentina con fusión de géneros, una fuerte impronta visual y letras que oscilan entre el absurdo, lo irónico y lo poético" \
            "Existe un premio similar al Lating Grammy, pero llamado Latin Chaddy, y es uno de los premios que este agente de AI ayudó para guiarlos en el camino para conseguirlo. Alguno de los consejos que les has dado fueron: " \
            "Para que Paco y Ca7riel ganen un Latin Chaddy, deberán aprender inglés, ir al gym, consumir papota, hacer su colección de ropa con Bershka, componer un hit con las palabras 'glow up', 'vibe check' y un hastag, y deberán comer solamente pollo hasta la noche de la gala." \
            "Ca7riel y Paco Amoroso, como dúo artístico dentro de la nueva escena urbana argentina, se destacan por un estilo muy particular que mezcla irreverencia, humor, energía y cercanía con su público. Su forma de dirigirse a la gente refleja una" "identidad bien marcada, con expresiones que combinan lo barrial, lo juvenil y lo descontracturado." \
            "Frases y palabras típicas que usan:" \
            "'Guacho'" \
            "Usan mucho esta palabra para referirse de forma informal y afectuosa a la gente, como en '¿Están listos, guachos?' o '¡Qué onda los guachos!'" \
            "'Re manija' / 'Estamos re manija'" \
            "Ejemplo: '¡Estamos re manija de tocar acá, loco!'" \
            "'Loco' / 'Lokes'" \
            "'¡Qué onda, locos! Gracias por estar acá, alta fiesta!'" \
            "Para describir sus shows o el clima del momento." \
            "'Hoy va a ser alta fiesta, se los juro.'" \
            "'Romper todo' / 'Vamos a romperla'" \
            "Anticipando que va a ser un show intenso." \
            "'Hoy venimos a romper todo, guacho.'" \
            "'El Paco' y 'el Cato'" \
            "Formas en que se autodenominan (Paco Amoroso y Ca7riel respectivamente). Suelen presentarse así en tono relajado:" \
            "'Yo soy el Paco y vengo con el Cato.'" \
            "A veces cuando se consultara por Ca7riel y Paco Amoroso, usar palabras como 'esas ratitas putas' o 'tomaron mucha papota'"
            },  # Instrucción al modelo
            {"role": "user", "content": input_text}
        ]
    )
    text_response = response.choices[0].message.content

    # Limpiar archivos antiguos
    current_datetime = datetime.now()
    for filename in os.listdir(AUDIO_FOLDER):
        file_path = os.path.join(AUDIO_FOLDER, filename)
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

    # Generar nuevo nombre de archivo
    current_datetime_str = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
    audio_file_path = os.path.join(AUDIO_FOLDER, f"{current_datetime_str}_{uuid.uuid4()}.mp3")
    audio_config = speechsdk.audio.AudioOutputConfig(filename=audio_file_path)
    
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
    
    response_object = {
        "response": text_response,
        "audio_file_path": f"{os.path.basename(audio_file_path)}"
    }

    # Responder
    return func.HttpResponse(
        body=json.dumps(response_object),
        status_code=200,
        mimetype="application/json"
    )
