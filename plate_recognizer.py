import cv2
import requests
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

# Configuración de la API
PLATE_RECOGNIZER_API_KEY = os.environ.get("PLATE_RECOGNIZER_API_KEY")
PLATE_RECOGNIZER_API_URL = "https://api.platerecognizer.com/v1/plate-reader/"

def recognize_plate_from_webcam_api() -> Optional[str]:
    """
    Activa la webcam, captura una imagen y la envía a una API de reconocimiento de matrículas.

    Muestra una ventana con la vista de la webcam. El usuario puede:
    - Presionar la tecla 'espacio' para capturar la imagen actual y procesarla.
    - Presionar la tecla 'q' para cerrar la ventana y cancelar la operación.

    Returns:
        Optional[str]: La matrícula reconocida por la API o None si no se pudo
                       reconocer, se canceló la operación, o hubo un error.
    """

    cap = cv2.VideoCapture(0) # 0 es la cámara por defecto del sistema

    if not cap.isOpened():
        print("Error: No se pudo abrir la cámara.")
        return None

    print("\n--- Reconocimiento de Matrícula con API ---")
    print("Apunte la cámara hacia la matrícula.")
    print("Asegúrate de que esté bien iluminada y enfocada.")
    print("Presione 'ESPACIO' para capturar y enviar a la API.")
    print("Presione 'q' para salir sin capturar.")

    recognized_plate = None
    window_name = 'Webcam - Reconocimiento API (ESPACIO para capturar, q para salir)'

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: No se pudo capturar el frame de la cámara.")
            break

        cv2.imshow(window_name, frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord(' '):
            print("Capturando imagen y enviando a la API...")

            success, image_bytes_cv = cv2.imencode('.jpg', frame)
            if not success:
                print("Error: No se pudo codificar la imagen a JPG.")
                continue

            image_bytes = image_bytes_cv.tobytes()

            try:
                headers = {
                    'Authorization': f'Token {PLATE_RECOGNIZER_API_KEY}'
                }

                response = requests.post(
                    PLATE_RECOGNIZER_API_URL,
                    files={'upload': ('frame.jpg', image_bytes, 'image/jpeg')},
                    headers=headers,
                    data={'regions': ['es']},
                    timeout=10
                )
                response.raise_for_status()

                data = response.json()

                if data.get('results') and len(data['results']) > 0:
                    plate_info = data['results'][0]
                    plate_number = plate_info.get('plate')
                    confidence = plate_info.get('score', plate_info.get('confidence', 0))

                    if plate_number:
                        plate_number_cleaned = "".join(filter(str.isalnum, plate_number)).upper()
                        print(f"Matrícula reconocida por API: '{plate_number_cleaned}' (Confianza: {confidence:.2f})")
                        recognized_plate = plate_number_cleaned
                        break
                    else:
                        print("La API no devolvió una matrícula en los resultados.")
                else:
                    print("La API no encontró ninguna matrícula en la imagen.")
                    if 'error' in data:
                        print(f"Error de la API: {data['error']}")

            except requests.exceptions.RequestException as e:
                print(f"Error de red o al contactar la API: {e}")
            except ValueError as e:
                print(f"Error al procesar la respuesta de la API (JSON inválido): {e}")
            except Exception as e:
                print(f"Error inesperado durante la llamada a la API: {e}")

            if not recognized_plate:
                print("Intente de nuevo o presione 'q' para salir.")

        elif key == ord('q'):
            print("Reconocimiento de matrícula cancelado por el usuario.")
            break

    cap.release()
    cv2.destroyAllWindows()
    return recognized_plate