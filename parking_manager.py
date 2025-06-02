import time
from datetime import datetime
import csv
from typing import Optional
import sqlite3

from vehicle import Vehicle, VehicleType


class ParkingManager:

    def __init__(self, db_name, capacity):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_tables()
        # Formateador para mostrar fechas y horas de forma legible.
        self.date_format_str: str = "%d/%m/%Y %H:%M:%S"
        self.capacity = capacity

    def _create_tables(self):
        """Crea las tablas de la base de datos si no existen."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS parked_vehicles (
                plate TEXT PRIMARY KEY,
                vehicle_type_name TEXT NOT NULL,
                check_in_time INTEGER NOT NULL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicle_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plate TEXT NOT NULL,
                vehicle_type_name TEXT NOT NULL,
                check_in_time INTEGER NOT NULL,
                check_out_time INTEGER NOT NULL,
                duration_minutes INTEGER NOT NULL,
                fee REAL NOT NULL
            )
        """)
        self.conn.commit()

    def _vehicle_from_row(self, row: tuple, is_history: bool = False) -> Optional[Vehicle]:
        """Convierte una fila de la base de datos en un objeto Vehicle."""
        if not row:
            return None
        plate, vehicle_type_name, check_in_time = row[0], row[1], row[2]
        check_out_time = row[3] if is_history and len(row) > 3 else None
        try:
            vehicle_type_enum = VehicleType[vehicle_type_name]
            return Vehicle(plate, vehicle_type_enum, check_in_time, check_out_time)
        except KeyError:
            print(f"Error: Tipo de vehículo desconocido '{vehicle_type_name}' en la base de datos para la matrícula {plate}.")
            return None
        
    def check_capacity(self) -> bool: # Utilizado por Flask
        self.cursor.execute("SELECT COUNT(*) FROM parked_vehicles")
        current_count = self.cursor.fetchone()[0]
        return not current_count >= self.capacity
    def check_in_vehicle(self, plate: str, vehicle_type: VehicleType) -> str: # Modificado para Flask
        self.cursor.execute("SELECT plate FROM parked_vehicles WHERE plate = ?", (plate,))
        if self.cursor.fetchone():
            return f"Error: El vehículo con matrícula {plate} ya está en el parking."
        
        check_in_time_millis = int(time.time() * 1000)
    
        try:
            self.cursor.execute(
                "INSERT INTO parked_vehicles (plate, vehicle_type_name, check_in_time) VALUES (?, ?, ?)",
                (plate, vehicle_type.name, check_in_time_millis)
            )
            self.conn.commit()
            check_in_dt = datetime.fromtimestamp(check_in_time_millis / 1000)
            return f"Vehículo {plate} ({vehicle_type.name}) registrada. Hora de entrada: {check_in_dt.strftime(self.date_format_str)}"
        except sqlite3.Error as e:
            return f"Error de base de datos al registrar entrada: {e}"

    def check_out_vehicle(self, plate: str) -> tuple[str, Optional[float]]: # Modificado para Flask
        """
        Registra la salida de un vehículo del aparcamiento.
        Calcula la duración de la estancia y el coste.
        Args:
            plate: La matrícula del vehículo a retirar.
        Returns:
            El objeto Vehicle que ha salido, o None si no se encontró el vehículo.
        """
        self.cursor.execute("SELECT plate, vehicle_type_name, check_in_time FROM parked_vehicles WHERE plate = ?", (plate,))
        row = self.cursor.fetchone()

        if not row:
            print(f"Error: El vehículo con matrícula {plate} no se encuentra en el parking.")
            return f"Error: El vehículo con matrícula {plate} no se encuentra en el parking.", None
    
        db_plate, db_vehicle_type_name, db_check_in_time = row
        try:
            vehicle_type_enum = VehicleType[db_vehicle_type_name]
        except KeyError:
            print(f"Error: Tipo de vehículo desconocido '{db_vehicle_type_name}' para la matrícula {db_plate} al salir.")
            return None

        current_check_out_time = int(time.time() * 1000)
        temp_vehicle_for_calc = Vehicle(db_plate, vehicle_type_enum, db_check_in_time, current_check_out_time)
        
        duration_minutes = temp_vehicle_for_calc.calculate_parking_duration_in_minutes()
        fee = temp_vehicle_for_calc.calculate_parking_fee()

        try:
            self.cursor.execute("DELETE FROM parked_vehicles WHERE plate = ?", (plate,))
            self.cursor.execute(
                """INSERT INTO vehicle_history 
                   (plate, vehicle_type_name, check_in_time, check_out_time, duration_minutes, fee) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (db_plate, db_vehicle_type_name, db_check_in_time, current_check_out_time, duration_minutes, fee)
            )
            self.conn.commit()

            check_in_dt = datetime.fromtimestamp(db_check_in_time / 1000)
            check_out_dt = datetime.fromtimestamp(current_check_out_time / 1000)
            message = (
                f"Salida registrada para {db_plate} ({db_vehicle_type_name}).\n"
                f"  Hora de entrada: {check_in_dt.strftime(self.date_format_str)}\n"
                f"  Hora de salida: {check_out_dt.strftime(self.date_format_str)}\n"
                f"  Duración: {duration_minutes} minutos\n"
                f"  Coste: €{fee:.2f}"
            )
            return message, fee
        except sqlite3.Error as e:
            self.conn.rollback() # Revertir cambios si algo falla
            return f"Error de base de datos al registrar salida: {e}", None

    def get_current_vehicles(self):
        """Muestra una lista de todos los vehículos que se encuentran actualmente en el aparcamiento."""
        self.cursor.execute("SELECT plate, vehicle_type_name, check_in_time FROM parked_vehicles ORDER BY check_in_time ASC")
        rows = self.cursor.fetchall()

        if not rows:
            print("No hay vehículos actualmente en el parking.")
            return
        print("\n--- Vehículos Actualmente en el Parking ---")
        for i, row in enumerate(rows):
            vehicle = self._vehicle_from_row(row, is_history=False)
            if vehicle:
                ongoing_duration = vehicle.calculate_parking_duration_in_minutes() # Duración hasta el momento actual
                check_in_dt = datetime.fromtimestamp(vehicle.check_in_time / 1000)
                print(f"{i + 1}. Matrícula: {vehicle.plate}, Tipo: {vehicle.type.name}, Hora de Entrada: {check_in_dt.strftime(self.date_format_str)}, Duración actual: {ongoing_duration} min.")
        print("----------------------------------------")

    def get_vehicle_history(self):
        """Muestra un historial de todos los vehículos que han salido del aparcamiento."""
        self.cursor.execute(
            "SELECT plate, vehicle_type_name, check_in_time, check_out_time, duration_minutes, fee FROM vehicle_history ORDER BY check_out_time DESC"
        )
        rows = self.cursor.fetchall()

        if not rows:
            print("No hay vehículos en el historial.")
            return
        print("\n--- Historial de Vehículos ---")
        for i, row in enumerate(rows):
            plate, vehicle_type_name, check_in_time, check_out_time, duration_minutes, fee = row
            check_in_dt = datetime.fromtimestamp(check_in_time / 1000)
            check_out_dt = datetime.fromtimestamp(check_out_time / 1000)
            print(f"{i + 1}. Matrícula: {plate}, Tipo: {vehicle_type_name}, Duración: {duration_minutes} min, Coste: €{fee:.2f}")
            print(f"     Entrada: {check_in_dt.strftime(self.date_format_str)}, Salida: {check_out_dt.strftime(self.date_format_str)}")
        print("------------------------------")

    def export_history_to_csv(self, filename: str = "historial.csv") -> Optional[str]: # Modificado para Flask
        """
        Exporta el historial de vehículos a un archivo CSV.

        Args:
            filename (str): El nombre del archivo CSV a crear.
        Returns:
            Optional[str]: La ruta al archivo CSV si la exportación fue exitosa, None en caso contrario.
        """
        self.cursor.execute(
            "SELECT plate, vehicle_type_name, check_in_time, check_out_time, duration_minutes, fee FROM vehicle_history ORDER BY check_out_time ASC"
        )
        rows = self.cursor.fetchall()

        if not rows:
            return None

        # Definir los encabezados para el archivo CSV
        headers = ["Matricula", "TipoVehiculo", "HoraEntrada", "HoraSalida", "DuracionMinutos", "CosteEuros"]
        
        # Usar un formato de fecha más estándar para CSV si se desea, o mantener el actual.
        csv_date_format = "%Y-%m-%d %H:%M:%S" 

        try:
            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(headers) # Escribir los encabezados.

                for row_data in rows:
                    plate, vehicle_type_name, check_in_time, check_out_time, duration_minutes, fee = row_data
                    row = [
                                                plate,
                        vehicle_type_name,
                        datetime.fromtimestamp(check_in_time / 1000).strftime(csv_date_format),
                        datetime.fromtimestamp(check_out_time / 1000).strftime(csv_date_format),
                        duration_minutes,
                        f"{fee:.2f}" # Formatear coste a dos decimales.
                    ]
                    writer.writerow(row)
            return filename
        except IOError as e:
            # El manejo de errores se hará en Flask con flash()
            return None
        
    def close_db(self):
        """Cierra la conexión a la base de datos."""
        if self.conn:
            self.conn.close()
            # print("Conexión a la base de datos cerrada.") # No es necesario para Flask

    # --- Métodos adicionales para Flask ---

    def get_current_occupancy(self) -> int:
        """Devuelve el número actual de vehículos en el parking."""
        self.cursor.execute("SELECT COUNT(*) FROM parked_vehicles")
        current_count = self.cursor.fetchone()[0]
        return current_count

    def get_current_vehicles_data(self) -> list[dict]:
        """Devuelve una lista de diccionarios con los vehículos actuales para Flask."""
        self.cursor.execute("SELECT plate, vehicle_type_name, check_in_time FROM parked_vehicles ORDER BY check_in_time ASC")
        rows = self.cursor.fetchall()
        vehicles = []
        for row_data in rows:
            plate, vehicle_type_name, check_in_time_millis = row_data
            check_in_dt = datetime.fromtimestamp(check_in_time_millis / 1000)
            vehicles.append({
                "plate": plate,
                "vehicle_type_name": vehicle_type_name, # Flask usará esto directamente
                "check_in_time": check_in_dt.strftime(self.date_format_str)
            })
        return vehicles

    def get_vehicle_history_data(self) -> list[dict]:
        """Devuelve una lista de diccionarios con el historial de vehículos para Flask."""
        self.cursor.execute(
            "SELECT plate, vehicle_type_name, check_in_time, check_out_time, duration_minutes, fee FROM vehicle_history ORDER BY check_out_time DESC"
        )
        rows = self.cursor.fetchall()
        history = []
        for plate_val, vt_name, ci_time, co_time, duration, cost in rows:
            history.append({
                "plate": plate_val,
                "vehicle_type_name": vt_name,
                "check_in_time": datetime.fromtimestamp(ci_time / 1000).strftime(self.date_format_str),
                "check_out_time": datetime.fromtimestamp(co_time / 1000).strftime(self.date_format_str) if co_time else None,
                "duration_minutes": duration,
                "total_cost": cost
            })
        return history