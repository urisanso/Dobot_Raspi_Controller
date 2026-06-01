# Dobot Raspi Controller

Sistema prototipo de clasificacion automatica de piezas usando un Dobot Magician Lite, una Raspberry Pi, vision artificial y una cinta transportadora controlada por ESP32.

El proyecto integra captura de imagen, deteccion de objetos mediante Roboflow, conversion de coordenadas de camara a coordenadas del robot mediante homografia, control del Dobot desde Raspberry Pi, accionamiento de bomba de vacio y registro automatico de inventario.

> Estado del proyecto: prototipo funcional de punta a punta.

---

## Objetivo

El objetivo del sistema es automatizar la deteccion, toma y clasificacion de piezas ubicadas sobre una cinta transportadora.

El flujo general es:

1. La cinta transportadora mueve las piezas.
2. Un sensor detecta la presencia de una pieza y detiene la cinta.
3. La ESP32 informa a la Raspberry Pi que hay una pieza lista para procesar.
4. La Raspberry Pi captura una imagen con la camara.
5. Se ejecuta inferencia con un modelo entrenado en Roboflow.
6. Se selecciona una deteccion valida.
7. Se transforma la posicion en pixeles a coordenadas reales del Dobot.
8. El Dobot toma la pieza con la bomba de vacio.
9. La pieza se deposita en una posicion asignada segun su clase.
10. Se actualiza un archivo de inventario.

---

## Hardware utilizado

- Raspberry Pi 4B
- Dobot Magician Lite con conexion USB
- Camara del kit Dobot Magician Lite
- ESP32 generico
- Driver A4988 para motor paso a paso
- Motor NEMA 21
- Sensor LDR
- Sensor laser KY-008
- Pulsadores de control
- Cinta transportadora
- Bomba de vacio / succion del Dobot

Los pines utilizados estan definidos directamente en los scripts principales:

- Raspberry Pi: `Scripts/main.py`
- ESP32: `Ctrl_cinta_transportadora/src/main.cpp`

---

## Seguridad

Antes de ejecutar el sistema completo, verificar que el area de trabajo del robot este libre de obstaculos y que no haya manos cerca de la zona de movimiento.

Se recomienda probar primero los movimientos sin piezas, con velocidades moderadas y con la bomba de vacio desactivada hasta validar la calibracion, la homografia y las posiciones de clasificacion.

---

## Estructura del proyecto

```text
Dobot_Raspi_Controller/
|-- Scripts/
|   |-- main.py
|   |-- Capture/
|   |   |-- capture_image.py
|   |   |-- capture_dataset.py
|   |   |-- capture_dataset_enter.py
|   |   |-- dataset_capture_vision_pose.py
|   |   `-- calculo_H.py
|   |-- Dobot/
|   |   |-- control_dobot.py
|   |   |-- control_curses.py
|   |   |-- dobot_jog_joints.py
|   |   |-- dobot_joints_demo.py
|   |   |-- record_trajectory.py
|   |   `-- test_gripper.py
|   `-- Roboflow/
|       |-- inferencia_api.py
|       |-- inferencia_test.py
|       `-- test_model.py
|-- lib/
|   |-- dobot_utils.py
|   |-- roboflow_detector.py
|   |-- utils.py
|   `-- inventario_utils.py
|-- JSON/
|   |-- Matriz_H.json
|   |-- places.json
|   `-- puntos.json
|-- Ctrl_cinta_transportadora/
|   |-- platformio.ini
|   `-- src/main.cpp
|-- capturas/
|-- predicciones/
|-- data/
|-- dataset/
|-- requirements.txt
`-- README.md
```

---

## Componentes principales

### Raspberry Pi

La Raspberry Pi ejecuta el sistema principal en Python. Sus responsabilidades son:

- Controlar el Dobot por USB.
- Leer entradas GPIO.
- Esperar la senal proveniente de la ESP32.
- Capturar imagenes desde la camara.
- Enviar imagenes a Roboflow para deteccion.
- Convertir coordenadas de imagen a coordenadas del robot.
- Ejecutar movimientos de pick and place.
- Actualizar el inventario.

El script principal es:

```bash
python -m Scripts.main
```

### Dobot Magician Lite

El Dobot se controla desde Python usando `pydobot`.

El sistema utiliza movimientos cartesianos y movimientos tipo joint para ubicar el robot en posiciones seguras, ir a la zona de vision, tomar piezas y clasificarlas.

