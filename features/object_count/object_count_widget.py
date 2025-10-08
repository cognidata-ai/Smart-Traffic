from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QGroupBox, QComboBox, QLineEdit,
                             QFileDialog, QSplitter, QFrame, QMessageBox, QSlider)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QFont
import cv2
import os

from lib.camera_capture import CameraCapture
from features.object_count.object_count import ObjectCount


class ObjectCountWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.camera_capture = None
        self.objectCount = ObjectCount()
        self.current_video_source = None
        self.initUI()

    def initUI(self):
        """Inicializar interfaz de usuario"""
        # Layout principal con splitter horizontal
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)

        # ===== PANEL IZQUIERDO - SOLO VIDEO (90%) =====
        self.videoLabel = QLabel("Seleccione una fuente de video para comenzar")
        self.videoLabel.setAlignment(Qt.AlignCenter)
        self.videoLabel.setStyleSheet("background-color: #2b2b2b; color: white; border: 2px solid #444;")
        splitter.addWidget(self.videoLabel)

        # ===== PANEL DERECHO - CONTROLES Y CONTADOR (10%) =====
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_panel.setMaximumWidth(350)
        right_panel.setMinimumWidth(300)

        # === Selección de Fuente de Video ===
        video_source_group = QGroupBox("Fuente de Video")
        video_source_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; padding: 8px; }")
        video_source_layout = QVBoxLayout()

        # Tipo de fuente
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Tipo:"))
        self.source_type_combo = QComboBox()
        self.source_type_combo.addItems(["Archivo", "Stream RTSP"])
        self.source_type_combo.currentTextChanged.connect(self.on_source_type_changed)
        type_layout.addWidget(self.source_type_combo)
        video_source_layout.addLayout(type_layout)

        # Container para archivo
        self.file_widget = QWidget()
        file_layout = QVBoxLayout(self.file_widget)
        file_layout.setContentsMargins(0, 0, 0, 0)
        
        file_input_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Seleccione un video...")
        file_input_layout.addWidget(self.file_path_edit)

        browse_btn = QPushButton("📁")
        browse_btn.setMaximumWidth(40)
        browse_btn.setToolTip("Buscar archivo")
        browse_btn.clicked.connect(self.browse_video_file)
        file_input_layout.addWidget(browse_btn)
        file_layout.addLayout(file_input_layout)

        video_source_layout.addWidget(self.file_widget)

        # Container para URL
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

        # === Controles de Reproducción ===
        playback_group = QGroupBox("Controles")
        playback_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; padding: 8px; }")
        playback_layout = QVBoxLayout()

        # Botones con iconos grandes
        self.play_btn = QPushButton("▶")
        self.play_btn.setEnabled(False)
        self.play_btn.setMinimumHeight(45)
        play_font = QFont()
        play_font.setPointSize(20)
        self.play_btn.setFont(play_font)
        self.play_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                background-color: #4caf50;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.play_btn.setToolTip("Iniciar reproducción")
        self.play_btn.clicked.connect(self.start_capture)
        playback_layout.addWidget(self.play_btn)

        self.pause_btn = QPushButton("⏸")
        self.pause_btn.setEnabled(False)
        self.pause_btn.setMinimumHeight(45)
        pause_font = QFont()
        pause_font.setPointSize(20)
        self.pause_btn.setFont(pause_font)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                background-color: #ff9800;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.pause_btn.setToolTip("Pausar reproducción")
        self.pause_btn.clicked.connect(self.pause_capture)
        playback_layout.addWidget(self.pause_btn)

        self.stop_btn = QPushButton("⏹")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(45)
        stop_font = QFont()
        stop_font.setPointSize(20)
        self.stop_btn.setFont(stop_font)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                background-color: #f44336;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.stop_btn.setToolTip("Detener reproducción")
        self.stop_btn.clicked.connect(self.stop_capture)
        playback_layout.addWidget(self.stop_btn)

        playback_group.setLayout(playback_layout)
        right_layout.addWidget(playback_group)

        # === Posición de Línea de Conteo ===
        line_group = QGroupBox("Posición de Línea")
        line_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; padding: 8px; }")
        line_layout = QVBoxLayout()

        # Label con posición actual
        position_info_layout = QHBoxLayout()
        position_info_layout.addWidget(QLabel("Posición:"))
        self.position_label = QLabel("55%")
        self.position_label.setStyleSheet("font-weight: bold; color: #00aaff;")
        position_info_layout.addWidget(self.position_label)
        position_info_layout.addStretch()
        line_layout.addLayout(position_info_layout)

        # Slider para ajustar posición
        self.line_slider = QSlider(Qt.Horizontal)
        self.line_slider.setMinimum(20)  # 20% del frame
        self.line_slider.setMaximum(80)  # 80% del frame
        self.line_slider.setValue(55)    # Por defecto 55%
        self.line_slider.setTickPosition(QSlider.TicksBelow)
        self.line_slider.setTickInterval(10)
        self.line_slider.valueChanged.connect(self.on_line_position_changed)
        self.line_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #999;
                height: 8px;
                background: #1e1e1e;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #00aaff;
                border: 1px solid #0088cc;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #00ccff;
            }
        """)
        line_layout.addWidget(self.line_slider)

        # Indicadores de posición
        indicators_layout = QHBoxLayout()
        label_arriba = QLabel("Arriba")
        label_arriba.setStyleSheet("font-size: 10px; color: #888;")
        label_abajo = QLabel("Abajo")
        label_abajo.setStyleSheet("font-size: 10px; color: #888;")
        indicators_layout.addWidget(label_arriba)
        indicators_layout.addStretch()
        indicators_layout.addWidget(label_abajo)
        line_layout.addLayout(indicators_layout)

        line_group.setLayout(line_layout)
        right_layout.addWidget(line_group)

        # === Contador al Final ===
        counter_group = QGroupBox("Contador")
        counter_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; padding: 8px; }")
        counter_layout = QVBoxLayout()

        self.counterLabel = QLabel("0")
        self.counterLabel.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(36)
        font.setBold(True)
        self.counterLabel.setFont(font)
        self.counterLabel.setStyleSheet("color: #00ff00; padding: 15px; background-color: #1e1e1e; border-radius: 5px;")
        counter_layout.addWidget(self.counterLabel)

        vehicles_label = QLabel("vehículos")
        vehicles_label.setAlignment(Qt.AlignCenter)
        vehicles_label.setStyleSheet("font-size: 12px; color: #666;")
        counter_layout.addWidget(vehicles_label)

        reset_btn = QPushButton("🔄 Reiniciar")
        reset_btn.setStyleSheet("padding: 6px; background-color: #ff6b6b; color: white; font-weight: bold;")
        reset_btn.clicked.connect(self.reset_counter)
        counter_layout.addWidget(reset_btn)

        counter_group.setLayout(counter_layout)
        right_layout.addWidget(counter_group)

        # Espaciador
        right_layout.addStretch()

        splitter.addWidget(right_panel)

        # Proporciones: 80% video, 20% controles
        splitter.setSizes([900, 100])
        splitter.setStretchFactor(0, 4)  # Video se estira más
        splitter.setStretchFactor(1, 1)  # Controles fijos

        main_layout.addWidget(splitter)

    def on_source_type_changed(self, source_type):
        """Cambiar entre archivo y stream"""
        if source_type == "Archivo":
            self.file_widget.setVisible(True)
            self.url_widget.setVisible(False)
        else:
            self.file_widget.setVisible(False)
            self.url_widget.setVisible(True)

    def on_line_position_changed(self, value):
        """Cambiar posición de línea de conteo"""
        self.position_label.setText(f"{value}%")
        # Actualizar la posición en el detector
        if hasattr(self, 'objectCount') and self.objectCount:
            # Forzar actualización en el próximo frame
            self.objectCount.counting_line_y = None
            self.objectCount.line_position = value / 100.0  # Convertir a decimal

    def browse_video_file(self):
        """Abrir diálogo para seleccionar archivo de video"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Video",
            "assets/video",
            "Videos (*.mp4 *.avi *.mov *.mkv);;Todos (*.*)"
        )

        if file_path:
            self.load_video_file(file_path)

    def load_video_file(self, file_path):
        """Cargar archivo de video"""
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
        """Cargar stream RTSP/HTTP"""
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
        """Iniciar captura"""
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

    def reset_counter(self):
        """Reiniciar contador"""
        self.objectCount.count_detection = 0
        self.objectCount.detected_cars = []
        self.counterLabel.setText("0")

    def updateVideoLabel(self, frame):
        """Procesar y mostrar frame"""
        frame = self.objectCount.start_detector_no_text(frame)
        self.counterLabel.setText(str(self.objectCount.count_detection))

        height, width, channels = frame.shape
        bytes_per_line = channels * width
        p = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(p)
        self.videoLabel.setPixmap(pixmap.scaled(self.videoLabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
