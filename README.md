# Sistema de Gestión de Parking

## 1. Descripción General del Proyecto

Este proyecto es un Sistema de Gestión de Parking desarrollado en Python utilizando Flask para la interfaz web. Permite administrar las entradas y salidas de vehículos por diferentes métodos, calcular las tarifas de estacionamiento, generar facturas en PDF, y visualizar el estado actual del parking y el historial de vehículos, además de exportarlo.

**Características Principales:**

*   Registro de entrada y salida de vehículos (manual y por webcam)
*   Cálculo de tarifas basado en el tipo de vehículo y la duración de la estancia.
*   Generación de facturas en PDF al registrar la salida.
*   Visualización de vehículos actualmente en el parking.
*   Historial de todos los vehículos que han utilizado el parking..
*   Exportación del historial de vehículos a CSV.
*   Interfaz web.
*   Almacenamiento de datos en SQLite.

## 2. Cómo Ejecutar el Proyecto

Sigue estos pasos para configurar y ejecutar el proyecto localmente:

1.  **Clonar el repositorio** (si aún no lo has hecho):
    ```bash
    git clone https://github.com/Alecaialex/parking.git
    cd parking
    ```

2.  **Crear un entorno virtual**:
    ```bash
    python -m venv env
    ```

3.  **Activar el entorno virtual**:
    *   En Windows:
        ```bash
        .\env\Scripts\activate
        ```
    *   En macOS/Linux:
        ```bash
        source env/bin/activate
        ```

4.  **Instalar las dependencias**:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configurar variables de entorno**:
    Crea un archivo `.env` en la raíz del proyecto con las claves necesarias (consulta la sección 2.7 para más detalles).
    ```dotenv
    PLATE_RECOGNIZER_API_KEY="tu_clave_aqui"
    FLASK_SECRET_KEY="una_clave_secreta_aleatoria"
    ```

6.  **Ejecutar la aplicación Flask**:
    ```bash
    flask run
    ```
    La aplicación estará disponible en `http://127.0.0.1:5000/`.

## 3. Estructura del Proyecto y Descripción de Archivos

Este proyecto es un Sistema de Gestión de Parking desarrollado en Python utilizando Flask para la interfaz web. Permite administrar las entradas y salidas de vehículos por diferentes métodos, calcular las tarifas de estacionamiento, generar facturas en PDF, y visualizar el estado actual del parking y el historial de vehículos, además de exportarlo.

**Características Principales:**

*   Registro de entrada y salida de vehículos (manual y por webcam)
*   Cálculo de tarifas basado en el tipo de vehículo y la duración de la estancia.
*   Generación de facturas en PDF al registrar la salida.
*   Visualización de vehículos actualmente en el parking.
*   Historial de todos los vehículos que han utilizado el parking..
*   Exportación del historial de vehículos a CSV.
*   Interfaz web.
*   Almacenamiento de datos en SQLite.

## 4. Estructura del Proyecto y Descripción de Archivos

A continuación se explica la función de cada archivo principal dentro del proyecto:

### 4.1. `app.py`

Es el archivo principal para la aplicación Flask. Define las rutas, maneja las solicitudes HTTP, interactúa con `ParkingManager` para la lógica del sistema, y renderiza las plantillas HTML para la UI web.

**Funciones Principales:**

*   **`get_vehicle_types_for_template()`**:
    *   **Función**: Prepara una lista de diccionarios con la información de los tipos de vehículos (nombre, valor, tarifa) para ser utilizada en las plantillas HTML, específicamente en los formularios de entrada.
    *   **Return**: `list` de `dict`

*   **`index()`**:
    *   **Ruta**: `/`
    *   **Métodos**: `GET`
    *   **Función**: Muestra la página principal del sistema. Presenta información como la capacidad total del parking y la ocupación actual.
    *   **Renderiza**: `templates/index.html`

*   **`check_in()`**:
    *   **Ruta**: `/check_in`
    *   **Métodos**: `GET`, `POST`
    *   **Función**:
        *   `GET`: Muestra el formulario para registrar manualmente la entrada de un vehículo.
        *   `POST`: Procesa los datos del formulario (matrícula, tipo de vehículo), valida los datos, verifica la capacidad del parking y, si todo es correcto, registra la entrada del vehículo utilizando `ParkingManager`.
    *   **Renderiza (GET)**: `templates/check_in.html`

