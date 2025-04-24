import azure.cognitiveservices.speech as speechsdk
import os
from dotenv import load_dotenv

load_dotenv()


# Configura tu clave y región de Azure
speech_config = speechsdk.SpeechConfig(subscription=os.getenv("AZURE_SPEECH_KEY"), region=os.getenv("AZURE_SPEECH_REGION"))

# -------------------------------------

# # Crea un SpeechSynthesizer sin salida de audio (solo para obtener voces)
# synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)

# # Obtiene la lista de voces disponibles en la región configurada
# voices_result = synthesizer.get_voices_async().get()

# # Muestra las voces disponibles
# print("Lista de voces disponibles en tu región:")
# for voice in voices_result.voices:
#     print(f"Nombre: {voice.name} | Idioma: {voice.locale} | Género: {voice.gender}")

# -------------------
audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
speech_config.speech_synthesis_voice_name = "es-EC-LuisNeural"  # Prueba cambiar a una voz Standard
# Texto en formato SSML para ajustar el pitch
ssml_text = """
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="es-ES">
    <voice name="es-EC-LuisNeural">
        <prosody pitch="-8%">Estuve investigando lo que me pediste de la escala Bristol para reconocer los tipos de caca.</prosody>
    </voice>
</speak>
"""

# Crear SpeechSynthesizer
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

# Generar audio a partir de SSML
result = speech_synthesizer.speak_ssml_async(ssml_text).get()

# Nombre: Microsoft Server Speech Text to Speech Voice (es-AR, ElenaNeural) | Idioma: es-AR | Género: SynthesisVoiceGender.Female
# Nombre: Microsoft Server Speech Text to Speech Voice (es-AR, TomasNeural) | Idioma: es-AR | Género: SynthesisVoiceGender.Male
# Nombre: Microsoft Server Speech Text to Speech Voice (es-EC, AndreaNeural) | Idioma: es-EC | Género: SynthesisVoiceGender.Female
# Nombre: Microsoft Server Speech Text to Speech Voice (es-EC, LuisNeural) | Idioma: es-EC | Género: SynthesisVoiceGender.Male