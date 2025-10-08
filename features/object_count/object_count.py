import cv2
import torch
import numpy as np
from collections import deque


class ObjectCount:
    """Contador de vehículos mejorado con tracking simple"""

    def __init__(self):
        super().__init__()
        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)

        # Sistema de tracking
        self.next_object_id = 0
        self.tracked_objects = {}
        self.count_detection = 0

        # Parámetros
        self.max_disappeared = 40
        self.max_distance = 80
        self.min_confidence = 0.65

        # Vehículos a detectar
        self.vehicle_classes = ['car', 'truck', 'bus', 'motorcycle', 'person', 'bicycle', 'cat', 'dog']

        # Conteo por línea
        self.counted_ids = set()
        self.counting_line_y = None
        self.line_position = 0.55  # Posición por defecto: 55% del frame

        # Contador por tipo de objeto
        self.object_type_counters = {}  # {'car': 1, 'person': 1, ...}

        # Traducción de nombres al español
        self.class_names_es = {
            'car': 'Auto',
            'truck': 'Camión',
            'bus': 'Bus',
            'motorcycle': 'Moto',
            'person': 'Persona',
            'bicycle': 'Bicicleta',
            'cat': 'Gato',
            'dog': 'Perro'
        }
        
    def set_counting_line(self, frame_height, position=0.5):
        """Establecer línea de conteo"""
        self.counting_line_y = int(frame_height * position)
        
    def euclidean_distance(self, point1, point2):
        """Calcular distancia euclidiana entre dos puntos"""
        return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
        
    def register_object(self, centroid, bbox, class_name):
        """Registrar nuevo objeto"""
        # Incrementar contador para este tipo de objeto
        if class_name not in self.object_type_counters:
            self.object_type_counters[class_name] = 0

        self.object_type_counters[class_name] += 1
        object_type_id = self.object_type_counters[class_name]

        # Obtener nombre en español
        display_name = self.class_names_es.get(class_name, class_name.capitalize())

        self.tracked_objects[self.next_object_id] = {
            'centroid': centroid,
            'bbox': bbox,
            'disappeared': 0,
            'prev_centroid': centroid,
            'class_name': class_name,
            'display_name': f"{display_name} {object_type_id}"
        }
        self.next_object_id += 1
        
    def deregister_object(self, object_id):
        """Eliminar objeto"""
        if object_id in self.tracked_objects:
            del self.tracked_objects[object_id]
        
    def update_tracking(self, detections):
        """Actualizar tracking con Hungarian algorithm simplificado"""

        # Si no hay objetos trackeados, registrar todos
        if len(self.tracked_objects) == 0:
            for centroid, bbox, class_name in detections:
                self.register_object(centroid, bbox, class_name)
            return
            
        # Si no hay nuevas detecciones
        if len(detections) == 0:
            for object_id in list(self.tracked_objects.keys()):
                self.tracked_objects[object_id]['disappeared'] += 1
                if self.tracked_objects[object_id]['disappeared'] > self.max_disappeared:
                    self.deregister_object(object_id)
            return
        
        # Matching simple: para cada objeto trackeado, encontrar la detección más cercana
        object_ids = list(self.tracked_objects.keys())
        used_detections = set()
        
        # Ordenar objetos por menor desaparición (más confiables primero)
        object_ids.sort(key=lambda oid: self.tracked_objects[oid]['disappeared'])
        
        for object_id in object_ids:
            obj_centroid = self.tracked_objects[object_id]['centroid']
            obj_class = self.tracked_objects[object_id]['class_name']

            # Encontrar detección más cercana no usada DE LA MISMA CLASE
            min_distance = float('inf')
            best_match = None

            for idx, (det_centroid, det_bbox, det_class) in enumerate(detections):
                if idx in used_detections:
                    continue

                # Solo emparejar objetos de la misma clase
                if det_class != obj_class:
                    continue

                distance = self.euclidean_distance(obj_centroid, det_centroid)

                if distance < min_distance and distance < self.max_distance:
                    min_distance = distance
                    best_match = idx

            # Si encontramos un match
            if best_match is not None:
                self.tracked_objects[object_id]['prev_centroid'] = self.tracked_objects[object_id]['centroid']
                self.tracked_objects[object_id]['centroid'] = detections[best_match][0]
                self.tracked_objects[object_id]['bbox'] = detections[best_match][1]
                self.tracked_objects[object_id]['disappeared'] = 0
                used_detections.add(best_match)
            else:
                # No encontró match, incrementar desaparición
                self.tracked_objects[object_id]['disappeared'] += 1
                if self.tracked_objects[object_id]['disappeared'] > self.max_disappeared:
                    self.deregister_object(object_id)

        # Registrar detecciones no matcheadas como nuevos objetos
        for idx, (centroid, bbox, class_name) in enumerate(detections):
            if idx not in used_detections:
                self.register_object(centroid, bbox, class_name)
                
    def check_line_crossing(self, object_id):
        """Verificar si cruzó la línea"""
        if self.counting_line_y is None:
            return False
            
        if object_id in self.counted_ids:
            return False
            
        if object_id not in self.tracked_objects:
            return False
            
        obj = self.tracked_objects[object_id]
        prev_y = obj['prev_centroid'][1]
        curr_y = obj['centroid'][1]
        
        # Cruzó de arriba hacia abajo
        if prev_y < self.counting_line_y <= curr_y:
            self.counted_ids.add(object_id)
            self.count_detection += 1
            print(f"✅ Vehículo {object_id} contado! Total: {self.count_detection}")
            return True
            
        return False
        
    def get_bboxes(self, prediction):
        """Obtener detecciones"""
        df = prediction.pandas().xyxy[0]
        df = df[df["confidence"] >= self.min_confidence]
        df = df[df["name"].isin(self.vehicle_classes)]

        detections = []
        for _, row in df.iterrows():
            bbox = [int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])]
            centroid = self.get_center(bbox)
            class_name = row['name']
            detections.append((centroid, bbox, class_name))

        return detections
        
    @staticmethod
    def get_center(bbox):
        """Calcular centroide"""
        center_x = (bbox[0] + bbox[2]) // 2
        center_y = (bbox[1] + bbox[3]) // 2
        return (center_x, center_y)
        
    def start_detector_no_text(self, frame):
        """Detectar sin texto en frame"""
        # Establecer línea de conteo (usar posición configurable)
        if self.counting_line_y is None:
            self.set_counting_line(frame.shape[0], position=self.line_position)
            
        # Detectar
        prediction = self.model(frame)
        detections = self.get_bboxes(prediction)
        
        # Actualizar tracking
        self.update_tracking(detections)
        
        # Dibujar línea de conteo
        cv2.line(frame, (0, self.counting_line_y), 
                (frame.shape[1], self.counting_line_y), (0, 255, 255), 3)
        cv2.putText(frame, "LINEA DE CONTEO", (10, self.counting_line_y - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Dibujar objetos y verificar cruces
        for object_id, obj in list(self.tracked_objects.items()):
            bbox = obj['bbox']
            centroid = obj['centroid']
            display_name = obj['display_name']

            # Verificar cruce
            self.check_line_crossing(object_id)

            # Color según estado
            if object_id in self.counted_ids:
                color = (255, 0, 255)  # Magenta: ya contado
            else:
                color = (0, 255, 0)    # Verde: no contado

            # Dibujar bbox
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)

            # Dibujar centroide
            cv2.circle(frame, centroid, 5, color, -1)

            # Dibujar nombre con clasificación (ej: "Auto 1", "Persona 3")
            label_size, _ = cv2.getTextSize(display_name, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)

            # Fondo para el texto
            cv2.rectangle(frame,
                         (bbox[0], bbox[1] - label_size[1] - 10),
                         (bbox[0] + label_size[0], bbox[1]),
                         color, -1)

            # Texto en negro sobre fondo de color
            cv2.putText(frame, display_name, (bbox[0], bbox[1] - 8),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
                   
        return frame
        
    def start_detector(self, frame):
        """Detectar con texto"""
        return self.start_detector_no_text(frame)