*   **`check_in_webcam()`**:
    *   **Ruta**: `/check_in_webcam`
    *   **Métodos**: `GET`
    *   **Función**: Inicia el proceso de reconocimiento de matrícula mediante la webcam para registrar una entrada. Si la funcionalidad de webcam no está disponible o el parking está lleno, muestra un error. Si se reconoce una matrícula, redirige al formulario de `check_in` (`templates/check_in.html`) con la matrícula pre-rellenada para que el usuario seleccione el tipo de vehículo y confirme.
    *   **Renderiza (si hay matrícula)**: `templates/check_in.html`

*   **`check_out()`**:
    *   **Ruta**: `/check_out`
    *   **Métodos**: `GET`, `POST`
    *   **Función**:
        *   `GET`: Muestra el formulario para registrar manualmente la salida de un vehículo.
        *   `POST`: Procesa la matrícula del vehículo a retirar. Utiliza `ParkingManager` para registrar la salida, calcular el coste y generar la factura. Muestra mensajes flash con el resultado, incluyendo un enlace a la factura si se generó correctamente. Redirige a la página de origen (ej. `index` o `current_vehicles`).
    *   **Renderiza (GET)**: `templates/check_out.html`

*   **`check_out_webcam()`**:
    *   **Ruta**: `/check_out_webcam`
    *   **Métodos**: `GET`
    *   **Función**: Similar a `check_in_webcam`, pero para registrar la salida. Si se reconoce una matrícula, redirige al formulario de `check_out` (`templates/check_out.html`) con la matrícula pre-rellenada para que el usuario confirme la salida.
    *   **Renderiza (si hay matrícula)**: `templates/check_out.html`

*   **`current_vehicles_route()`**:
    *   **Ruta**: `/current_vehicles`
    *   **Métodos**: `GET`
    *   **Función**: Muestra una lista de todos los vehículos que se encuentran actualmente estacionados en el parking. Obtiene los datos de `ParkingManager`.
    *   **Renderiza**: `templates/current_vehicles.html`

*   **`history_route()`**:
    *   **Ruta**: `/history`
    *   **Métodos**: `GET`
    *   **Función**: Muestra el historial de todos los vehículos que han pasado por el parking, incluyendo detalles como matrícula, tipo, horas de entrada/salida y coste. Obtiene los datos de `ParkingManager`.
    *   **Renderiza**: `templates/vehicle_history.html`

*   **`export_csv()`**:
    *   **Ruta**: `/export_csv`
    *   **Métodos**: `GET`
    *   **Función**: Permite al usuario descargar el historial de vehículos en un archivo CSV. Utiliza `ParkingManager` para generar el archivo y luego lo envía al navegador del usuario.

*   **`serve_invoice(filename)`**:
    *   **Ruta**: `/invoices/<filename>`
    *   **Métodos**: `GET`
    *   **Función**: Sirve los archivos PDF de las facturas generadas. Permite a los usuarios descargar o visualizar las facturas a través de un enlace.
    *   **Acción**: Descarga de archivo PDF


### 4.2. `parking_manager.py`

Este archivo contiene la clase `ParkingManager`, que encapsula toda la lógica de negocio y las interacciones con la base de datos SQLite. Es el núcleo del sistema de gestión del parking.

**Clase `ParkingManager`:**

*   **`__init__(self, db_name, capacity)`**:
    *   **Función**: Constructor de la clase. Inicializa la conexión a la base de datos, crea las tablas si no existen, establece la capacidad del parking, y configura detalles como el nombre del parking, dirección, NIF y el directorio para guardar las facturas.
    *   **Parámetros**:
        *   `db_name (str)`: Nombre del archivo de la base de datos SQLite.
        *   `capacity (int)`: Capacidad máxima del parking.

*   **`_create_tables(self)`**:
    *   **Función**: Método privado que crea las tablas `parked_vehicles` (para vehículos actualmente estacionados) y `vehicle_history` (para el historial de vehículos) en la base de datos si aún no existen.

