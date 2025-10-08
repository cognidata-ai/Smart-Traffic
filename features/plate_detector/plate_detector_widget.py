import os
import cv2
import time
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtWidgets import (QWidget, QLabel, QSplitter, QVBoxLayout, QHBoxLayout,
                             QPushButton, QGroupBox, QComboBox, QLineEdit, QFileDialog,
                             QMessageBox, QListWidget, QListWidgetItem, QFrame)
from features.plate_detector.detector import Detector
from features.plate_detector.plate import Plate
from lib.camera_capture import CameraCapture


class PlateDetectorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.camera_capture = None
        self.detector = Detector()
        self.detected_plates = set()  # Set de placas ÚNICAS detectadas
        self.current_video_source = None
        self.last_plate_image = None
        self.detection_count = 0  # Contador total de detecciones

        # Variables para cálculo de velocidad
        self.tracked_vehicles = {}  # {id: {'positions': [(x,y,time)], 'speed': km/h}}
        self.next_vehicle_id = 0
        self.last_speed = 0
        self.pixels_per_meter = 8.8  # Calibración: ~8.8 pixels = 1 metro (ajustable)
        self.fps = 30  # FPS del video

        # Cooldown para evitar detecciones repetidas
        self.last_detection_time = 0
        self.detection_cooldown = 3.0  # 3 segundos de espera entre detecciones
        self.frames_since_detection = 0
        self.cooldown_frames = 60  # ~2 segundos a 30fps

        self.initUI()

    def initUI(self):
        """Inicializar interfaz"""
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)

        # ===== PANEL IZQUIERDO - VIDEO =====
        self.videoLabel = QLabel("Seleccione una fuente de video para comenzar")
        self.videoLabel.setAlignment(Qt.AlignCenter)
        self.videoLabel.setStyleSheet("background-color: #2b2b2b; color: white; border: 2px solid #444;")
        splitter.addWidget(self.videoLabel)

        # ===== PANEL DERECHO - CONTROLES =====
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_panel.setMaximumWidth(350)
        right_panel.setMinimumWidth(300)

        # === Fuente de Video ===
        video_source_group = QGroupBox("Fuente de Video")
        video_source_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; padding: 8px; }")
        video_source_layout = QVBoxLayout()

        # Tipo
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Tipo:"))
        self.source_type_combo = QComboBox()
        self.source_type_combo.addItems(["Archivo", "Stream RTSP"])
        self.source_type_combo.currentTextChanged.connect(self.on_source_type_changed)
        type_layout.addWidget(self.source_type_combo)
        video_source_layout.addLayout(type_layout)

        # Archivo
        self.file_widget = QWidget()
        file_layout = QVBoxLayout(self.file_widget)
        file_layout.setContentsMargins(0, 0, 0, 0)
        
        file_input_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Seleccione un video...")
        file_input_layout.addWidget(self.file_path_edit)

        browse_btn = QPushButton("📁")
        browse_btn.setMaximumWidth(40)
        browse_btn.clicked.connect(self.browse_video_file)
        file_input_layout.addWidget(browse_btn)
        file_layout.addLayout(file_input_layout)

        video_source_layout.addWidget(self.file_widget)

        # URL
        self.url_widget = QWidget()
        url_layout = QVBoxLayout(self.url_widget)
        url_layout.setContentsMargins(0, 0, 0, 0)
        
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("rtsp://user:pass@ip:port")
        url_layout.addWidget(QLabel("URL:"))
        url_layout.addWidget(self.url_edit)

        load_stream_btn = QPushButton("🌐 Conectar")
        load_stream_btn.clicked.connect(self.load_stream)
        url_layout.addWidget(load_stream_btn)
        
        self.url_widget.setVisible(False)
        video_source_layout.addWidget(self.url_widget)

        video_source_group.setLayout(video_source_layout)
        right_layout.addWidget(video_source_group)

        # === Controles ===
        playback_group = QGroupBox("Controles")
        playback_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; padding: 8px; }")
        playback_layout = QVBoxLayout()

        # Botones
        self.play_btn = QPushButton("▶")
        self.play_btn.setEnabled(False)
        self.play_btn.setMinimumHeight(45)
        play_font = QFont()
        play_font.setPointSize(20)
        self.play_btn.setFont(play_font)
        self.play_btn.setStyleSheet("""
            QPushButton {
                padding: 10px; background-color: #4caf50; color: white;
                font-weight: bold; border-radius: 5px; border: none;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #cccccc; color: #666666; }
        """)
        self.play_btn.clicked.connect(self.start_capture)
        playback_layout.addWidget(self.play_btn)

        self.pause_btn = QPushButton("⏸")
        self.pause_btn.setEnabled(False)
        self.pause_btn.setMinimumHeight(45)
        self.pause_btn.setFont(play_font)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                padding: 10px; background-color: #ff9800; color: white;
                font-weight: bold; border-radius: 5px; border: none;
            }
            QPushButton:hover { background-color: #e68900; }
            QPushButton:disabled { background-color: #cccccc; color: #666666; }
        """)
        self.pause_btn.clicked.connect(self.pause_capture)
        playback_layout.addWidget(self.pause_btn)

        self.stop_btn = QPushButton("⏹")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(45)
        self.stop_btn.setFont(play_font)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                padding: 10px; background-color: #f44336; color: white;
                font-weight: bold; border-radius: 5px; border: none;
            }
            QPushButton:hover { background-color: #da190b; }
            QPushButton:disabled { background-color: #cccccc; color: #666666; }
        """)
        self.stop_btn.clicked.connect(self.stop_capture)
        playback_layout.addWidget(self.stop_btn)

        playback_group.setLayout(playback_layout)
        right_layout.addWidget(playback_group)

        # === Última Placa Detectada ===
        plate_group = QGroupBox("Última Placa Detectada")
        plate_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; padding: 10px; }")
        plate_layout = QVBoxLayout()

        # Texto de la placa (grande, sin imagen)
        self.plate_text_label = QLabel("---")
        self.plate_text_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(36)
        font.setBold(True)
        self.plate_text_label.setFont(font)
        self.plate_text_label.setStyleSheet("""
            color: #00ff00;
            padding: 30px;
            background-color: #1e1e1e;
            border-radius: 8px;
            min-height: 80px;
            border: 2px solid #00ff00;
        """)
        plate_layout.addWidget(self.plate_text_label)

        # Total detectadas
        self.total_label = QLabel("Total detectadas: 0")
        self.total_label.setAlignment(Qt.AlignCenter)
        self.total_label.setStyleSheet("font-size: 13px; color: #888; padding: 8px; font-weight: bold;")
        plate_layout.addWidget(self.total_label)

        # Botón limpiar
        clear_btn = QPushButton("🗑️ Limpiar Historial")
        clear_btn.setStyleSheet("padding: 8px; background-color: #ff6b6b; color: white; font-weight: bold; border-radius: 4px;")
        clear_btn.clicked.connect(self.clear_history)
        plate_layout.addWidget(clear_btn)

        plate_group.setLayout(plate_layout)
        right_layout.addWidget(plate_group)

        # === Velocidad ===
        speed_group = QGroupBox("Velocidad")
        speed_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 12px; padding: 6px; }")
        speed_layout = QVBoxLayout()
        speed_layout.setSpacing(5)

        # Indicador de velocidad (más pequeño)
        self.speed_label = QLabel("0")
        self.speed_label.setAlignment(Qt.AlignCenter)
        speed_font = QFont()
        speed_font.setPointSize(28)
        speed_font.setBold(True)
        self.speed_label.setFont(speed_font)
        self.speed_label.setStyleSheet("""
            color: #00aaff;
            padding: 12px;
            background-color: #1e1e1e;
            border-radius: 6px;
            border: 2px solid #00aaff;
            min-height: 40px;
        """)
        speed_layout.addWidget(self.speed_label)

        # Unidad
        unit_label = QLabel("km/h")
        unit_label.setAlignment(Qt.AlignCenter)
        unit_label.setStyleSheet("font-size: 11px; color: #666; padding: 2px;")
        speed_layout.addWidget(unit_label)

        speed_group.setLayout(speed_layout)
        right_layout.addWidget(speed_group)

        # Espaciador
        right_layout.addStretch()

        splitter.addWidget(right_panel)
        splitter.setSizes([900, 100])
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

    def on_source_type_changed(self, source_type):
        """Cambiar entre archivo y stream"""
        if source_type == "Archivo":
            self.file_widget.setVisible(True)
            self.url_widget.setVisible(False)
        else:
            self.file_widget.setVisible(False)
            self.url_widget.setVisible(True)

    def browse_video_file(self):
        """Seleccionar archivo"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Video", "assets/video",
            "Videos (*.mp4 *.avi *.mov *.mkv);;Todos (*.*)"
        )
        if file_path:
            self.load_video_file(file_path)

    def load_video_file(self, file_path):
        """Cargar video"""
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Error", f"Archivo no encontrado:\n{file_path}")
            return

        self.file_path_edit.setText(file_path)
        self.current_video_source = file_path

        if self.camera_capture:
            self.camera_capture.stop_capture()

        self.camera_capture = CameraCapture()
        self.camera_capture.video_path = file_path
        self.play_btn.setEnabled(True)

    def load_stream(self):
        """Cargar stream"""
        url = self.url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Ingrese una URL válida")
            return

        self.current_video_source = url

        if self.camera_capture:
            self.camera_capture.stop_capture()

        self.camera_capture = CameraCapture()
        self.camera_capture.video_path = url
        self.play_btn.setEnabled(True)

    def start_capture(self):
        """Iniciar"""
        if self.camera_capture:
            self.camera_capture.frameCaptured.connect(self.updateVideoLabel)
            self.camera_capture.start_capture()
            self.play_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)

    def pause_capture(self):
        """Pausar"""
        if self.camera_capture:
            self.camera_capture.pause_capture()
            self.play_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)

    def stop_capture(self):
        """Detener"""
        if self.camera_capture:
            self.camera_capture.stop_capture()
            self.play_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.videoLabel.setText("Detenido")

    def clear_history(self):
        """Limpiar historial"""
        self.detected_plates = set()
        self.detection_count = 0
        self.plate_text_label.setText("---")
        self.total_label.setText("Total detectadas: 0")
        self.tracked_vehicles = {}
        self.next_vehicle_id = 0
        self.last_speed = 0
        self.speed_label.setText("0")
        self.last_detection_time = 0
        self.frames_since_detection = 0

    def calculate_speed(self, detections):
        """Calcular velocidad de vehículos detectados"""
        current_time = time.time()
        current_centroids = []

        # Obtener centroides de detecciones actuales
        for detection in detections:
            ymin, xmin, ymax, xmax = detection['box']
            centroid_x = (xmin + xmax) / 2
            centroid_y = (ymin + ymax) / 2
            current_centroids.append((centroid_x, centroid_y))

        # Tracking simple: asociar con vehículos existentes
        updated_vehicles = {}

        for centroid in current_centroids:
            # Buscar vehículo más cercano
            min_distance = float('inf')
            matched_id = None

            for vehicle_id, data in self.tracked_vehicles.items():
                if len(data['positions']) > 0:
                    last_pos = data['positions'][-1]
                    distance = np.sqrt((centroid[0] - last_pos[0])**2 + (centroid[1] - last_pos[1])**2)

                    if distance < min_distance and distance < 100:  # Max 100 pixels de movimiento
                        min_distance = distance
                        matched_id = vehicle_id

            # Si encontramos match, actualizar
            if matched_id is not None:
                vehicle_data = self.tracked_vehicles[matched_id]
                vehicle_data['positions'].append((centroid[0], centroid[1], current_time))

                # Mantener solo últimas 10 posiciones
                if len(vehicle_data['positions']) > 10:
                    vehicle_data['positions'] = vehicle_data['positions'][-10:]

                # Calcular velocidad si tenemos suficientes puntos
                if len(vehicle_data['positions']) >= 3:
                    positions = vehicle_data['positions']
                    first_pos = positions[0]
                    last_pos = positions[-1]

                    # Distancia en pixels
                    pixel_distance = np.sqrt(
                        (last_pos[0] - first_pos[0])**2 +
                        (last_pos[1] - first_pos[1])**2
                    )

                    # Tiempo en segundos
                    time_diff = last_pos[2] - first_pos[2]

                    if time_diff > 0 and pixel_distance > 5:  # Mínimo movimiento
                        # Convertir a metros
                        meters = pixel_distance / self.pixels_per_meter

                        # Velocidad en m/s
                        speed_ms = meters / time_diff

                        # Convertir a km/h
                        speed_kmh = speed_ms * 3.6

                        # Limitar valores razonables (0-200 km/h)
                        if 0 < speed_kmh < 200:
                            vehicle_data['speed'] = speed_kmh
                            self.last_speed = int(speed_kmh)

                updated_vehicles[matched_id] = vehicle_data
            else:
                # Nuevo vehículo
                new_id = self.next_vehicle_id
                self.next_vehicle_id += 1
                updated_vehicles[new_id] = {
                    'positions': [(centroid[0], centroid[1], current_time)],
                    'speed': 0
                }

        self.tracked_vehicles = updated_vehicles

        # Actualizar UI con la velocidad más reciente
        if self.last_speed > 0:
            self.speed_label.setText(str(self.last_speed))

            # Cambiar color según velocidad
            if self.last_speed < 60:
                color = "#00ff00"  # Verde
            elif self.last_speed < 100:
                color = "#ffaa00"  # Naranja
            else:
                color = "#ff0000"  # Rojo

            self.speed_label.setStyleSheet(f"""
                color: {color};
                padding: 12px;
                background-color: #1e1e1e;
                border-radius: 6px;
                border: 2px solid {color};
                min-height: 40px;
            """)

    def updateVideoLabel(self, frame):
        """Procesar frame"""
        result = self.detector.detect(frame)
        frame = result[0]
        detections = result[3] if len(result) > 3 else []  # Obtener detecciones

        # Calcular velocidad
        self.calculate_speed(detections)

        # Mostrar video
        height, width, channels = frame.shape
        bytes_per_line = channels * width
        p = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(p)
        self.videoLabel.setPixmap(pixmap.scaled(self.videoLabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

        # Incrementar contador de frames desde última detección
        self.frames_since_detection += 1

        # Detectar placa con confianza > 90% Y con cooldown
        if result[1] and self.frames_since_detection >= self.cooldown_frames:  # Alta confianza (> 90%) + cooldown
            try:
                # Intentar leer la placa
                plate_text = Plate(result[0]).get()

                # SOLO procesar si la placa tiene formato válido (ABC-1234)
                if plate_text and plate_text.strip() != "":
                    # Validar formato usando la función de util
                    from lib.util import license_complies_format

                    if license_complies_format(plate_text):
                        # Solo contar si es una placa nueva (única)
                        if plate_text not in self.detected_plates:
                            self.detected_plates.add(plate_text)
                            self.plate_text_label.setText(plate_text)
                            self.total_label.setText(f"Total detectadas: {len(self.detected_plates)}")

                            # Resetear cooldown
                            self.frames_since_detection = 0
                            self.last_detection_time = time.time()

                            print(f"✅ Placa detectada: {plate_text} | Total únicas: {len(self.detected_plates)} | Velocidad: {self.last_speed} km/h")
                        else:
                            # Si ya existe, solo actualizar display pero NO resetear cooldown
                            self.plate_text_label.setText(plate_text)
                    else:
                        print(f"⚠️ Placa rechazada (formato inválido): {plate_text}")
                else:
                    print(f"⚠️ No se pudo leer texto de placa (OCR falló)")

            except Exception as e:
                print(f"❌ Error detectando placa: {e}")
