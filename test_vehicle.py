import unittest
from vehicle import Vehicle, VehicleType

class TestVehicle(unittest.TestCase):
    """
    Unit tests for the Vehicle class, focusing on duration and fee calculations.
    """

    def setUp(self):
        """
        Set up common constants for tests.
        Using relative millisecond timestamps for reproducibility.
        """
        self.ms_in_minute = 60 * 1000
        self.ms_in_hour = 60 * self.ms_in_minute

        # Define some fixed time points for consistent testing
        # These are arbitrary millisecond values, their difference is what matters.
        self.time_start_millis = 1000000000  # An arbitrary start time in ms
        
        # 10:00 AM to 11:30 AM -> 90 minutes
        self.time_checkout_90_min_later = self.time_start_millis + (90 * self.ms_in_minute)
        
        # 10:00 AM to 11:15 AM -> 75 minutes
        self.time_checkout_75_min_later = self.time_start_millis + (75 * self.ms_in_minute)

        # 10:00 AM to 10:00 AM -> 0 minutes
        self.time_checkout_0_min_later = self.time_start_millis # Same as start time

        # For negative duration scenario (check_out < check_in)
        self.time_checkout_before_start = self.time_start_millis - (30 * self.ms_in_minute)


    def test_calculate_parking_duration_in_minutes(self):
        """
        Test that parking duration is calculated correctly in minutes.
        Example: 90 minutes.
        """
        vehicle = Vehicle("TEST001", VehicleType.COCHE, self.time_start_millis, self.time_checkout_90_min_later)
        self.assertEqual(vehicle.calculate_parking_duration_in_minutes(), 90)

    def test_calculate_parking_duration_zero_minutes(self):
        """
        Test parking duration when check-in and check-out times are the same.
        """
        vehicle = Vehicle("TEST000", VehicleType.MOTO, self.time_start_millis, self.time_checkout_0_min_later)
        self.assertEqual(vehicle.calculate_parking_duration_in_minutes(), 0)

    def test_calculate_parking_duration_negative_scenario(self):
        """
        Test parking duration when check-out time is before check-in time (should result in 0).
        """
        vehicle = Vehicle("TESTNEG", VehicleType.FURGONETA, self.time_start_millis, self.time_checkout_before_start)
        self.assertEqual(vehicle.calculate_parking_duration_in_minutes(), 0)

    def test_calculate_parking_fee_coche(self):
        """
        Test parking fee calculation for COCHE type (1.5 €/hour).
        Duration: 90 minutes = 1.5 hours. Fee = 1.5 * 1.5 = 2.25 €
        """
        vehicle = Vehicle("CAR-001", VehicleType.COCHE, self.time_start_millis, self.time_checkout_90_min_later)
        self.assertAlmostEqual(vehicle.calculate_parking_fee(), 2.25, places=2)

    def test_calculate_parking_fee_moto(self):
        """
        Test parking fee calculation for MOTO type (1.0 €/hour).
        Duration: 90 minutes = 1.5 hours. Fee = 1.5 * 1.0 = 1.50 €
        """
        vehicle = Vehicle("MOTO-001", VehicleType.MOTO, self.time_start_millis, self.time_checkout_90_min_later)
        self.assertAlmostEqual(vehicle.calculate_parking_fee(), 1.50, places=2)

    def test_calculate_parking_fee_furgoneta(self):
        """
        Test parking fee calculation for FURGONETA type (2.0 €/hour).
        Duration: 90 minutes = 1.5 hours. Fee = 1.5 * 2.0 = 3.00 €
        """
        vehicle = Vehicle("VAN-001", VehicleType.FURGONETA, self.time_start_millis, self.time_checkout_90_min_later)
        self.assertAlmostEqual(vehicle.calculate_parking_fee(), 3.00, places=2)

    def test_calculate_parking_fee_partial_hour(self):
        """
        Test fee calculation with partial hours (e.g., 1h 15min = 75 minutes = 1.25 hours).
        For COCHE (1.5 €/hour): Fee = 1.25 * 1.5 = 1.875 €
        """
        vehicle = Vehicle("CAR-002", VehicleType.COCHE, self.time_start_millis, self.time_checkout_75_min_later)
        # 1.25 hours * 1.5 €/hour = 1.875 €
        self.assertAlmostEqual(vehicle.calculate_parking_fee(), 1.875, places=3) 

    def test_calculate_parking_fee_zero_duration(self):
        """
        Test that parking fee is zero for zero duration.
        """
        vehicle = Vehicle("ZERO-FEE", VehicleType.COCHE, self.time_start_millis, self.time_checkout_0_min_later)
        self.assertAlmostEqual(vehicle.calculate_parking_fee(), 0.0, places=2)

    def test_calculate_parking_fee_negative_duration_scenario(self):
        """
        Test that parking fee is zero when check-out is before check-in (duration becomes 0).
        """
        vehicle = Vehicle("NEG-FEE", VehicleType.MOTO, self.time_start_millis, self.time_checkout_before_start)
        self.assertAlmostEqual(vehicle.calculate_parking_fee(), 0.0, places=2)

if __name__ == '__main__':
    unittest.main()