*   **`_vehicle_from_row(self, row: tuple, is_history: bool = False) -> Optional[Vehicle]`**:
    *   **Función**: Método privado auxiliar para convertir una fila de resultados de la base de datos en un objeto `Vehicle`. Maneja la diferencia entre registros de vehículos actuales e históricos.
    *   **Parámetros**:
        *   `row (tuple)`: Fila de datos de la base de datos.
        *   `is_history (bool)`: Indica si la fila proviene de la tabla de historial.
    *   **Return**: Un objeto `Vehicle` o `None` si hay un error.

*   **`check_capacity(self) -> bool`**:
    *   **Función**: Verifica si hay espacio disponible en el parking.
    *   **Return**: `True` si hay capacidad, `False` si está lleno.

*   **`check_in_vehicle(self, plate: str, vehicle_type: VehicleType) -> str`**:
    *   **Función**: Registra la entrada de un vehículo en el parking. Verifica si el vehículo ya está dentro y si hay capacidad. Inserta el registro en la tabla `parked_vehicles`.
    *   **Parámetros**:
        *   `plate (str)`: Matrícula del vehículo.
        *   `vehicle_type (VehicleType)`: Tipo de vehículo.
    *   **Return**: Un mensaje de cadena indicando el resultado de la operación (éxito o error).

*   **`_generate_invoice_pdf(self, filepath: str, vehicle: Vehicle, fee: float, check_in_dt: datetime, check_out_dt: datetime, duration_minutes: int) -> bool`**:
    *   **Función**: Método privado que genera una factura en formato PDF utilizando la librería FPDF. Incluye detalles del parking, del cliente, del vehículo, fechas, duración y el importe total.
    *   **Parámetros**: Información detallada del servicio para incluir en la factura.
    *   **Return**: `True` si el PDF se generó correctamente, `False` en caso contrario.

*   **`check_out_vehicle(self, plate: str) -> Tuple[str, Optional[float], Optional[str]]`**:
    *   **Función**: Registra la salida de un vehículo. Busca el vehículo en `parked_vehicles`, calcula la duración de la estancia y la tarifa, lo elimina, lo añade a `vehicle_history`, y genera una factura PDF.
    *   **Parámetros**:
        *   `plate (str)`: Matrícula del vehículo a retirar.
    *   **Return**: Una tupla con:
        *   `str`: Mensaje de resultado.
        *   `Optional[float]`: Tarifa calculada (o `None` si hay error).
        *   `Optional[str]`: Nombre del archivo de la factura generada (o `None`).

*   **`get_current_vehicles(self)`**:
    *   **Función**: (CLI) Imprime en la consola una lista de los vehículos actualmente en el parking.

*   **`get_vehicle_history(self)`**:
    *   **Función**: (CLI) Imprime en la consola el historial de vehículos que han salido del parking.

*   **`export_history_to_csv(self, filename: str = "historial.csv") -> Optional[str]`**:
    *   **Función**: Exporta el historial de vehículos de la tabla `vehicle_history` a un archivo CSV.
    *   **Parámetros**:
        *   `filename (str)`: Nombre del archivo CSV a generar.
    *   **Return**: La ruta al archivo CSV si la exportación fue exitosa, `None` en caso contrario.

*   **`close_db(self)`**:
    *   **Función**: Cierra la conexión a la base de datos.

*   **`get_current_occupancy(self) -> int`**:
    *   **Función**: Devuelve el número actual de vehículos en el parking.
    *   **Return**: `int` con la cantidad de vehículos.

*   **`get_current_vehicles_data(self) -> list[dict]`**:
    *   **Función**: Obtiene y formatea los datos de los vehículos actualmente en el parking para ser utilizados por la aplicación Flask (específicamente, para las plantillas).
    *   **Return**: `list` de `dict`, donde cada diccionario representa un vehículo.

*   **`get_vehicle_history_data(self) -> list[dict]`**:
    *   **Función**: Obtiene y formatea los datos del historial de vehículos para ser utilizados por la aplicación Flask.
    *   **Return**: `list` de `dict`, donde cada diccionario representa un registro del historial.

