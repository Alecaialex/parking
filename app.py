from flask import Flask, render_template, request, redirect, url_for, flash, send_file, send_from_directory
from markupsafe import Markup
from dotenv import load_dotenv
import os
from plate_recognizer import recognize_plate_from_webcam_api
from parking_manager import ParkingManager
from vehicle import VehicleType

# Cargar las variables de entorno
load_dotenv()

# Inicializar la aplicación Flask
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

# Configuraciones
DB_NAME = "parking_system.db"
PARKING_CAPACITY = 10 
CSV_EXPORT_FILENAME = "parking_history.csv"

# Inicializar instancia de ParkingManager
parking_manager = ParkingManager(db_name=DB_NAME, capacity=PARKING_CAPACITY)

# Directorio donde se guardan las facturas
INVOICES_DIR = os.path.join(app.root_path, parking_manager.invoices_dir)

def get_vehicle_types_for_template():
    """Obtiene todos los tipos de vehículos para el formulario"""
    return [{"name": vt.name, "value": vt.value, "rate": vt.hourly_rate} for vt in VehicleType]

@app.route('/')
def index():
    """Página principal: Estado del parking. Devuelve la plantilla con la capacidad y ocupación actual."""
    return render_template('index.html', capacity=parking_manager.capacity,
                           current_occupancy=parking_manager.get_current_occupancy())

@app.route('/check_in', methods=['GET', 'POST'])
def check_in():
    """Página para registrar un vehículo manualmente. Devuelve la plantilla con el formulario de check-in y los tipos de vehículos disponibles."""
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
            vehicle_type = VehicleType(float(vehicle_type_value))
            message = parking_manager.check_in_vehicle(plate, vehicle_type)
            flash(message, "success" if "registrado" in message else "error")
        except ValueError:
            flash("Error: Tipo de vehículo no válido.", "error")
        except Exception as e:
            flash(f"Error: {e}", "error")
        return redirect(url_for('index'))

    return render_template('check_in.html', vehicle_types=get_vehicle_types_for_template())

@app.route('/check_in_webcam', methods=['GET'])
def check_in_webcam():
    """Página para registrar un vehículo mediante cámara. Devuelve la plantilla con el formulario de check-in (matricula pre-rellenada) y los tipos de vehículos disponibles."""
    if not parking_manager.check_capacity():
        flash("Error: El parking está lleno.", "error")
        return redirect(url_for('index'))

    plate = recognize_plate_from_webcam_api()

    if not plate:
        flash("No se pudo reconocer la matrícula o la operación fue cancelada.", "info")
        return redirect(url_for('index'))

    flash(f"Matrícula reconocida: {plate}. Por favor, selecciona el tipo de vehículo.", "info")
    return render_template('check_in.html', vehicle_types=get_vehicle_types_for_template(), recognized_plate=plate)


@app.route('/check_out', methods=['GET', 'POST'])
def check_out():
    """Página para registrar la salida de un vehículo. Devuelve la plantilla con el formulario de check-out."""
    if request.method == 'POST':
        plate = request.form.get('plate', '').strip().upper()

        if not plate:
            flash("Error: La matrícula no puede estar vacía.", "error")
            return redirect(url_for('index'))

        message, generated_invoice_filename = parking_manager.check_out_vehicle(plate)
        is_success = "Salida registrada" in message

        if is_success:
            success_message_to_flash = message

            flash(success_message_to_flash, "success")

            if generated_invoice_filename:
                invoice_url = url_for('serve_invoice', filename=generated_invoice_filename)
                flash(Markup(f'Factura generada: <a href="{invoice_url}" target="_blank" class="alert-link">{generated_invoice_filename}</a>.'), "info")
        else:
            flash(message, "error")

        return redirect(url_for('index'))

    # Para el GET
    return render_template('check_out.html')

@app.route('/check_out_webcam', methods=['GET'])
def check_out_webcam():
    """Página para registrar la salida de un vehículo mediante cámara. Devuelve la plantilla con el formulario de check-out (matricula pre-rellenada)."""
    plate = recognize_plate_from_webcam_api()

    if not plate:
        flash("No se pudo reconocer la matrícula o la operación fue cancelada.", "info")
        return redirect(url_for('index'))

    flash(f"Matrícula reconocida: {plate}. Por favor, confirme la salida.", "info")
    return render_template('check_out.html', recognized_plate=plate)

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
            return send_file(returned_path, as_attachment=True, download_name=CSV_EXPORT_FILENAME)
        else:
            flash("Error: El archivo CSV fue generado pero no se encontró.", "error")
    except Exception as e:
        flash(f"Error inesperado al exportar CSV: {str(e)}", "error")
    return redirect(url_for('index'))

@app.route('/invoices/<filename>')
def serve_invoice(filename):
    """Envía un archivo de factura PDF desde el directorio de facturas, forzando la descarga."""
    return send_from_directory(INVOICES_DIR, 
                               filename, 
                               as_attachment=True, 
                               download_name=filename)

if __name__ == '__main__':
    parking_manager._create_tables()
    app.run(debug=True)
