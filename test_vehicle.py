import unittest
from vehicle import Vehicle, VehicleType # Asegúrate de que vehicle.py esté accesible

# Constantes para facilitar la lectura de tiempos en milisegundos
MS_IN_MINUTE = 60 * 1000
MS_IN_HOUR = 60 * MS_IN_MINUTE

class TestVehicleCalculations(unittest.TestCase):

    def test_calculate_parking_duration_in_minutes(self):
        """
        Prueba el cálculo de la duración de la estancia en minutos.
        """
        # Caso 1: Duración de 90 minutos (ej: 10:00 a 11:30)
        check_in_1 = 0  # Tiempo de entrada base en ms
        check_out_1 = 90 * MS_IN_MINUTE # 90 minutos después, en ms
        vehicle1 = Vehicle("PLATE1", VehicleType.COCHE, check_in_1, check_out_1)
        self.assertEqual(vehicle1.calculate_parking_duration_in_minutes(), 90, "La duración debería ser de 90 minutos.")

        # Caso 2: Duración de 0 minutos
        check_in_2 = 1000 # Cualquier tiempo base
        check_out_2 = 1000 # Mismo tiempo que la entrada
        vehicle2 = Vehicle("PLATE2", VehicleType.MOTO, check_in_2, check_out_2)
        self.assertEqual(vehicle2.calculate_parking_duration_in_minutes(), 0, "La duración debería ser de 0 minutos.")

        # Caso 3: Hora de salida anterior a la hora de entrada (debería ser 0 según la implementación actual)
        check_in_3 = 1 * MS_IN_MINUTE # 1 minuto
        check_out_3 = 0 # Antes de la entrada
        vehicle3 = Vehicle("PLATE3", VehicleType.FURGONETA, check_in_3, check_out_3)
        self.assertEqual(vehicle3.calculate_parking_duration_in_minutes(), 0, "La duración debería ser 0 si la salida es antes de la entrada.")

        # Caso 4: Duración de 1 minuto
        check_in_4 = 0
        check_out_4 = 1 * MS_IN_MINUTE # 1 minuto después
        vehicle4 = Vehicle("PLATE4", VehicleType.COCHE, check_in_4, check_out_4)
        self.assertEqual(vehicle4.calculate_parking_duration_in_minutes(), 1, "La duración debería ser de 1 minuto.")

        # Caso 5: Duración de 75 minutos (1 hora y 15 minutos)
        check_in_5 = 0
        check_out_5 = 75 * MS_IN_MINUTE # 75 minutos después
        vehicle5 = Vehicle("PLATE5", VehicleType.COCHE, check_in_5, check_out_5)
        self.assertEqual(vehicle5.calculate_parking_duration_in_minutes(), 75, "La duración debería ser de 75 minutos.")

    def test_calculate_parking_fee_coche(self):
        """
        Prueba el cálculo del coste para vehículos tipo COCHE (1.5 €/hora).
        """
        check_in_time = 0 # Tiempo de entrada base

        # Caso 1: 1 hora (60 minutos)
        vehicle_1h = Vehicle("COCHE1", VehicleType.COCHE, check_in_time, 1 * MS_IN_HOUR)
        self.assertAlmostEqual(vehicle_1h.calculate_parking_fee(), 1.5 * 1.0, msg="Coste para COCHE 1 hora incorrecto.")

        # Caso 2: 1.5 horas (90 minutos)
        vehicle_1_5h = Vehicle("COCHE2", VehicleType.COCHE, check_in_time, int(1.5 * MS_IN_HOUR))
        self.assertAlmostEqual(vehicle_1_5h.calculate_parking_fee(), 1.5 * 1.5, msg="Coste para COCHE 1.5 horas incorrecto.") # 2.25

        # Caso 3: 1.25 horas (75 minutos) - manejo de minutos parciales
        vehicle_1_25h = Vehicle("COCHE3", VehicleType.COCHE, check_in_time, int(1.25 * MS_IN_HOUR)) # 75 minutos
        self.assertAlmostEqual(vehicle_1_25h.calculate_parking_fee(), 1.5 * 1.25, msg="Coste para COCHE 1.25 horas incorrecto.") # 1.875

        # Caso 4: 0 minutos
        vehicle_0m = Vehicle("COCHE4", VehicleType.COCHE, check_in_time, check_in_time) # 0 duración
        self.assertAlmostEqual(vehicle_0m.calculate_parking_fee(), 0.0, msg="Coste para COCHE 0 minutos incorrecto.")

    def test_calculate_parking_fee_moto(self):
        """
        Prueba el cálculo del coste para vehículos tipo MOTO (1.0 €/hora).
        """
        check_in_time = 0 # Tiempo de entrada base

        # Caso 1: 2 horas (120 minutos)
        vehicle_2h = Vehicle("MOTO1", VehicleType.MOTO, check_in_time, 2 * MS_IN_HOUR)
        self.assertAlmostEqual(vehicle_2h.calculate_parking_fee(), 1.0 * 2.0, msg="Coste para MOTO 2 horas incorrecto.")

        # Caso 2: 0.5 horas (30 minutos)
        vehicle_0_5h = Vehicle("MOTO2", VehicleType.MOTO, check_in_time, int(0.5 * MS_IN_HOUR))
        self.assertAlmostEqual(vehicle_0_5h.calculate_parking_fee(), 1.0 * 0.5, msg="Coste para MOTO 0.5 horas incorrecto.") # 0.5

    def test_calculate_parking_fee_furgoneta(self):
        """
        Prueba el cálculo del coste para vehículos tipo FURGONETA (2.0 €/hora).
        """
        check_in_time = 0 # Tiempo de entrada base

        # Caso 1: 0.75 horas (45 minutos)
        vehicle_0_75h = Vehicle("FURGO1", VehicleType.FURGONETA, check_in_time, int(0.75 * MS_IN_HOUR))
        self.assertAlmostEqual(vehicle_0_75h.calculate_parking_fee(), 2.0 * 0.75, msg="Coste para FURGONETA 0.75 horas incorrecto.") # 1.5

        # Caso 2: 2.5 horas (150 minutos)
        vehicle_2_5h = Vehicle("FURGO2", VehicleType.FURGONETA, check_in_time, int(2.5 * MS_IN_HOUR))
        self.assertAlmostEqual(vehicle_2_5h.calculate_parking_fee(), 2.0 * 2.5, msg="Coste para FURGONETA 2.5 horas incorrecto.") # 5.0

if __name__ == '__main__':
    unittest.main()