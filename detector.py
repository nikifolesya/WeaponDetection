import os
import uuid
import cv2
import numpy as np
from roboflow import Roboflow
import supervision as sv

class WeaponDetector:
    def __init__(self, api_key):
        self.rf = Roboflow(api_key=api_key)
        self.project = self.rf.workspace().project("yolo-weapon-detection")
        self.model = self.project.version(2).model
        print("Roboflow model initialized successfully")
    
    def detect_image(self, image_path):
        result = self.model.predict(image_path, confidence=40, overlap=30).json()
        
        labels = [item["class"] for item in result["predictions"]]
        
        detections = sv.Detections.from_inference(result)
        
        label_annotator = sv.LabelAnnotator()
        box_annotator = sv.BoxAnnotator()
        
        image = cv2.imread(image_path)
        
        annotated_image = box_annotator.annotate(scene=image, detections=detections)
        annotated_image = label_annotator.annotate(scene=annotated_image, detections=detections, labels=labels)
        
        result_path = os.path.join('static/results', f"{uuid.uuid4().hex}_result.jpg")
        cv2.imwrite(result_path, annotated_image)
        
        return result_path, result["predictions"]
    
    def detect_video(self, video_path):
        target_video_path = os.path.join('static/results', f"{uuid.uuid4().hex}_result.mp4")

        video_info = sv.VideoInfo.from_video_path(video_path)
        byte_tracker = sv.ByteTrack()

        box_annotator = sv.BoxAnnotator()
        label_annotator = sv.LabelAnnotator()

        all_detections = []  # Список уникальных детекций
        seen_tracker_ids = set()  # Множество для отслеживания уникальных tracker_id

        def callback(frame: np.ndarray, index: int) -> np.ndarray:
            results = self.model.predict(frame).json()
            detections = sv.Detections.from_inference(results)

            detections = byte_tracker.update_with_detections(detections)

            labels = [
                f"#{detections.tracker_id[i]} {results['predictions'][i]['class']} {detections.confidence[i]:.2f}"
                for i in range(len(detections))
            ]

            # Добавляем только уникальные детекции
            for i in range(len(detections)):
                tracker_id = int(detections.tracker_id[i])
                if tracker_id not in seen_tracker_ids:
                    seen_tracker_ids.add(tracker_id)  # Добавляем tracker_id в множество
                    all_detections.append({
                        "x": int(detections.xyxy[i][0]),
                        "y": int(detections.xyxy[i][1]),
                        "width": int(detections.xyxy[i][2] - detections.xyxy[i][0]),
                        "height": int(detections.xyxy[i][3] - detections.xyxy[i][1]),
                        "confidence": float(detections.confidence[i]),
                        "class": results['predictions'][i]['class'],
                        "tracker_id": tracker_id
                    })

            annotated_frame = box_annotator.annotate(scene=frame, detections=detections)
            annotated_frame = label_annotator.annotate(scene=annotated_frame, detections=detections, labels=labels)

            return annotated_frame

        sv.process_video(
            source_path=video_path,
            target_path=target_video_path,
            callback=callback
        )

        return target_video_path, all_detections