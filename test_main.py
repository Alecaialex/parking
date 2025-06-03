import unittest
from unittest.mock import patch, MagicMock, call

# Asegúrate de que los módulos de tu proyecto estén accesibles.
# Si main.py y vehicle.py están en el mismo directorio que este test,
# los imports directos deberían funcionar.
from main import main, ask_vehicle_type
from vehicle import VehicleType
# ParkingManager será mockeado, por lo que no necesitamos importarlo para usarlo,
# pero sí para que el decorador @patch('main.ParkingManager') lo encuentre.
# from parking_manager import ParkingManager # Necesario para que @patch funcione correctamente

class TestMainCLI(unittest.TestCase):

    @patch('main.input', create=True)
    @patch('main.print', create=True)
    def test_ask_vehicle_type_valid_selection(self, mock_print, mock_input):
        mock_input.return_value = "1" # Simula la selección de COCHE
        result = ask_vehicle_type()
        self.assertEqual(result, VehicleType.COCHE)
        mock_print.assert_any_call("Seleccione el tipo de vehículo:")
        mock_print.assert_any_call(f"1. {VehicleType.COCHE.name} (Tarifa: €{VehicleType.COCHE.hourly_rate:.2f}/hora)")

    @patch('main.input', create=True)
    @patch('main.print', create=True)
    def test_ask_vehicle_type_invalid_number_too_high(self, mock_print, mock_input):
        mock_input.return_value = "99" # Número fuera de rango
        result = ask_vehicle_type()
        self.assertIsNone(result)

    @patch('main.input', create=True)
    @patch('main.print', create=True)
    def test_ask_vehicle_type_invalid_input_text(self, mock_print, mock_input):
        mock_input.return_value = "abc" # Entrada no numérica
        result = ask_vehicle_type()
        self.assertIsNone(result)

    @patch('main.ParkingManager') # Mockea la clase ParkingManager importada en main.py
    @patch('main.input', create=True)
    @patch('main.print', create=True)
    def test_main_check_in_vehicle_success(self, mock_print, mock_input, MockParkingManager):
        mock_pm_instance = MockParkingManager.return_value
        mock_pm_instance.check_capacity.return_value = True
        # La función check_in_vehicle de ParkingManager es la que imprime el mensaje de éxito/error.
        # main.py no lo reimprime.

        # Simular entradas: opción 1 (check-in), matrícula, tipo 1 (COCHE), opción 7 (salir)
        mock_input.side_effect = ["1", "ABC123", "1", "7"]
        main()

        mock_pm_instance.check_capacity.assert_called_once()
        mock_pm_instance.check_in_vehicle.assert_called_once_with("ABC123", VehicleType.COCHE)
        mock_print.assert_any_call("\n--- Registrar Entrada de Vehículo ---") # main.py imprime esto
        mock_print.assert_any_call("\nCerrando el programa.") # main.py imprime esto al salir
        mock_pm_instance.close_db.assert_called_once()

    @patch('main.ParkingManager')
    @patch('main.input', create=True)
    @patch('main.print', create=True)
    def test_main_check_in_vehicle_parking_full(self, mock_print, mock_input, MockParkingManager):
        mock_pm_instance = MockParkingManager.return_value
        mock_pm_instance.check_capacity.return_value = False # Parking lleno

        mock_input.side_effect = ["1", "7"] # Opción 1, luego 7 (salir)
        main()

        mock_pm_instance.check_capacity.assert_called_once()
        mock_print.assert_any_call("Error: El parking está lleno. No se puede registrar la entrada de más vehículos.")
        mock_pm_instance.check_in_vehicle.assert_not_called()

    @patch('main.ParkingManager')
    @patch('main.input', create=True)
    @patch('main.print', create=True)
    def test_main_check_in_vehicle_empty_plate(self, mock_print, mock_input, MockParkingManager):
        mock_pm_instance = MockParkingManager.return_value
        mock_pm_instance.check_capacity.return_value = True
        mock_input.side_effect = ["1", "", "7"] # Opción 1, matrícula vacía, salir
        main()
        mock_print.assert_any_call("Error: La matrícula no puede estar vacía.")
        mock_pm_instance.check_in_vehicle.assert_not_called()

    @patch('main.ParkingManager')
    @patch('main.input', create=True)
    @patch('main.print', create=True)
    def test_main_check_in_vehicle_invalid_type_selection(self, mock_print, mock_input, MockParkingManager):
        mock_pm_instance = MockParkingManager.return_value
        mock_pm_instance.check_capacity.return_value = True
        mock_input.side_effect = ["1", "DEF456", "xyz", "7"] # Opción 1, matrícula, tipo inválido, salir
        main()
        mock_print.assert_any_call("Error: Tipo de vehículo no válido.")
        mock_pm_instance.check_in_vehicle.assert_not_called()

    @patch('main.ParkingManager')
    @patch('main.input', create=True)
    @patch('main.print', create=True)
    def test_main_check_out_vehicle(self, mock_print, mock_input, MockParkingManager):
        mock_pm_instance = MockParkingManager.return_value
        # check_out_vehicle de ParkingManager imprime sus propios mensajes.
        # main.py no reimprime el mensaje de éxito/error de check_out_vehicle.

        mock_input.side_effect = ["2", "GHI789", "7"] # Opción 2 (check-out), matrícula, salir
        main()
        mock_pm_instance.check_out_vehicle.assert_called_once_with("GHI789")
        mock_print.assert_any_call("\n--- Registrar Salida de Vehículo ---")

    @patch('main.ParkingManager')
    @patch('main.input', create=True)
    @patch('main.print', create=True)
    def test_main_get_current_vehicles(self, mock_print, mock_input, MockParkingManager):
        mock_pm_instance = MockParkingManager.return_value
        mock_input.side_effect = ["3", "7"] # Opción 3, salir
        main()
        mock_pm_instance.get_current_vehicles.assert_called_once()

    @patch('main.ParkingManager')
    @patch('main.input', create=True)
    @patch('main.print', create=True)
    def test_main_get_vehicle_history(self, mock_print, mock_input, MockParkingManager):
        mock_pm_instance = MockParkingManager.return_value
        mock_input.side_effect = ["4", "7"] # Opción 4, salir
        main()
        mock_pm_instance.get_vehicle_history.assert_called_once()

    @patch('main.ParkingManager')
    @patch('main.input', create=True)
    @patch('main.print', create=True)
    def test_main_export_csv(self, mock_print, mock_input, MockParkingManager):
        mock_pm_instance = MockParkingManager.return_value
        mock_input.side_effect = ["5", "7"] # Opción 5, salir
        main()
        mock_pm_instance.export_history_to_csv.assert_called_once() # main.py no especifica nombre de archivo
        mock_print.assert_any_call("\n--- Exportar Historial a CSV ---")

    @patch('main.recognize_plate_from_webcam', return_value="REC123")
    @patch('main.ParkingManager')
    @patch('main.input', create=True)
    @patch('main.print', create=True)
    def test_main_check_in_webcam_success(self, mock_print, mock_input, MockParkingManager, mock_recognize_plate):
        mock_pm_instance = MockParkingManager.return_value
        mock_pm_instance.check_capacity.return_value = True

        mock_input.side_effect = ["6", "2", "7"] # Opción 6 (webcam), tipo 2 (MOTO), salir
        main()

        mock_recognize_plate.assert_called_once()
        mock_pm_instance.check_capacity.assert_called_once()
        mock_pm_instance.check_in_vehicle.assert_called_once_with("REC123", VehicleType.MOTO)
        mock_print.assert_any_call("\n--- Registrar Entrada con Reconocimiento de Matrícula (Webcam) ---")

    @patch('main.recognize_plate_from_webcam', return_value=None) # Simula fallo en reconocimiento
    @patch('main.ParkingManager')
    @patch('main.input', create=True)
    @patch('main.print', create=True)
    def test_main_check_in_webcam_recognition_fails(self, mock_print, mock_input, MockParkingManager, mock_recognize_plate):
        mock_pm_instance = MockParkingManager.return_value
        mock_pm_instance.check_capacity.return_value = True

        mock_input.side_effect = ["6", "7"] # Opción 6, luego salir
        main()

        mock_recognize_plate.assert_called_once()
        mock_print.assert_any_call("No se pudo reconocer la matrícula o la operación fue cancelada.")
        mock_pm_instance.check_in_vehicle.assert_not_called()

    @patch('main.ParkingManager')
    @patch('main.input', create=True)
    @patch('main.print', create=True)
    def test_main_exit_program(self, mock_print, mock_input, MockParkingManager):
        mock_pm_instance = MockParkingManager.return_value
        mock_input.return_value = "7" # Opción 7 (salir)
        main()
        mock_print.assert_any_call("\nCerrando el programa.")
        mock_pm_instance.close_db.assert_called_once()

    @patch('main.ParkingManager')
    @patch('main.input', create=True)
    @patch('main.print', create=True)
    def test_main_invalid_menu_choice(self, mock_print, mock_input, MockParkingManager):
        mock_input.side_effect = ["99", "7"] # Opción inválida, luego salir
        main()
        mock_print.assert_any_call("Opción no válida. Introduce un número entre 1 y 7.")

if __name__ == '__main__':
    unittest.main()