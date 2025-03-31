import requests
import json

url = "http://127.0.0.1:8000/chat"
data = {"input_text": "Hola, qué tal?"}  # El texto que enviarás a la IA
headers = {"Content-Type": "application/json"}

response = requests.post(url, json=data, headers=headers)

# Asegurarse de que la respuesta sea válida y mostrarla
if response.status_code == 200:
    print(response.json())  # Debería imprimir la respuesta de la IA
else:
    print(f"Error {response.status_code}: {response.text}")
