import unittest
from unittest.mock import patch, MagicMock, mock_open, call
import sqlite3
import time
import os
from datetime import datetime

from parking_manager import ParkingManager
from vehicle import Vehicle, VehicleType

# Constantes de tiempo para pruebas (milisegundos desde la época)
FIXED_TIME_MS_BASE = 1678886400000  # Ejemplo: 15 Mar 2023 12:00:00 GMT
ONE_HOUR_MS = 60 * 60 * 1000
NINETY_MINUTES_MS = 90 * 60 * 1000

class TestParkingManager(unittest.TestCase):

    def setUp(self):
        """Configura el entorno para cada prueba."""
        self.db_name = ":memory:"  # Usar base de datos en memoria para tests
        self.capacity = 3
        self.invoices_test_dir = "test_invoices_temp"

        # Mockear time.time() para tener tiempos predecibles
        self.patcher_time = patch('time.time', MagicMock(return_value=FIXED_TIME_MS_BASE / 1000))
        self.mock_time = self.patcher_time.start()

        # Mockear os.makedirs para evitar crear directorios reales durante las pruebas de __init__
        self.patcher_makedirs = patch('os.makedirs')
        self.mock_makedirs = self.patcher_makedirs.start()

        self.parking_manager = ParkingManager(self.db_name, self.capacity)
        self.parking_manager.invoices_dir = self.invoices_test_dir # Sobrescribir para tests
        
        # Detener el mock de makedirs después de la inicialización de ParkingManager
        # para que _generate_invoice_pdf pueda crear su directorio si es necesario (aunque lo mockearemos)
        self.patcher_makedirs.stop() 
        # Re-crear el mock_makedirs para _generate_invoice_pdf si es necesario para pruebas específicas de ese método
        # o mockearlo directamente en esa prueba.

        # Asegurarse de que las tablas se creen en la BD en memoria
        self.parking_manager._create_tables()

    def tearDown(self):
        """Limpia después de cada prueba."""
        self.patcher_time.stop()
        # self.patcher_makedirs.stop() # Asegurarse que está detenido si no se hizo antes
        self.parking_manager.close_db()
        # Limpiar directorio de facturas de prueba si se creó
        if os.path.exists(self.invoices_test_dir):
            for f in os.listdir(self.invoices_test_dir):
                os.remove(os.path.join(self.invoices_test_dir, f))
            os.rmdir(self.invoices_test_dir)

    def test_create_tables_idempotent(self):
        try:
            self.parking_manager._create_tables() # Llamar de nuevo
        except Exception as e:
            self.fail(f"_create_tables lanzó una excepción inesperada al llamarse de nuevo: {e}")

    def test_check_capacity(self):
        self.assertTrue(self.parking_manager.check_capacity())
        for i in range(self.capacity):
            self.mock_time.return_value = (FIXED_TIME_MS_BASE + i * 1000) / 1000
            self.parking_manager.check_in_vehicle(f"PLATE{i}", VehicleType.COCHE)
        self.assertFalse(self.parking_manager.check_capacity(), "No debería haber capacidad cuando está lleno.")
        self.assertEqual(self.parking_manager.get_current_occupancy(), self.capacity)

    def test_check_in_vehicle_success(self):
        self.mock_time.return_value = FIXED_TIME_MS_BASE / 1000
        plate = "TEST001"
        vehicle_type = VehicleType.COCHE
        msg = self.parking_manager.check_in_vehicle(plate, vehicle_type)

        self.assertIn(f"Vehículo {plate} ({vehicle_type.name}) registrado.", msg)
        self.parking_manager.cursor.execute("SELECT plate, vehicle_type_name, check_in_time FROM parked_vehicles WHERE plate = ?", (plate,))
        row = self.parking_manager.cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], plate)
        self.assertEqual(row[1], vehicle_type.name)
        self.assertEqual(row[2], FIXED_TIME_MS_BASE)
        self.assertEqual(self.parking_manager.get_current_occupancy(), 1)

    def test_check_in_vehicle_already_parked(self):
        plate = "TEST002"
        self.parking_manager.check_in_vehicle(plate, VehicleType.MOTO)
        msg = self.parking_manager.check_in_vehicle(plate, VehicleType.MOTO)
        self.assertIn(f"Error: El vehículo con matrícula {plate} ya está en el parking.", msg)
        self.assertEqual(self.parking_manager.get_current_occupancy(), 1) # No debe aumentar

    @patch('parking_manager.ParkingManager._generate_invoice_pdf', return_value=True)
    def test_check_out_vehicle_success(self, mock_generate_pdf):
        plate = "OUT001"
        vehicle_type = VehicleType.COCHE
        check_in_time_ms = FIXED_TIME_MS_BASE

        self.mock_time.return_value = check_in_time_ms / 1000
        self.parking_manager.check_in_vehicle(plate, vehicle_type)

        check_out_time_ms = check_in_time_ms + ONE_HOUR_MS # 1 hora después
        self.mock_time.return_value = check_out_time_ms / 1000

        msg, invoice_file = self.parking_manager.check_out_vehicle(plate)

        expected_duration_minutes = ONE_HOUR_MS // (60 * 1000)
        expected_fee = vehicle_type.hourly_rate * (expected_duration_minutes / 60.0)

        self.assertIn(f"Salida registrada para {plate}", msg)
        self.assertIn(f"Duración: {expected_duration_minutes} minutos", msg)
        self.assertIn(f"Coste: €{expected_fee:.2f}", msg)
        self.assertIsNotNone(invoice_file)
        mock_generate_pdf.assert_called_once()
        
        # Verificar que el vehículo ya no está en parked_vehicles y está en history
        self.parking_manager.cursor.execute("SELECT * FROM parked_vehicles WHERE plate = ?", (plate,))
        self.assertIsNone(self.parking_manager.cursor.fetchone())
        self.parking_manager.cursor.execute("SELECT fee FROM vehicle_history WHERE plate = ?", (plate,))
        self.assertAlmostEqual(self.parking_manager.cursor.fetchone()[0], expected_fee)
        self.assertEqual(self.parking_manager.get_current_occupancy(), 0)

    def test_check_out_vehicle_not_found(self):
        msg, invoice_file = self.parking_manager.check_out_vehicle("NONEXIST")
        self.assertIn("Error: El vehículo con matrícula NONEXIST no se encuentra en el parking.", msg)
        self.assertIsNone(invoice_file)

    @patch('parking_manager.ParkingManager._generate_invoice_pdf', return_value=True)
    def test_check_out_vehicle_unknown_type_in_db(self, mock_generate_pdf):
        plate = "BADTYPEDB"
        self.parking_manager.cursor.execute(
            "INSERT INTO parked_vehicles (plate, vehicle_type_name, check_in_time) VALUES (?, ?, ?)",
            (plate, "INVALIDTYPE", FIXED_TIME_MS_BASE)
        )
        self.parking_manager.conn.commit()

        self.mock_time.return_value = (FIXED_TIME_MS_BASE + ONE_HOUR_MS) / 1000
        msg, invoice_file = self.parking_manager.check_out_vehicle(plate)
        self.assertIn(f"Error: Tipo de vehículo desconocido 'INVALIDTYPE' para la matrícula {plate}", msg)
        self.assertIsNone(invoice_file)
        mock_generate_pdf.assert_not_called()

    @patch('parking_manager.ParkingManager._generate_invoice_pdf', return_value=False) # Simular fallo en PDF
    def test_check_out_vehicle_pdf_generation_fails(self, mock_generate_pdf_fail):
        plate = "PDFFAIL01"
        self.mock_time.return_value = FIXED_TIME_MS_BASE / 1000
        self.parking_manager.check_in_vehicle(plate, VehicleType.MOTO)
        self.mock_time.return_value = (FIXED_TIME_MS_BASE + ONE_HOUR_MS) / 1000
        
        msg, invoice_file = self.parking_manager.check_out_vehicle(plate)
        self.assertIn(f"Salida registrada para {plate}", msg)
        self.assertIn("Error al generar la factura PDF.", msg)
        self.assertIsNone(invoice_file) # No se devuelve nombre de archivo
        mock_generate_pdf_fail.assert_called_once()

    @patch('parking_manager.FPDF')
    def test_generate_invoice_pdf_success(self, MockFPDF):
        mock_pdf_instance = MockFPDF.return_value
        mock_pdf_instance.output = MagicMock()
        os.makedirs(self.invoices_test_dir, exist_ok=True) # Crear dir para esta prueba

        vehicle = Vehicle("INV001", VehicleType.FURGONETA, FIXED_TIME_MS_BASE, FIXED_TIME_MS_BASE + ONE_HOUR_MS)
        filepath = os.path.join(self.invoices_test_dir, "test_invoice.pdf")

        result = self.parking_manager._generate_invoice_pdf(
            filepath, vehicle, 2.0, datetime.now(), datetime.now(), 60
        )
        self.assertTrue(result)
        MockFPDF.assert_called_once()
        mock_pdf_instance.output.assert_called_once_with(filepath, "F")

    @patch('parking_manager.FPDF')
    def test_generate_invoice_pdf_failure_exception(self, MockFPDF):
        mock_pdf_instance = MockFPDF.return_value
        mock_pdf_instance.output = MagicMock(side_effect=Exception("PDF Gen Error"))
        os.makedirs(self.invoices_test_dir, exist_ok=True)
        filepath = os.path.join(self.invoices_test_dir, "fail_invoice.pdf")

        with patch('builtins.print') as mock_print:
            result = self.parking_manager._generate_invoice_pdf(
                filepath, Vehicle("INV002", VehicleType.MOTO, 0, 0), 1.0, datetime.now(), datetime.now(), 30
            )
            self.assertFalse(result)
            mock_print.assert_called_with(f"Error al generar el PDF de la factura {filepath}: PDF Gen Error")

    def test_get_current_vehicles_empty(self):
        with patch('builtins.print') as mock_print:
            self.parking_manager.get_current_vehicles()
            mock_print.assert_any_call("No hay vehículos actualmente en el parking.")

    def test_get_current_vehicles_with_data(self):
        self.mock_time.return_value = FIXED_TIME_MS_BASE / 1000
        self.parking_manager.check_in_vehicle("CURR1", VehicleType.COCHE)
        self.mock_time.return_value = (FIXED_TIME_MS_BASE + 30000) / 1000 # 30s después
        self.parking_manager.check_in_vehicle("CURR2", VehicleType.MOTO)

        # Simular que han pasado 60 minutos desde la entrada de CURR1 para el cálculo de duración actual
        self.mock_time.return_value = (FIXED_TIME_MS_BASE + ONE_HOUR_MS) / 1000

        with patch('builtins.print') as mock_print:
            self.parking_manager.get_current_vehicles()
            output = "\n".join(call_args[0][0] for call_args in mock_print.call_args_list if call_args[0])
            self.assertIn("CURR1", output)
            self.assertIn(VehicleType.COCHE.name, output)
            self.assertIn("Duración actual: 60 min.", output) # CURR1
            self.assertIn("CURR2", output)
            self.assertIn(VehicleType.MOTO.name, output)
            # CURR2 entró 30s después de CURR1. Si ahora es 1h después de CURR1, CURR2 lleva 1h - 30s = 3570s = 59.5 min => 59 min
            self.assertIn("Duración actual: 59 min.", output) # CURR2

    def test_get_current_vehicles_data(self):
        self.mock_time.return_value = FIXED_TIME_MS_BASE / 1000
        self.parking_manager.check_in_vehicle("DATA1", VehicleType.FURGONETA)
        check_in_dt_str = datetime.fromtimestamp(FIXED_TIME_MS_BASE / 1000).strftime(self.parking_manager.date_format_str)

        data = self.parking_manager.get_current_vehicles_data()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['plate'], "DATA1")
        self.assertEqual(data[0]['vehicle_type_name'], VehicleType.FURGONETA.name)
        self.assertEqual(data[0]['check_in_time'], check_in_dt_str)

    def test_get_vehicle_history_empty(self):
        with patch('builtins.print') as mock_print:
            self.parking_manager.get_vehicle_history()
            mock_print.assert_any_call("No hay vehículos en el historial.")

    @patch('parking_manager.ParkingManager._generate_invoice_pdf', return_value=True)
    def test_get_vehicle_history_with_data(self, mock_pdf):
        self.mock_time.return_value = FIXED_TIME_MS_BASE / 1000
        self.parking_manager.check_in_vehicle("HIST1", VehicleType.COCHE)
        self.mock_time.return_value = (FIXED_TIME_MS_BASE + NINETY_MINUTES_MS) / 1000 # 1.5 horas después
        self.parking_manager.check_out_vehicle("HIST1")

        with patch('builtins.print') as mock_print:
            self.parking_manager.get_vehicle_history()
            output = "\n".join(call_args[0][0] for call_args in mock_print.call_args_list if call_args[0])
            self.assertIn("HIST1", output)
            self.assertIn("Duración: 90 min", output)
            expected_fee = VehicleType.COCHE.hourly_rate * 1.5
            self.assertIn(f"Coste: €{expected_fee:.2f}", output)

    @patch('parking_manager.ParkingManager._generate_invoice_pdf', return_value=True)
    def test_get_vehicle_history_data(self, mock_pdf):
        self.mock_time.return_value = FIXED_TIME_MS_BASE / 1000
        self.parking_manager.check_in_vehicle("HDATA1", VehicleType.MOTO)
        check_in_dt_str = datetime.fromtimestamp(FIXED_TIME_MS_BASE / 1000).strftime(self.parking_manager.date_format_str)

        checkout_time = FIXED_TIME_MS_BASE + ONE_HOUR_MS
        self.mock_time.return_value = checkout_time / 1000
        self.parking_manager.check_out_vehicle("HDATA1")
        check_out_dt_str = datetime.fromtimestamp(checkout_time / 1000).strftime(self.parking_manager.date_format_str)

        data = self.parking_manager.get_vehicle_history_data()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['plate'], "HDATA1")
        self.assertEqual(data[0]['duration_minutes'], 60)
        self.assertAlmostEqual(data[0]['total_cost'], VehicleType.MOTO.hourly_rate * 1.0)
        self.assertEqual(data[0]['check_in_time'], check_in_dt_str)
        self.assertEqual(data[0]['check_out_time'], check_out_dt_str)

    @patch('parking_manager.ParkingManager._generate_invoice_pdf', return_value=True)
    @patch('builtins.open', new_callable=mock_open)
    @patch('csv.writer')
    def test_export_history_to_csv_success(self, mock_csv_writer, mock_file_open, mock_pdf):
        self.mock_time.return_value = FIXED_TIME_MS_BASE / 1000
        self.parking_manager.check_in_vehicle("CSV1", VehicleType.COCHE)
        self.mock_time.return_value = (FIXED_TIME_MS_BASE + ONE_HOUR_MS) / 1000
        self.parking_manager.check_out_vehicle("CSV1")

        filename = "test_historial.csv"
        result_path = self.parking_manager.export_history_to_csv(filename)

        self.assertEqual(result_path, filename)
        mock_file_open.assert_called_once_with(filename, mode='w', newline='', encoding='utf-8')
        mock_csv_writer.return_value.writerow.assert_any_call(
            ["Matricula", "TipoVehiculo", "HoraEntrada", "HoraSalida", "DuracionMinutos", "CosteEuros"]
        )
        # Verificar datos escritos (simplificado)
        self.assertTrue(mock_csv_writer.return_value.writerow.call_count >= 2)

    def test_export_history_to_csv_no_data(self):
        result_path = self.parking_manager.export_history_to_csv("empty_historial.csv")
        self.assertIsNone(result_path)

    @patch('parking_manager.ParkingManager._generate_invoice_pdf', return_value=True)
    @patch('builtins.open', side_effect=IOError("Disk full"))
    def test_export_history_to_csv_io_error(self, mock_file_open_error, mock_pdf):
        self.mock_time.return_value = FIXED_TIME_MS_BASE / 1000
        self.parking_manager.check_in_vehicle("CSVIO", VehicleType.MOTO)
        self.mock_time.return_value = (FIXED_TIME_MS_BASE + ONE_HOUR_MS) / 1000
        self.parking_manager.check_out_vehicle("CSVIO")

        result_path = self.parking_manager.export_history_to_csv("error_historial.csv")
        self.assertIsNone(result_path)
        mock_file_open_error.assert_called_once()

    def test_vehicle_from_row_parked(self):
        row_data = ("PLATEVFR", VehicleType.COCHE.name, FIXED_TIME_MS_BASE)
        vehicle = self.parking_manager._vehicle_from_row(row_data, is_history=False)
        self.assertIsNotNone(vehicle)
        self.assertEqual(vehicle.plate, "PLATEVFR")
        self.assertEqual(vehicle.type, VehicleType.COCHE)

    def test_vehicle_from_row_history(self):
        row_data = ("PLATEVFR_H", VehicleType.MOTO.name, FIXED_TIME_MS_BASE, FIXED_TIME_MS_BASE + ONE_HOUR_MS)
        vehicle = self.parking_manager._vehicle_from_row(row_data, is_history=True)
        self.assertIsNotNone(vehicle)
        self.assertEqual(vehicle.plate, "PLATEVFR_H")
        self.assertEqual(vehicle.type, VehicleType.MOTO)
        self.assertEqual(vehicle.check_out_time, FIXED_TIME_MS_BASE + ONE_HOUR_MS)

    def test_vehicle_from_row_unknown_type(self):
        row_data = ("BADTYPEVFR", "CAMION", FIXED_TIME_MS_BASE)
        with patch('builtins.print') as mock_print:
            vehicle = self.parking_manager._vehicle_from_row(row_data, is_history=False)
            self.assertIsNone(vehicle)
            mock_print.assert_called_with("Error: Tipo de vehículo desconocido 'CAMION' en la base de datos para la matrícula BADTYPEVFR.")

    def test_get_current_occupancy(self):
        self.assertEqual(self.parking_manager.get_current_occupancy(), 0)
        self.parking_manager.check_in_vehicle("OCCUP1", VehicleType.COCHE)
        self.assertEqual(self.parking_manager.get_current_occupancy(), 1)

    def test_close_db(self):
        # Crear un manager temporal para esta prueba específica de cierre
        temp_manager = ParkingManager(":memory:", 1)
        temp_manager.close_db() # Allow the actual close_db method to run
        self.assertIsNone(temp_manager.conn, "La conexión debería ser None después de cerrarla.")
        
        # Probar que llamar a close_db en una conexión ya cerrada (conn es None) no da error
        try:
            temp_manager.close_db()
        except Exception as e:
            self.fail(f"close_db() en conexión ya cerrada (conn=None) lanzó: {e}")

if __name__ == '__main__':
    unittest.main()