Las funciones principales de control se encuentran en:

```text
lib/dobot_utils.py
```

Entre ellas:

- Deteccion automatica del puerto USB.
- Movimiento cartesiano.
- Movimiento por juntas.
- Control de la bomba de vacio.
- Carga de posiciones desde archivos JSON.

### Modos de movimiento utilizados

El proyecto usa principalmente los siguientes modos de movimiento de `pydobot`:

- `MOVJ_XYZ`: movimiento a coordenadas cartesianas con trayectoria por juntas.
- `MOVJ_ANGLE`: movimiento directo por angulos articulares.
- `move_to`: movimiento cartesiano utilizado en rutinas de pick and place.

### Vision artificial

La deteccion de piezas se realiza mediante un modelo alojado en Roboflow. Para ejecutar el sistema completo se requiere conexion a internet y una API Key valida de Roboflow.

El flujo de vision es:

1. Captura de imagen desde camara.
2. Envio de la imagen a Roboflow Serverless.
3. Recepcion de predicciones.
4. Filtrado por confianza minima.
5. Ignorado de clases no deseadas.
6. Seleccion de la deteccion objetivo.

El modulo encargado de la deteccion es:

```text
lib/roboflow_detector.py
```

Las imagenes capturadas y las predicciones pueden guardarse como archivos de depuracion en:

```text
capturas/
predicciones/
```

### Homografia

Para que el Dobot pueda tomar una pieza detectada por la camara, se transforma la posicion en pixeles `(u, v)` a coordenadas del robot `(x, y)`.

La matriz de homografia se almacena en:

```text
JSON/Matriz_H.json
```

Este archivo incluye:

- Resolucion de camara.
- Pose de vision del Dobot.
- Matriz `H` para transformar coordenadas de imagen a coordenadas del robot.

El calculo y prueba de la homografia se trabaja desde:

```text
Scripts/Capture/calculo_H.py
```

### Posiciones de clasificacion

Las posiciones donde el Dobot deja cada pieza se definen en:

```text
JSON/places.json
```

Cada clase detectada tiene asociada una posicion:

```json
{
  "Polea": {
    "x": 96,
    "y": -220,
    "z": 50,
    "r": 0
  }
}
```

Si una clase no tiene posicion especifica, se utiliza la posicion `default`.

### Cinta transportadora

La cinta transportadora es controlada por una ESP32 programada con PlatformIO y Arduino Framework.

El codigo se encuentra en:

```text
Ctrl_cinta_transportadora/src/main.cpp
```

La ESP32 controla:

- Motor paso a paso mediante driver A4988.
- Lectura del sensor LDR.
- Sensor laser KY-008.
- Pausa y reanudacion mediante pulsador.
- Senal de habilitacion hacia la Raspberry Pi.

La configuracion de PlatformIO esta en:

```text
Ctrl_cinta_transportadora/platformio.ini
```

Dependencia principal:

```ini
lib_deps = waspinator/AccelStepper@^1.64
```

---

## Instalacion del entorno en Raspberry Pi

Se recomienda utilizar Raspberry Pi OS 64 bits. Para verificar la arquitectura:

```bash
uname -m
```

La salida esperada es:

```text
aarch64
```

Clonar el repositorio:

```bash
git clone https://github.com/urisanso/Dobot_Raspi_Controller.git
cd Dobot_Raspi_Controller
```

Actualizar paquetes del sistema e instalar dependencias base:

```bash
sudo apt update
sudo apt install git python3-pip python3-venv libatlas-base-dev
```

Crear y activar entorno virtual:

