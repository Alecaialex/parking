from flask import Flask, render_template, request, redirect, url_for, flash, send_file, after_this_request, send_from_directory, Markup
from parking_manager import ParkingManager
from vehicle import VehicleType
from typing import Optional
import os # Necesario para la exportación CSV

# Importar la nueva función de reconocimiento de matrículas
try:
    from plate_recognizer import recognize_plate_from_webcam_api as recognize_plate_from_webcam
except ImportError: # Manejar el caso donde las dependencias de OCR no estén instaladas
    recognize_plate_from_webcam = None

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Necesario para `flash` messages

# --- Configuración ---
DB_NAME = "parking_system.db"
PARKING_CAPACITY = 10  # Ajusta la capacidad según necesites
CSV_EXPORT_FILENAME = "parking_history.csv"

# --- Instancia del ParkingManager ---
# Se crea una única instancia para toda la aplicación
parking_manager = ParkingManager(db_name=DB_NAME, capacity=PARKING_CAPACITY)

# Directorio donde se guardan las facturas (relativo a la ubicación de app.py)
INVOICES_DIR = os.path.join(app.root_path, parking_manager.invoices_dir)

def get_vehicle_types_for_template():
    """Prepara los tipos de vehículo para usarlos en las plantillas."""
    return [{"name": vt.name, "value": vt.value, "rate": vt.hourly_rate} for vt in VehicleType]

@app.route('/')
def index():
    """Página principal que muestra el menú."""
    return render_template('index.html', capacity=parking_manager.capacity,
                           current_occupancy=parking_manager.get_current_occupancy())

@app.route('/check_in', methods=['GET', 'POST'])
def check_in():
    """Registra la entrada de un vehículo manualmente."""
    if request.method == 'POST':
        plate = request.form.get('plate', '').strip().upper()
        vehicle_type_value = request.form.get('vehicle_type')

        if not plate:
            flash("Error: La matrícula no puede estar vacía.", "error")
            return redirect(url_for('check_in'))

        if not vehicle_type_value: # Comprobar si se seleccionó un tipo de vehículo
            flash("Error: Debe seleccionar un tipo de vehículo.", "error")
            return redirect(url_for('check_in'))

        if not parking_manager.check_capacity():
            flash("Error: El parking está lleno.", "error")
            return redirect(url_for('index'))

        try:
            # Dado que los valores en VehicleType (COCHE=1.5, MOTO=1.0, etc.) son flotantes
            # y estos son los valores que se envían desde el formulario HTML,
            # debemos convertir el vehicle_type_value (que es un string) a float.
            vehicle_type_as_float = float(vehicle_type_value)
            vehicle_type = VehicleType(vehicle_type_as_float) # Busca el miembro de Enum usando su valor float
            message = parking_manager.check_in_vehicle(plate, vehicle_type)
            flash(message, "success" if "registrada" in message else "error")
        except ValueError:
            flash("Error: Tipo de vehículo no válido.", "error")
        except Exception as e:
            flash(f"Error inesperado: {e}", "error")
        return redirect(url_for('index'))

    return render_template('check_in.html', vehicle_types=get_vehicle_types_for_template())

@app.route('/check_in_webcam', methods=['GET'])
def check_in_webcam():
    """Registra la entrada de un vehículo usando reconocimiento de matrícula."""
    if recognize_plate_from_webcam is None:
        flash("Error: La funcionalidad de reconocimiento de matrículas no ha funcionado correctamente.")
        return redirect(url_for('index'))

    if not parking_manager.check_capacity():
        flash("Error: El parking está lleno.", "error")
        return redirect(url_for('index'))

    # Nota: recognize_plate_from_webcam() tal como está en tu main.py
    # intentará acceder a la webcam del servidor. Para una aplicación web real,
    # necesitarías una solución del lado del cliente (JavaScript) para capturar
    # la imagen y enviarla al servidor.
    # Por ahora, mantenemos la lógica original, asumiendo que esto podría
    # ejecutarse en un entorno donde el servidor tiene acceso a una webcam.
    plate = recognize_plate_from_webcam()

    if not plate:
        flash("No se pudo reconocer la matrícula o la operación fue cancelada.", "info")
        return redirect(url_for('index'))

    # Si se reconoce la matrícula, redirigimos al formulario de check-in manual
    # pre-rellenando la matrícula.
    flash(f"Matrícula reconocida: {plate}. Por favor, selecciona el tipo de vehículo.", "info")
    return render_template('check_in.html', vehicle_types=get_vehicle_types_for_template(), recognized_plate=plate)


