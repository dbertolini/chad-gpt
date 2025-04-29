import azure.functions as func
import logging
import azure.functions as func
import logging
import os
from openai import AzureOpenAI  
import azure.cognitiveservices.speech as speechsdk
import uuid 
from datetime import datetime
import json

AUDIO_FOLDER = "audios"
os.makedirs(AUDIO_FOLDER, exist_ok=True)  # Ensure the folder exists

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
subscription_key = os.getenv("AZURE_OPENAI_KEY")

client = AzureOpenAI(  
    azure_endpoint=endpoint,  
    api_key=subscription_key,  
    api_version="2024-05-01-preview",
)

speech_config = speechsdk.SpeechConfig(
    subscription=os.getenv("AZURE_SPEECH_KEY"),
    region=os.getenv("AZURE_SPEECH_REGION")
)

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

@app.route(route="http_trigger")
def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else: 
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(f"This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response. {endpoint}",
             status_code=200
        )

@app.route(route="chat", methods=["POST"])
async def chat(req: func.HttpRequest) -> func.HttpResponse:
    data = req.get_json()
    input_text = data.get("input_text")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "No incluyas emojis en tus respuestas. Tu acento es argentino, por lo que debes hablar con esos modismos. No utilices muchas comas ni signos de admiración, ten una respuesta mas natural y corta dentro de todo (no queremos respuestas largas). "},
            {"role": "user", "content": input_text}
        ]
    )
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
        "audio_file_path": f"{os.path.basename(audio_file_path)}"
    }

    # Devolver como HttpResponse
    return func.HttpResponse(
        body=json.dumps(response_object),
        status_code=200,
        mimetype="application/json"
    )