### 4.3. `vehicle.py`

Define las estructuras de datos para los vehículos y sus tipos.

**Enum `VehicleType(Enum)`:**

*   **Función**: Define los diferentes tipos de vehículos permitidos (COCHE, MOTO, FURGONETA) y asocia a cada uno su tarifa por hora.
*   **Atributos**: `COCHE`, `MOTO`, `FURGONETA` (con sus valores de tarifa).
*   **Propiedad `hourly_rate(self) -> float`**: Devuelve la tarifa por hora del tipo de vehículo.

**Clase `Vehicle`:**

*   **Función**: Representa un vehículo individual con sus atributos y métodos para calcular la duración y el coste del estacionamiento.
*   **Atributos**:
    *   `plate (str)`: Matrícula del vehículo.
    *   `type (VehicleType)`: Tipo de vehículo (instancia de `VehicleType`).
    *   `check_in_time (int)`: Marca de tiempo (milisegundos desde la época) de la entrada.
    *   `check_out_time (Optional[int])`: Marca de tiempo de la salida (opcional).
*   **Métodos**:
    *   **`__init__(self, plate: str, vehicle_type: VehicleType, check_in_time: int, check_out_time: Optional[int] = None)`**: Constructor.
    *   **`calculate_parking_duration_in_minutes(self) -> int`**: Calcula la duración de la estancia en minutos. Si `check_out_time` no está definido, usa la hora actual.
    *   **`calculate_parking_fee(self) -> float`**: Calcula la tarifa total de estacionamiento basándose en la duración y la tarifa horaria del tipo de vehículo.

### 4.4. `plate_recognizer.py`

Maneja la funcionalidad de reconocimiento de matrículas utilizando la webcam y la API "Plate Recognizer".

**Función `recognize_plate_from_webcam_api() -> Optional[str]`:**

*   **Función**: Activa la cámara web, permite al usuario capturar una imagen y la envía a la API de Plate Recognizer para su procesamiento.
*   **Interacción**: Muestra una ventana de la webcam. El usuario pulsa 'espacio' para capturar o 'q' para cancelar.
*   **Configuración**: Requiere una `PLATE_RECOGNIZER_API_KEY` configurada en las variables de entorno (`.env`).
*   **Return**: La matrícula reconocida como una cadena de texto, o `None` si no se reconoce, se cancela, o hay un error.

### 4.5. `main.py`

Proporciona una interfaz de línea de comandos (CLI) para interactuar con el sistema de parking. Versión anterior a la interfaz web con Flask.

**Funciones Principales:**

*   **`ask_vehicle_type() -> Optional[VehicleType]`**:
    *   **Función**: Muestra al usuario las opciones de tipo de vehículo en la consola y solicita una selección.
    *   **Return**: Un objeto `VehicleType` correspondiente a la selección, o `None` si la entrada es inválida.

*   **`main()`**:
    *   **Función**: Bucle principal. Muestra un menú con opciones (registrar entrada/salida, ver vehículos, ver historial, exportar CSV, registrar entrada con webcam, salir).
    *   **Interacción**: Lee la entrada del usuario y llama a los métodos correspondientes de `ParkingManager`.

### 4.6. Plantillas HTML (`templates/`)

Estos archivos definen la estructura y presentación de las páginas web de la aplicación. Utilizan el motor de plantillas Jinja2.

*   **`base.html`**: Plantilla base que define la estructura común (navegación, encabezado, pie de página, mensajes flash) heredada por las demás plantillas.
*   **`check_in.html`**: Formulario para registrar la entrada de un vehículo. Permite ingresar la matrícula y seleccionar el tipo de vehículo.
*   **`check_out.html`**: Formulario para registrar la salida de un vehículo. Permite ingresar la matrícula.
*   **`current_vehicles.html`**: Muestra una tabla con los vehículos actualmente en el parking, con opción de registrar su salida directamente desde la tabla.
*   **`index.html`**: Página de inicio, muestra la capacidad y ocupación del parking.
*   **`vehicle_history.html`**: Muestra una tabla con el historial de vehículos que han utilizado el parking.

### 4.7. `.env`

Archivo de configuración para variables de entorno.

**Contenido:**

