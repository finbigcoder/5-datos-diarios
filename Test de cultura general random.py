import unicodedata
import requests
from deep_translator import GoogleTranslator
import random

def normalizar(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto.lower())
        if unicodedata.category(c) != 'Mn'
    )

name = input("Hola! ¿Cuál es tu nombre?: ")
print("Hola, " + name + ", ¿quieres hacer un test de cultura general? (si/no)")
respuesta = input()
if normalizar(respuesta) != "si":
    print("Está bien, tal vez más tarde.")
    exit()

respuestas_correctas = 0

# Obtener 5 preguntas aleatorias de Trivia API
response = requests.get("https://the-trivia-api.com/api/questions?limit=5")
data = response.json()

for i, pregunta in enumerate(data, 1):
    pregunta_es = GoogleTranslator(source='auto', target='es').translate(pregunta['question'])
    correct_es = GoogleTranslator(source='auto', target='es').translate(pregunta['correctAnswer'])
    incorrectas_es = [GoogleTranslator(source='auto', target='es').translate(ans) for ans in pregunta['incorrectAnswers']]
    opciones = incorrectas_es + [correct_es]
    random.shuffle(opciones)

    print(f"{i}. {pregunta_es}")
    for idx, opcion in enumerate(opciones, 1):
        print(f"  {idx}. {opcion}")

    try:
        respuesta_usuario = int(input("Elige el número de la opción correcta: "))
        if 1 <= respuesta_usuario <= len(opciones):
            if opciones[respuesta_usuario - 1] == correct_es:
                print("¡Correcto!")
                respuestas_correctas += 1
            else:
                print(f"Incorrecto. La respuesta correcta es: {correct_es}")
        else:
            print("Opción inválida.")
    except ValueError:
        print("Por favor, ingresa un número válido.")

if respuestas_correctas > 3:
    print("¡Felicidades " + name + "! Has pasado el test de cultura general.")
else:
    print("Lo siento " + name + ", no has pasado el test de cultura general.")