@app.route('/check_out', methods=['GET', 'POST'])
def check_out():
    """Registra la salida de un vehículo."""
    if request.method == 'POST':
        plate = request.form.get('plate', '').strip().upper()
        # Obtener la página de origen para la redirección, por defecto 'index'
        source_page_route = request.form.get('source_page_route', 'index')
        
        if not plate:
            flash("Error: La matrícula no puede estar vacía.", "error")
            try:
                redirect_url = url_for(source_page_route)
            except: # BuildError (si source_page_route no es una ruta válida)
                redirect_url = url_for('check_out') # Default a la propia página de checkout
            return redirect(redirect_url)

        message, fee, generated_invoice_filename = parking_manager.check_out_vehicle(plate)        
        category = "success" if "Salida registrada" in message else "error"
        
        if generated_invoice_filename and category == "success":
            # Si la factura se generó con éxito, servirla directamente para descarga.
            # Un mensaje flash aquí no sería visible ya que la respuesta es un archivo.
            # Puedes registrar el mensaje si es necesario.
            app.logger.info(f"Salida registrada para {plate}. Factura {generated_invoice_filename} generada. Mensaje: {message}")
            return send_from_directory(INVOICES_DIR, 
                                       generated_invoice_filename, 
                                       as_attachment=True, 
                                       download_name=generated_invoice_filename)
        else:
            # Si hubo un error o la factura no se generó, mostrar mensaje flash y redirigir.
            # Flashear el mensaje original. Los \n se tratarán como espacios en HTML por defecto.
            flash(message, category)
            
            try:
                redirect_url = url_for(source_page_route)
            except:
                redirect_url = url_for('index') # Default a index si la ruta de origen es inválida
            return redirect(redirect_url)

    return render_template('check_out.html')

@app.route('/current_vehicles')
def current_vehicles_route():
    """Muestra los vehículos actualmente en el parking."""
    vehicles = parking_manager.get_current_vehicles_data() # Necesitamos un método que devuelva los datos
    return render_template('current_vehicles.html', vehicles=vehicles)

@app.route('/history')
def history_route():
    """Muestra el historial de vehículos."""
    history = parking_manager.get_vehicle_history_data() # Necesitamos un método que devuelva los datos
    return render_template('vehicle_history.html', history=history)

@app.route('/export_csv')
def export_csv():
    """Exporta el historial a un archivo CSV."""
    # Construir la ruta completa y absoluta al archivo CSV.
    # app.root_path es el directorio donde se encuentra app.py.
    full_filepath = os.path.join(app.root_path, CSV_EXPORT_FILENAME)

    try:
        # parking_manager.export_history_to_csv recibe la ruta completa
        # y debería devolver esta misma ruta si la operación fue exitosa, o None en caso contrario.
        returned_path = parking_manager.export_history_to_csv(filename=full_filepath)

        if returned_path is None:
            # Esto significa que export_history_to_csv decidió no crear el archivo
            # (p.ej., no hay datos, o un IOError interno que manejó devolviendo None).
            flash("No hay datos para exportar o error al escribir el archivo CSV.", "error")
        elif os.path.exists(returned_path): # returned_path debería ser full_filepath
            # send_file funciona mejor con rutas absolutas.
            @after_this_request
            def remove_file(response):
                try:
                    os.remove(returned_path)
                except Exception as error:
                    app.logger.error(f"Error eliminando el archivo CSV temporal: {error}")
                return response
            return send_file(returned_path, as_attachment=True, download_name=CSV_EXPORT_FILENAME, conditional=True)
        else:
            flash("Error: El archivo CSV fue generado pero no se encontró.", "error")
    except Exception as e:
        flash(f"Error inesperado al exportar CSV: {str(e)}", "error")
    return redirect(url_for('index'))

@app.route('/invoices/<filename>')
def serve_invoice(filename):
    """Sirve un archivo de factura PDF desde el directorio de facturas, forzando la descarga."""
    return send_from_directory(INVOICES_DIR, 
                               filename, 
                               as_attachment=True, 
                               download_name=filename)

# Es buena práctica cerrar la base de datos cuando la aplicación se detiene
@app.teardown_appcontext
def close_connection(exception):
    # parking_manager.close_db() # Descomentar si ParkingManager tiene un método close_db
    pass

if __name__ == '__main__':
    # Crea la base de datos y tablas si no existen al iniciar
    parking_manager._create_tables()
    app.run(debug=True)