*   **`PLATE_RECOGNIZER_API_KEY`**: Clave necesaria para usar la API de Plate Recognizer.
*   **`FLASK_SECRET_KEY`**: Clave secreta utilizada por Flask para firmar sesiones y otros fines de seguridad.

### 4.8. `requirements.txt`

Lista las dependencias de Python del proyecto, necesarias para su ejecución.

**Contenido:** Flask requests opencv-python fpdf python-dotenv

Permite instalar todas las dependencias fácilmente con `pip install -r requirements.txt`.

### 4.9. `static/style.css`

Archivo CSS de la aplicación web.

### 4.10. `test_vehicle.py`

Contiene pruebas unitarias para la clase `Vehicle` definida en `vehicle.py`.

**Clase `TestVehicle(unittest.TestCase)`:**

*   **Función**: Verificar el correcto funcionamiento de los métodos de la clase `Vehicle`, especialmente `calculate_parking_duration_in_minutes()` y `calculate_parking_fee()`.
*   **Métodos de Prueba**:
    *   `setUp()`: Configura datos comunes para las pruebas (tiempos de referencia).
    *   `test_calculate_parking_duration_in_minutes()`: Prueba el cálculo de duración normal.
    *   `test_calculate_parking_duration_zero_minutes()`: Prueba duración cero.
    *   `test_calculate_parking_duration_negative_scenario()`: Prueba el caso donde la salida es antes que la entrada (debería dar 0).
    *   `test_calculate_parking_fee_coche()`, `test_calculate_parking_fee_moto()`, `test_calculate_parking_fee_furgoneta()`: Prueban el cálculo de tarifa para cada tipo de vehículo.
    *   `test_calculate_parking_fee_partial_hour()`: Prueba con fracciones de hora.
    *   `test_calculate_parking_fee_zero_duration()`: Prueba tarifa con duración cero.
    *   `test_calculate_parking_fee_negative_duration_scenario()`: Prueba tarifa con duración negativa (debería ser 0).

### 4.11. `test_parking_manager.py`

Contiene pruebas unitarias para la clase `ParkingManager` definida en `parking_manager.py`. Utiliza `unittest.mock` para simular dependencias como `time.time()`, `os.makedirs`, `FPDF`, y la base de datos (usando `:memory:`).

**Clase `TestParkingManager(unittest.TestCase)`:**

*   **Función**: Verificar el correcto funcionamiento de los métodos de `ParkingManager`, incluyendo la gestión de capacidad, registro de entradas y salidas, generación de facturas, manejo de la base de datos, y exportación de datos.
*   **Métodos de Prueba Principales**:
    *   `setUp()`: Configura el entorno para cada prueba, incluyendo mocks y una base de datos en memoria.
    *   `tearDown()`: Limpia después de cada prueba, deteniendo mocks y cerrando la base de datos.
    *   Pruebas para `check_capacity()`, `check_in_vehicle()` (éxito, vehículo ya aparcado).
    *   Pruebas para `check_out_vehicle()` (éxito, vehículo no encontrado, tipo desconocido en BD, fallo en generación de PDF).
    *   Pruebas para `_generate_invoice_pdf()` (éxito, fallo por excepción).
    *   Pruebas para `get_current_vehicles()` y `get_current_vehicles_data()` (vacío, con datos).
    *   Pruebas para `get_vehicle_history()` y `get_vehicle_history_data()` (vacío, con datos).
    *   Pruebas para `export_history_to_csv()` (éxito, sin datos, error de E/S).
    *   Pruebas para `_vehicle_from_row()` (aparcado, historial, tipo desconocido).
    *   Pruebas para `get_current_occupancy()` y `close_db()`.

### 4.12. `test_main.py`

Contiene pruebas unitarias para las funciones del script `main.py` (la interfaz de línea de comandos). Utiliza `unittest.mock` para simular `input()`, `print()`, `ParkingManager`, y `recognize_plate_from_webcam`.

**Clase `TestMainCLI(unittest.TestCase)`:**

