from flask import Flask, render_template, request, redirect, url_for, flash, send_file, after_this_request, send_from_directory
from plate_recognizer import recognize_plate_from_webcam_api
from parking_manager import ParkingManager
from vehicle import VehicleType
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"  # TODO: Cambiar y cargar desde variable de entorno para producción

# Configuraciones
DB_NAME = "parking_system.db"
PARKING_CAPACITY = 10 
CSV_EXPORT_FILENAME = "parking_history.csv"

# Inicializar instancia de ParkingManager
parking_manager = ParkingManager(db_name=DB_NAME, capacity=PARKING_CAPACITY)

# Directorio donde se guardan las facturas
INVOICES_DIR = os.path.join(app.root_path, parking_manager.invoices_dir) # type: ignore

# Obtiene todos los tipos de vehículos para el formulario
def get_vehicle_types_for_template():
    return [{"name": vt.name, "value": vt.value, "rate": vt.hourly_rate} for vt in VehicleType]

@app.route('/')
# Página principal: Estado del parking
def index():
    return render_template('index.html', capacity=parking_manager.capacity,
                           current_occupancy=parking_manager.get_current_occupancy())

@app.route('/check_in', methods=['GET', 'POST'])
# Página para registrar un vehículo manualmente
def check_in():
    if request.method == 'POST':
        plate = request.form.get('plate', '').strip().upper()
        vehicle_type_value = request.form.get('vehicle_type')

        if not plate:
            flash("Error: La matrícula no puede estar vacía.", "error")
            return redirect(url_for('check_in'))

        if not vehicle_type_value:
            flash("Error: Debe seleccionar un tipo de vehículo.", "error")
            return redirect(url_for('check_in'))

        if not parking_manager.check_capacity():
            flash("Error: El parking está lleno.", "error")
            return redirect(url_for('index'))

        try:
            vehicle_type_as_float = float(vehicle_type_value)
            vehicle_type = VehicleType(vehicle_type_as_float)
            message = parking_manager.check_in_vehicle(plate, vehicle_type)
            flash(message, "success" if "registrada" in message else "error")
        except ValueError:
            flash("Error: Tipo de vehículo no válido.", "error")
        except Exception as e:
            flash(f"Error inesperado: {e}", "error")
        return redirect(url_for('index'))

    return render_template('check_in.html', vehicle_types=get_vehicle_types_for_template())

@app.route('/check_in_webcam', methods=['GET'])
# Página para registrar un vehículo mediante cámara
def check_in_webcam():
    if recognize_plate_from_webcam_api is None:
        flash("Error: La funcionalidad de reconocimiento de matrículas no está disponible o no ha funcionado correctamente.", "error")
        return redirect(url_for('index'))

    if not parking_manager.check_capacity():
        flash("Error: El parking está lleno.", "error")
        return redirect(url_for('index'))

    plate = recognize_plate_from_webcam_api()

    if not plate:
        flash("No se pudo reconocer la matrícula o la operación fue cancelada.", "info")
        return redirect(url_for('index'))

    # Si se reconoce, pre-rellenar formulario de check-in manual.
    flash(f"Matrícula reconocida: {plate}. Por favor, selecciona el tipo de vehículo.", "info")
    return render_template('check_in.html', vehicle_types=get_vehicle_types_for_template(), recognized_plate=plate)


@app.route('/check_out', methods=['GET', 'POST'])
# Página para registrar la salida de un vehículo
def check_out():
    if request.method == 'POST':
        plate = request.form.get('plate', '').strip().upper()
        source_page_route = request.form.get('source_page_route', 'index')
        
        if not plate:
            flash("Error: La matrícula no puede estar vacía.", "error")
            try:
                redirect_url = url_for(source_page_route)
            except:
                redirect_url = url_for('check_out')
            return redirect(redirect_url)

        message, fee, generated_invoice_filename = parking_manager.check_out_vehicle(plate)        
        category = "success" if "Salida registrada" in message else "error"
        
        if generated_invoice_filename and category == "success":
            # Si la factura se generó con éxito, flashear un mensaje con el enlace y redirigir.
            app.logger.info(f"Salida registrada para {plate}. Factura {generated_invoice_filename} generada. Mensaje: {message}")
            
            try:
                redirect_url = url_for(source_page_route)
            except: # werkzeug.routing.exceptions.BuildError
                redirect_url = url_for('index')
            return redirect(redirect_url)
        else:
            flash(message, category)
            
            try:
                redirect_url = url_for(source_page_route)
            except:
                redirect_url = url_for('index')
            return redirect(redirect_url)

    # Para el método GET, mostrar el formulario de check_out
    return render_template('check_out.html')

@app.route('/current_vehicles')
def current_vehicles_route():
    """Muestra los vehículos actualmente en el parking."""
    vehicles = parking_manager.get_current_vehicles_data()
    return render_template('current_vehicles.html', vehicles=vehicles)

@app.route('/history')
def history_route():
    """Muestra el historial de vehículos."""
    history = parking_manager.get_vehicle_history_data()
    return render_template('vehicle_history.html', history=history)

@app.route('/export_csv')
def export_csv():
    """Exporta el historial a un archivo CSV."""
    full_filepath = os.path.join(app.root_path, CSV_EXPORT_FILENAME)

    try:
        returned_path = parking_manager.export_history_to_csv(filename=full_filepath)

        if returned_path is None:
            flash("No hay datos para exportar o error al escribir el archivo CSV.", "error")
        elif os.path.exists(returned_path):
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

@app.teardown_appcontext
def close_connection(exception):
    # parking_manager.close_db() # Considerar si es necesario para SQLite en Flask
    pass

if __name__ == '__main__':
    parking_manager._create_tables()
    app.run(debug=True)
