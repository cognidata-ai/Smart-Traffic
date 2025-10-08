# Smart Traffic - Sistema de Monitoreo de Tráfico Inteligente

Sistema avanzado de monitoreo de tráfico con detección de vehículos, reconocimiento de placas y medición de velocidad en tiempo real.

**Desarrollado por [Cognidata AI](https://cognidata.ai)**

## Características

- **Detección de Placas**: Reconocimiento automático de placas vehiculares con validación de formato
- **Conteo de Objetos**: Detección y seguimiento de múltiples tipos de objetos (autos, camiones, buses, motos, personas, bicicletas, mascotas)
- **Medidor de Velocidad**: Cálculo de velocidad en tiempo real
- **Tracking Inteligente**: Sistema de seguimiento por centroide con IDs únicos
- **Línea de Conteo Configurable**: Ajusta la posición de la línea de conteo con un slider
- **Interfaz Intuitiva**: Diseño moderno con PyQt5

## Requisitos del Sistema

- **Python**: 3.12 (recomendado)
- **Sistema Operativo**: Windows, macOS, Linux
- **Memoria RAM**: 4GB mínimo (8GB recomendado)
- **Espacio en Disco**: 2GB para dependencias y modelos

## Instalación

### 1. Clonar el Repositorio

```bash
git clone <url-del-repositorio>
cd "Smart Traffic"
```

### 2. Crear Entorno Virtual

**En macOS/Linux:**
```bash
python3.12 -m venv venv
source venv/bin/activate
```

**En Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar Dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Nota:** La instalación puede tardar varios minutos debido al tamaño de TensorFlow y PyTorch.

### 4. Verificar Estructura de Archivos

Asegúrate de tener la siguiente estructura:

```
Smart Traffic/
├── main.py                    # Punto de entrada principal
├── requirements.txt           # Dependencias
├── assets/
│   ├── images/               # Iconos e imágenes
│   ├── labels/               # Etiquetas de modelos
│   ├── models/               # Modelos ML
│   │   ├── detect.tflite
│   │   └── license_plate_detector.pt
│   └── video/                # Videos de prueba
├── features/
│   ├── object_count/         # Módulo de conteo
│   └── plate_detector/       # Módulo de detección de placas
└── lib/                      # Utilidades compartidas
```

### 5. Descargar Modelos (si no están incluidos)

Los modelos se descargarán automáticamente la primera vez que ejecutes la aplicación:

- **YOLOv5s**: Se descarga desde ultralytics/yolov5
- **License Plate Detector**: Debe estar en `assets/models/license_plate_detector.pt`
- **TFLite Model**: Debe estar en `assets/models/detect.tflite`

## Ejecución

### Iniciar la Aplicación

```bash
# Asegúrate de que el entorno virtual esté activado
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Ejecutar la aplicación
python main.py
```

### Primera Ejecución

La primera vez que ejecutes la aplicación:

1. Se cargarán los modelos de ML (puede tardar 1-2 minutos)
2. Verás mensajes de TensorFlow y PyTorch en la consola (esto es normal)
3. La ventana principal se abrirá con 4 opciones en el menú superior

## Uso de la Aplicación

### 1. Detección de Placas

1. Haz clic en **"Detección de Placas"** en el menú superior
2. Selecciona la fuente de video:
   - **Archivo**: Busca un video MP4/AVI
   - **Stream RTSP**: Ingresa la URL del stream
3. Haz clic en **▶ (Play)** para iniciar
4. Las placas detectadas se mostrarán en el panel derecho
5. Solo se muestran placas con formato válido (ABC-1234)

**Características:**
- Confianza mínima: 90%
- Cooldown de 2 segundos entre detecciones
- Contador de placas únicas
- Medidor de velocidad integrado

### 2. Conteo de Objetos

1. Haz clic en **"Conteo de Objetos"** en el menú superior
2. Carga un video desde archivo o stream
3. Ajusta la **Posición de Línea** con el slider (20%-80%)
4. Haz clic en **▶ (Play)** para iniciar
5. Los objetos se etiquetarán como: "Auto 1", "Persona 2", etc.

**Línea de Conteo:**
- Verde: Objeto no contado aún
- Magenta: Objeto ya contado
- Amarilla: Línea de conteo

**Objetos Detectados:**
- Vehículos: Auto, Camión, Bus, Moto
- Otros: Persona, Bicicleta, Gato, Perro

### 3. Estadísticas

(Por implementar)

## Controles

### Botones de Reproducción

- **▶ Play**: Iniciar reproducción y detección
- **⏸ Pause**: Pausar temporalmente
- **⏹ Stop**: Detener y reiniciar

### Slider de Posición de Línea

- Arrastra el control para mover la línea de conteo
- Rango: 20% (arriba) - 80% (abajo)
- El cambio se aplica en tiempo real

## Solución de Problemas

### Error: "No module named 'PyQt5'"

```bash
pip install PyQt5
```

### Error: FFmpeg/OpenCV crash en macOS

La aplicación incluye correcciones automáticas. Si persiste:

```bash
brew install ffmpeg
```

### Rendimiento Lento

- Reduce la resolución del video
- Usa videos locales en lugar de streams RTSP
- Cierra otras aplicaciones pesadas
- Considera usar GPU si está disponible

### Modelos No Encontrados

Verifica que los archivos existan en:
- `assets/models/detect.tflite`
- `assets/models/license_plate_detector.pt`
- `assets/models/yolov5s.pt`
- `assets/labels/labelmap.txt`

## Configuración Avanzada

### Ajustar Confianza de Detección

Edita en el código fuente:

**Placas** (`features/plate_detector/detector.py`):
```python
if scores[i] > 0.90:  # Cambiar umbral (0.0-1.0)
```

**Objetos** (`features/object_count/object_count.py`):
```python
self.min_confidence = 0.65  # Cambiar confianza mínima
```

### Calibrar Medidor de Velocidad

Edita en `features/plate_detector/plate_detector_widget.py`:
```python
self.pixels_per_meter = 8.8  # Ajustar según tu cámara
```

### Ajustar Cooldown de Detección

Edita en `features/plate_detector/plate_detector_widget.py`:
```python
self.cooldown_frames = 60  # 60 frames = ~2 segundos a 30fps
```

## Estructura del Proyecto

```
Smart Traffic/
├── main.py                         # Aplicación principal
├── requirements.txt                # Dependencias
├── README.md                       # Esta documentación
├── CLAUDE.md                       # Documentación técnica
├── smart_traffic.db                # Base de datos SQLite
├── features/
│   ├── object_count/
│   │   ├── object_count.py        # Lógica de conteo
│   │   └── object_count_widget.py # UI de conteo
│   └── plate_detector/
│       ├── detector.py            # Detector TFLite
│       ├── plate.py               # Procesamiento de placas
│       └── plate_detector_widget.py # UI de detección
└── lib/
    ├── camera_capture.py          # Captura de video
    ├── util.py                    # Utilidades (OCR, validación)
    ├── database_manager.py        # Gestión de BD
    └── export_manager.py          # Exportación de datos
```

## Tecnologías Utilizadas

- **PyQt5**: Framework de interfaz gráfica
- **OpenCV**: Procesamiento de video e imágenes
- **YOLOv5**: Detección de objetos
- **TensorFlow Lite**: Detección de placas
- **EasyOCR**: Reconocimiento óptico de caracteres
- **NumPy/Pandas**: Procesamiento de datos
- **SQLite**: Base de datos local

## Contribuciones

Para contribuir al proyecto:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## Licencia

Este proyecto está licenciado bajo Apache License 2.0 - ver el archivo [LICENSE](LICENSE) para más detalles.

**Copyright © 2024 [Cognidata AI](https://cognidata.ai)**

## Desarrolladores

**Smart Traffic** fue creado y desarrollado por **Cognidata AI**, empresa especializada en soluciones de inteligencia artificial y visión por computadora.

- 🌐 Website: [https://cognidata.ai](https://cognidata.ai)
- 📧 Contacto: Para consultas comerciales y soporte

## Soporte

Para reportar bugs o solicitar funcionalidades, abre un issue en el repositorio.

---

**Desarrollado con ❤️ por Cognidata AI para el monitoreo inteligente de tráfico**