*   **Función**: Verificar el comportamiento de la CLI, incluyendo la selección de opciones del menú, la entrada de datos del usuario y la interacción con `ParkingManager` y el reconocimiento de matrículas.
*   **Métodos de Prueba Principales**:
    *   Pruebas para `ask_vehicle_type()` (selección válida, inválida).
    *   Pruebas para el flujo principal `main()` simulando diferentes interacciones del usuario:
        *   Registro de entrada (éxito, parking lleno, matrícula vacía, tipo inválido).
        *   Registro de salida.
        *   Visualización de vehículos actuales e historial.
        *   Exportación a CSV.
        *   Registro de entrada con webcam (éxito, fallo en reconocimiento).
        *   Salida del programa y opción de menú inválida.

## 5. Flujo del Programa

### 5.1. Ver Página de Inicio

1.  Usuario accede a la URL raíz (`/`).
2.  **`app.py`**: La ruta `/` llama a la función `index()`.
3.  **`index()`**: Llama a `parking_manager.capacity` y `parking_manager.get_current_occupancy()` para obtener el estado actual.
4.  **`index()`**: Renderiza `templates/index.html`, pasando los datos de capacidad y ocupación.

### 5.2. Registrar Entrada de Vehículo (Manual)

1.  Usuario navega a "Registrar Entrada" (`/check_in`).
2.  **`app.py`**: La ruta `/check_in` (método GET) llama a `check_in()`.
3.  **`check_in()`**: Llama a `get_vehicle_types_for_template()` para obtener los tipos de vehículos.
4.  **`check_in()`**: Renderiza `templates/check_in.html` con el formulario y los tipos de vehículo.
5.  Usuario rellena matrícula, selecciona tipo y envía el formulario (método POST a `/check_in`).
6.  **`app.py`**: La ruta `/check_in` (método POST) llama a `check_in()`.
7.  **`check_in()`**:
    *   Recupera `plate` y `vehicle_type` del formulario.
    *   Valida que no estén vacíos.
    *   Llama a `parking_manager.check_capacity()`. Si está lleno, muestra error y redirige.
    *   Convierte `vehicle_type_value` a `VehicleType`.
    *   Llama a `parking_manager.check_in_vehicle(plate, vehicle_type)`.
    *   `ParkingManager`: Verifica si la matrícula ya existe, y si no, inserta el nuevo vehículo en `parked_vehicles`. Devuelve un mensaje.
    *   Establece un mensaje flash (éxito/error).
    *   Redirige al usuario a la página de inicio (`/`).

### 5.3. Registrar Entrada de Vehículo (Webcam)

1.  Usuario navega a "Entrada (Webcam)" (`/check_in_webcam`).
2.  **`app.py`**: La ruta `/check_in_webcam` (método GET) llama a `check_in_webcam()`.
3.  **`check_in_webcam()`**:
    *   Llama a `parking_manager.check_capacity()`. Si está lleno, muestra error y redirige.
    *   Llama a `plate_recognizer.recognize_plate_from_webcam_api()`.
        *   **`plate_recognizer.py`**: Abre la webcam. Usuario presiona 'espacio'. Imagen se envía a API. Se devuelve la matrícula o `None`.
    *   Si se reconoce una matrícula (`plate` no es `None`):
        *   Establece un mensaje flash informativo.
        *   Renderiza `templates/check_in.html` con la `recognized_plate` pre-rellenada y los `vehicle_types`.
    *   Si no se reconoce matrícula o se cancela:
        *   Establece un mensaje flash.
        *   Redirige al usuario a la página de inicio (`/`).
4.  Usuario (si se reconoció matrícula) selecciona el tipo de vehículo en el formulario pre-rellenado y lo envía.
5.  El flujo continúa como en el paso 5 de "Registrar Entrada de Vehículo (Manual)".

### 5.4. Registrar Salida de Vehículo (Manual)