```bash
python3 -m venv venv
source venv/bin/activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

En caso de trabajar con una instalacion minima, puede usarse:

```bash
pip install -r requirements_new.txt
```

Verificar que `numpy` funcione correctamente:

```bash
python -c "import numpy; print(numpy.__version__)"
```

---

## Permisos para el Dobot

Conectar el Dobot por USB y verificar el puerto:

```bash
ls /dev/tty*
```

Normalmente puede aparecer como:

```text
/dev/ttyACM0
/dev/ttyUSB0
```

Agregar el usuario al grupo `dialout`:

```bash
sudo usermod -aG dialout $USER
```

Luego cerrar sesion y volver a ingresar.

---

## Configuracion de Roboflow

El sistema utiliza una API Key de Roboflow para ejecutar inferencia en la nube mediante Roboflow Serverless. Por este motivo, el sistema principal requiere conexion a internet durante la deteccion.

Actualmente la configuracion se encuentra en el script principal:

```python
API_KEY = "..."
PROJECT = "model_ping_reduced_v2-0"
VERSION = 2
```

Para una version mas segura y mantenible, se recomienda migrar estos valores a variables de entorno o a un archivo `.env`, evitando dejar claves privadas dentro del codigo fuente.

Ejemplo recomendado:

```env
ROBOFLOW_API_KEY=tu_api_key
ROBOFLOW_PROJECT=model_ping_reduced_v2-0
ROBOFLOW_VERSION=2
```

---

## Ejecucion del sistema principal

Desde la raiz del proyecto:

```bash
source venv/bin/activate
python -m Scripts.main
```

Al iniciar, el sistema solicita seleccionar o crear un archivo de inventario.

Luego queda en espera hasta que el operador active el ciclo mediante el pulsador correspondiente.

---

## Inventario

El sistema registra automaticamente las piezas clasificadas.

El modulo de inventario esta en:

```text
lib/inventario_utils.py
```

El inventario cuenta cuantas piezas de cada clase fueron clasificadas durante la ejecucion.

Ejemplo:

```text
ConversorB_2x2: 17
Polea: 21
Esquina_Grande: 20
Viga_2x2: 15
```

---

## Scripts auxiliares

### Captura de dataset

Scripts para capturar imagenes y construir datasets:

```bash
python -m Scripts.Capture.capture_dataset_enter --label NOMBRE_CLASE
```

Tambien existen scripts para captura individual y captura asociada a pose de vision.

### Calibracion de homografia

Script utilizado para calcular o probar la matriz de conversion entre imagen y coordenadas del robot:

```bash
python -m Scripts.Capture.calculo_H
```

### Control manual del Dobot

Scripts de prueba y control manual:

```bash
python -m Scripts.Dobot.dobot_jog_joints
python -m Scripts.Dobot.control_curses
```

### Grabacion de trayectorias

El proyecto incluye un grabador de trayectorias articulares:

```bash
python -m Scripts.Dobot.record_trajectory
```

Permite mover el Dobot manualmente, guardar puntos y reproducir trayectorias.

### Pruebas de Roboflow

Scripts para probar inferencia y conexion con el modelo:

```bash
python -m Scripts.Roboflow.test_model
python -m Scripts.Roboflow.inferencia_test
```

---

## Funcionamiento general del prototipo

```text
ESP32 + cinta
    |
Sensor detecta pieza
    |
Cinta se detiene
    |
Raspberry recibe senal
    |
Dobot se posiciona en pose de vision
    |
Camara captura imagen
    |
Roboflow detecta la pieza
    |
Homografia convierte pixeles a coordenadas del robot
    |
Dobot toma la pieza
    |
Dobot deposita segun clase detectada
    |
Se actualiza inventario
```

---

## Limitaciones actuales

- El sistema funciona como prototipo y depende de una calibracion correcta de camara, iluminacion y posicion de piezas.
- La API Key de Roboflow se encuentra actualmente definida en codigo.
- Las posiciones de clasificacion estan configuradas manualmente en JSON.
- La precision de toma depende de la homografia y de la estabilidad mecanica del montaje.
- El sensor LDR y el laser requieren ajuste fisico para una deteccion confiable.
- El control de errores puede ampliarse para recuperacion automatica ante fallos de camara, red o comunicacion con el Dobot.

---

## Posibles mejoras futuras

- Migrar configuracion sensible a `.env`.
- Agregar documentacion grafica del cableado.
- Incorporar una rutina guiada de calibracion de homografia.
- Registrar logs estructurados de cada ciclo.
- Agregar interfaz de monitoreo local.
- Mejorar el manejo de errores ante perdida de conexion con Roboflow o Dobot.
- Agregar tests para modulos auxiliares.
- Separar configuracion de hardware en archivos externos.

---

## Creditos

Proyecto desarrollado por Uriel Sansoni.

Repositorio oficial:

```text
https://github.com/urisanso/Dobot_Raspi_Controller
```

Prototipo probado con Raspberry Pi 4B, Raspberry Pi OS 64 bits, Dobot Magician Lite, camara del kit Dobot Magician Lite, ESP32 generico, driver A4988, motor NEMA 21, sensor LDR y sensor laser KY-008.
