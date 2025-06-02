from typing import Optional

from parking_manager import ParkingManager
from vehicle import VehicleType
# Importar la nueva función de reconocimiento de matrículas
try:
    from plate_recognizer import recognize_plate_from_webcam_api as recognize_plate_from_webcam
except ImportError: # Manejar el caso donde las dependencias de OCR no estén instaladas
    recognize_plate_from_webcam = None


def ask_vehicle_type() -> Optional[VehicleType]:
    """
    Obtiene y muestra al usuario las opciones de tipo de vehículo y solicita una selección, luego la devuelve
    Si la entrada no es válida, devuelve None, cancelando la selección
    """
    print("Seleccione el tipo de vehículo:")
    vehicle_types = list(VehicleType)
    for i, vt in enumerate(vehicle_types):
        print(f"{i + 1}. {vt.name} (Tarifa: €{vt.hourly_rate:.2f}/hora)")
    
    choice = input("Introduzca el número correspondiente al tipo de vehículo: ")
    
    try:
        choice_idx = int(choice)
        if 1 <= choice_idx <= len(vehicle_types):
            return vehicle_types[choice_idx - 1]
        else:
            return None
    except ValueError:
        return None


def main():
    parking_manager = ParkingManager(db_name="parking_system.db", capacity=2)

    while True:
        # Mostrar el menú principal
        print("\n--- Menú Principal ---")
        print("1. Registrar entrada de vehículo")
        print("2. Registrar salida de vehículo")
        print("3. Ver vehículos actualmente en el parking")
        print("4. Ver historial de vehículos")
        print("5. Exportar historial a CSV")
        print("6. Registrar entrada con reconocimiento de matrícula (webcam)")
        print("7. Salir del programa")

        choice = input("Elige una opción (1-7): ")

        try:
            choice = int(choice)
        except ValueError:
            choice = -1

        if choice == 1:
            print("\n--- Registrar Entrada de Vehículo ---")
            if not parking_manager.check_capacity():
                print("Error: El parking está lleno. No se puede registrar la entrada de más vehículos.")
                continue

            plate = input("Introduce la matrícula del vehículo: ").strip().upper()
            if not plate:
                print("Error: La matrícula no puede estar vacía.")
                continue

            vehicle_type = ask_vehicle_type()
            if vehicle_type:
                parking_manager.check_in_vehicle(plate, vehicle_type)
            else:
                print("Error: Tipo de vehículo no válido.")


        elif choice == 2:
            print("\n--- Registrar Salida de Vehículo ---")
            plate = input("Introduce la matrícula del vehículo a retirar: ").strip().upper()
            if not plate:
                print("Error: La matrícula no puede estar vacía.")
                continue
            parking_manager.check_out_vehicle(plate)

        elif choice == 3:
            parking_manager.get_current_vehicles()

        elif choice == 4:
            parking_manager.get_vehicle_history()

        elif choice == 5:
            print("\n--- Exportar Historial a CSV ---")
            parking_manager.export_history_to_csv()

        elif choice == 6:
            print("\n--- Registrar Entrada con Reconocimiento de Matrícula (Webcam) ---")
            if recognize_plate_from_webcam is None:
                print("Error: La funcionalidad de reconocimiento de matrículas no está disponible.")
                print("Asegúrate de tener OpenCV (cv2) y Pytesseract instalados,")
                print("y el motor Tesseract OCR configurado en tu sistema.")
                continue

            if not parking_manager.check_capacity():
                print("Error: El parking está lleno. No se puede registrar la entrada de más vehículos.")
                continue

            plate = recognize_plate_from_webcam()
            if not plate: # Si no se reconoció o se canceló
                print("No se pudo reconocer la matrícula o la operación fue cancelada.")
                continue

            vehicle_type = ask_vehicle_type()
            if vehicle_type:
                parking_manager.check_in_vehicle(plate, vehicle_type)
            else:
                print("Error: Tipo de vehículo no válido.")
        elif choice == 7:
            print("\nCerrando el programa.")
            parking_manager.close_db()
            break
        else:
            print("Opción no válida. Introduce un número entre 1 y 7.")


if __name__ == "__main__":
    main()