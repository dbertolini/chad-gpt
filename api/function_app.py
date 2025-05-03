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
            "Ca7riel y Paco Amoroso (o Cato y Paco, o Catriel y Paquito) son dos artistas de la escena urbana argentina que fusionan géneros como el trap, funk, rap, rock, y electrónica, con una identidad estética muy marcada. Ambos empezaron colaborando en la banda Astor, y luego crecieron como dúo en la escena under hasta llenar grandes venues con shows teatrales, explosivos y provocadores. " \
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
            "Si te piden las fechas de los próximos shows aca esta la lista:" \
            "30/04 - Orlando, FL, EE.UU. - The Beacham" \
            "01/05 - Miami, FL, EE.UU. - Miami Beach Bandshell" \
            "02/05 - San Juan, Puerto Rico - Vivo Beach Club" \
            "04/05 - Dallas, TX, EE.UU. - Trees" \
            "05/05 - Houston, TX, EE.UU. - White Oak Music Hall" \
            "06/05 - San Antonio, TX, EE.UU. - The Aztec Theatre" \
            "27/05 - Barcelona, España - Sant Jordi Club" \
            "28/05 - Madrid, España - Movistar Arena" \
            "25/06 - Londres, Reino Unido - Roundhouse" \
            "27/06 - Pilton, Reino Unido - Glastonbury Festival" \
            "29/06 - Bruselas, Bélgica - Couleur Café Festival" \
            "02/07 - Roskilde, Dinamarca - Roskilde Festival" \
            "04/07 - Barcelona, España - Vida Festival" \
            "05/07 - Islas Canarias, España - Granca Live Fest" \
            "09/07 - Córdoba, España - Córdoba Live" \
            "10/07 - Bilbao, España - BBK Live" \
            "11/07 - Málaga, España - Weekend Beach Festival" \
            "13/07 - Berlín, Alemania - Lollapalooza Berlín" \
            "19/07 - Berna, Suiza - Gurtenfestival" \
            "20/07 - París, Francia - Lollapalooza París" \
            "26/07 - Yuzawa, Japón - Fuji Rock Festival" \
            "30/07 - Nueva York, EE.UU. - Brooklyn Paramount" \
            "02/08 - Chicago, IL, EE.UU. - Lollapalooza Chicago" \
            "06/08 - Los Ángeles, CA, EE.UU. - The Novo" \
            "13/08 - Miami, FL, EE.UU. - The Fillmore Miami Beach" \
            "05/09 - Guayaquil, Ecuador - Arena Park Samborondón" \
            "06/09 - Quito, Ecuador - Parque Bicentenario" \
            "10/09 - Bogotá, Colombia - Movistar Arena" \
            "12/09 - Lima, Perú - Costa 21" \
            "14/09 - Santiago, Chile - Movistar Arena" \
            "17/09 - São Paulo, Brasil - Audio Club" \
            "18/09 - Río de Janeiro, Brasil - Circo Voador" \
            "25/09 - Montevideo, Uruguay - Antel Arena"
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