1.  Usuario navega a "Registrar Salida" (`/check_out`).
2.  **`app.py`**: La ruta `/check_out` (método GET) llama a `check_out()`.
3.  **`check_out()`**: Renderiza `templates/check_out.html` con el formulario.
4.  Usuario ingresa la matrícula y envía el formulario (método POST a `/check_out`).
5.  **`app.py`**: La ruta `/check_out` (método POST) llama a `check_out()`.
6.  **`check_out()`**:
    *   Recupera `plate` del formulario.
    *   Valida que no esté vacía.
    *   Llama a `parking_manager.check_out_vehicle(plate)`.
        *   **`ParkingManager`**:
            *   Busca el vehículo en `parked_vehicles`. Si no existe, devuelve error.
            *   Calcula duración y tarifa usando métodos del objeto `Vehicle`.
            *   Elimina el vehículo de `parked_vehicles`.
            *   Inserta el registro en `vehicle_history`.
            *   Llama a `_generate_invoice_pdf()` para crear la factura.
            *   Devuelve mensaje, tarifa y nombre del archivo de la factura.
    *   Establece mensajes flash: uno para el resultado general y otro con el enlace a la factura (usando `Markup`) si se generó.
    *   Redirige al usuario a la página de origen (por defecto, `/`).

### 5.5. Registrar Salida de Vehículo (Webcam)

1.  Usuario navega a "Salida (Webcam)" (`/check_out_webcam`).
2.  **`app.py`**: La ruta `/check_out_webcam` (método GET) llama a `check_out_webcam()`.
3.  **`check_out_webcam()`**:
    *   Llama a `plate_recognizer.recognize_plate_from_webcam_api()`.
    *   Si se reconoce una matrícula:
        *   Establece un mensaje flash informativo.
        *   Renderiza `templates/check_out.html` con la `recognized_plate` pre-rellenada.
    *   Si no se reconoce matrícula o se cancela:
        *   Establece un mensaje flash.
        *   Redirige al usuario a la página de inicio (`/`).
4.  Usuario (si se reconoció matrícula) confirma la salida enviando el formulario pre-rellenado.
5.  El flujo continúa como en el paso 5 de "Registrar Salida de Vehículo (Manual)".

### 5.6. Ver Vehículos Actuales

1.  Usuario navega a "Vehículos Actuales" (`/current_vehicles`).
2.  **`app.py`**: La ruta `/current_vehicles` llama a `current_vehicles_route()`.
3.  **`current_vehicles_route()`**: Llama a `parking_manager.get_current_vehicles_data()` para obtener la lista de vehículos.
4.  **`current_vehicles_route()`**: Renderiza `templates/current_vehicles.html`, pasando la lista de vehículos.
5.  El navegador muestra la tabla. Cada fila tiene un botón "Registrar Salida" que es un formulario POST a `/check_out` con la matrícula del vehículo y `source_page_route`="current_vehicles_route".

### 5.7. Ver Historial de Vehículos

1.  Usuario navega a "Historial" (`/history`).
2.  **`app.py`**: La ruta `/history` llama a `history_route()`.
3.  **`history_route()`**: Llama a `parking_manager.get_vehicle_history_data()` para obtener el historial.
4.  **`history_route()`**: Renderiza `templates/vehicle_history.html`, pasando los datos del historial.

### 5.8. Exportar Historial a CSV

1.  Usuario navega a "Exportar CSV" (`/export_csv`).
2.  **`app.py`**: La ruta `/export_csv` llama a `export_csv()`.
3.  **`export_csv()`**:
    *   Define la ruta completa del archivo CSV.
    *   Llama a `parking_manager.export_history_to_csv(filename=full_filepath)`.
        *   **`ParkingManager`**: Consulta `vehicle_history`, formatea los datos y escribe el archivo CSV. Devuelve la ruta del archivo o `None`.
    *   Si el archivo se generó y existe, usa `send_file()` para enviarlo al navegador para su descarga.
    *   Si hay error o no hay datos, muestra un mensaje flash y redirige a `/`.

### 5.9. Descargar Factura

1.  Después de un `check_out` exitoso, se muestra un mensaje flash con un enlace a la factura (ej. `/invoices/factura_PLATE_FECHA.pdf`).
2.  Usuario hace clic en el enlace.
3.  **`app.py`**: La ruta `/invoices/<filename>` llama a `serve_invoice(filename)`.
4.  **`serve_invoice()`**: Utiliza `send_from_directory()` para buscar el archivo PDF en el directorio `invoices` y enviarlo al navegador, forzando la descarga (`as_attachment=True`).