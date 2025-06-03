from enum import Enum
from typing import Optional
import time


class VehicleType(Enum):
    """Enum de tipos de vehículos con sus tarifas por hora."""
    COCHE = 1.5
    MOTO = 1.0
    FURGONETA = 2.0

    @property
    def hourly_rate(self) -> float:
        return self.value

class Vehicle:
    """Atributos de la clase Vehicle::
        plate str: La matrícula del vehículo
        type VehicleType: El tipo de vehículo
        check_in_time int: La hora en que el vehículo entró al parking (ms desde la época)
        check_out_time Optional[int]: La hora en que el vehículo salió del parking (ms desde la época)"""
    def __init__(self, plate: str, vehicle_type: VehicleType, check_in_time: int, check_out_time: Optional[int] = None):
        self.plate: str = plate
        self.type: VehicleType = vehicle_type
        self.check_in_time: int = check_in_time
        self.check_out_time: Optional[int] = check_out_time

    def calculate_parking_duration_in_minutes(self) -> int:
        """Calcula la duración de la estancia en minutos.
        Si check_out_time es None, usa la hora actual
        para calcular la duración actual."""
        end_time = self.check_out_time if self.check_out_time is not None else int(time.time() * 1000)
        duration_millis = end_time - self.check_in_time
        return int(duration_millis / 60000) if duration_millis >= 0 else 0

    def calculate_parking_fee(self) -> float:
        """Calcula la tarifa total de estacionamiento."""
        duration_in_minutes = self.calculate_parking_duration_in_minutes()
        duration_in_hours = duration_in_minutes / 60.0
        return duration_in_hours * self.type.hourly_rate