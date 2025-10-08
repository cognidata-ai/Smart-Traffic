#!/usr/bin/env python3
"""
Smart Traffic - Sistema de Monitoreo de Tráfico
"""
import os
# Fix para FFmpeg threading en macOS
os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp'
os.environ['OPENCV_VIDEOIO_PRIORITY_FFMPEG'] = '0'

import sys
import traceback
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QToolBar, QAction, QVBoxLayout, QWidget, QActionGroup, QMessageBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QPixmap

# Importaciones locales con manejo de errores
try:
    from features.plate_detector.plate_detector_widget import PlateDetectorWidget
    from lib.camera_capture import CameraCapture
    from features.object_count.object_count_widget import ObjectCountWidget
    from features.plate_detector.detector import Detector

    print("✅ Módulos cargados correctamente")
except ImportError as e:
    print(f"⚠️ Error importando módulos: {e}")
    sys.exit(1)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.actionGroup = None
        self.toolbar = None
        self.central_widget = None
        self.setWindowTitle("Smart Traffic")
        
        # Inicializar detector con manejo de errores
        try:
            self.detector = Detector()
        except Exception as e:
            print(f"Advertencia: No se pudo inicializar el detector: {e}")
            self.detector = None

        # NO inicializar camera_capture automáticamente para evitar crash en macOS
        # Se inicializará cuando el usuario seleccione una función que lo requiera
        self.camera_capture = None
        self.camera_label = QLabel()
        self.splitter_right = None
        
        # Configurar tamaño de ventana
        self.setMinimumSize(1280, 720)
        self.setMaximumSize(1280, 720)
        
        # Inicializar acciones
        self.start_action = None
        self.detector_action = None
        self.count_action = None
        self.std_action = None
        
        # Inicializar UI
        self.initUI()
        
        # Asegurar que la ventana se muestre
        self.show()
        self.raise_()
        self.activateWindow()

    def initUI(self):
        """Inicializa la interfaz de usuario"""
        try:
            self.toolbar = QToolBar()
            self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            self.addToolBar(Qt.TopToolBarArea, self.toolbar)
            self.actionGroup = QActionGroup(self)

            # Crear acciones con verificación de iconos
            self.start_action = self.create_action("assets/images/home.png", "Inicio")
            self.detector_action = self.create_action("assets/images/camera.png", "Detección de Placas")
            self.count_action = self.create_action("assets/images/conteo.png", "Conteo de Objetos")
            self.std_action = self.create_action("assets/images/std.png", "Estadísticas")

            # Agregar acciones al grupo
            for action in [self.start_action, self.detector_action,
                          self.count_action, self.std_action]:
                if action:
                    self.actionGroup.addAction(action)
                    self.toolbar.addAction(action)

            # Conectar acciones con manejo de errores
            if self.start_action:
                self.start_action.triggered.connect(self.safe_setInitialLayout)
            if self.detector_action:
                self.detector_action.triggered.connect(self.safe_setupPlateDetector)
            if self.count_action:
                self.count_action.triggered.connect(self.safe_setupCountLayout)
            if self.std_action:
                self.std_action.triggered.connect(self.safe_setupStdLayout)

            self.setupInitialLayout()
            
        except Exception as e:
            print(f"Error inicializando UI: {e}")
            self.show_error(f"Error inicializando la interfaz: {e}")

    def create_action(self, icon_path, text):
        """Crea una acción con manejo de errores para el icono"""
        try:
            import os
            if os.path.exists(icon_path):
                action = QAction(QIcon(icon_path), text, self)
            else:
                print(f"Icono no encontrado: {icon_path}")
                action = QAction(text, self)
            action.setCheckable(True)
            return action
        except Exception as e:
            print(f"Error creando acción {text}: {e}")
            return None

    def setupInitialLayout(self):
        """Configura el layout inicial"""
        try:
            self.central_widget = QWidget()
            self.setCentralWidget(self.central_widget)
            layout = QVBoxLayout(self.central_widget)
            layout.setContentsMargins(0, 0, 0, 0)

            image_label = QLabel(self.central_widget)

            import os
            if os.path.exists("assets/images/fondo.png"):
                pixmap = QPixmap("assets/images/fondo.png")
                image_label.setPixmap(pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            else:
                # Fondo con gradiente oscuro profesional
                image_label.setText("SMART TRAFFIC\n\nSistema Inteligente de Monitoreo")
                image_label.setStyleSheet("""
                    QLabel {
                        font-size: 32px;
                        font-weight: bold;
                        color: white;
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                                   stop:0 #1a1a2e,
                                                   stop:0.5 #16213e,
                                                   stop:1 #0f3460);
                        padding: 50px;
                    }
                """)

            image_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(image_label)
        except Exception as e:
            print(f"Error en setupInitialLayout: {e}")

    # Métodos seguros con manejo de errores
    def safe_setInitialLayout(self, checked):
        if checked:
            try:
                self.clearLayout()
                self.setupInitialLayout()
            except Exception as e:
                self.handle_error(e)

    def safe_setupPlateDetector(self, checked):
        if checked:
            try:
                self.clearLayout()
                captureWidget = PlateDetectorWidget()
                self.setCentralWidget(captureWidget)
            except Exception as e:
                self.handle_error(e)
                self.setupInitialLayout()

    def safe_setupCountLayout(self, checked):
        if checked:
            try:
                self.clearLayout()
                # Usar widget mejorado de conteo de objetos
                objectCount = ObjectCountWidget()
                self.setCentralWidget(objectCount)
                print("✅ Widget de conteo de objetos cargado")
            except Exception as e:
                print(f"❌ Error cargando conteo: {e}")
                self.handle_error(e)
                self.setupInitialLayout()

    def safe_setupStdLayout(self, checked):
        if checked:
            self.clearLayout()
            # Por implementar
            label = QLabel("Estadísticas - Por implementar")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-size: 18px; padding: 20px;")
            self.setCentralWidget(label)

    def clearLayout(self):
        """Limpia el layout actual"""
        try:
            if self.centralWidget():
                self.centralWidget().deleteLater()
        except Exception as e:
            print(f"Error limpiando layout: {e}")

    def handle_error(self, error):
        """Maneja errores y muestra mensaje al usuario"""
        print(f"Error: {error}")
        traceback.print_exc()
        self.show_error(f"Error: {error}")

    def show_error(self, message):
        """Muestra un mensaje de error al usuario"""
        try:
            QMessageBox.critical(self, "Error", message)
        except:
            print(f"Error crítico: {message}")

    def closeEvent(self, event):
        """Maneja el cierre de la aplicación"""
        try:
            if self.camera_capture:
                self.camera_capture.stop_capture()
        except:
            pass
        event.accept()


def main():
    """Función principal"""
    try:
        print("Iniciando Smart Traffic...")
        app = QApplication(sys.argv)
        app.setApplicationName("Smart Traffic")
        app.setStyle('Fusion')
        
        # Crear ventana principal
        window = MainWindow()
        
        # Configurar manejo de excepciones global
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            print("Error no capturado:")
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            
        sys.excepthook = handle_exception
        
        # Ejecutar aplicación
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"Error fatal: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()