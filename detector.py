from typing import Any, Dict, List, Optional

import cv2

try:
    from ultralytics import YOLO
except Exception:  # pragma: no cover - import fallback for minimal environments
    YOLO = None  # type: ignore


class PersonDetector:
    """Person detector with Ultralytics first, OpenCV HOG fallback."""

    def __init__(self, model_path: str, confidence_threshold: float = 0.5) -> None:
        self.model_path = model_path
        self.confidence_threshold = float(confidence_threshold)
        self.backend: str = "hog"
        self.model: Optional[Any] = None
        self.hog = None

        if str(model_path).lower() == "hog":
            self._init_hog()
            return

        if YOLO is None:
            self._init_hog()
            return

        try:
            self.model = YOLO(model_path)
            self.backend = "ultralytics"
        except Exception:
            self._init_hog()

    def _init_hog(self) -> None:
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        self.backend = "hog"
        self.model = None

    def _detect_with_hog(self, frame: Any) -> List[Dict[str, Any]]:
        rects, weights = self.hog.detectMultiScale(
            frame,
            winStride=(8, 8),
            padding=(8, 8),
            scale=1.05,
        )

        detections: List[Dict[str, Any]] = []
        for (x, y, w, h), weight in zip(rects, weights):
            confidence = float(weight)
            if confidence < self.confidence_threshold:
                continue
            detections.append(
                {
                    "confidence": confidence,
                    "bbox": [float(x), float(y), float(x + w), float(y + h)],
                }
            )
        return detections

    def _detect_with_ultralytics(self, frame: Any) -> List[Dict[str, Any]]:
        results = self.model.predict(source=frame, verbose=False)[0]
        detections: List[Dict[str, Any]] = []

        if results.boxes is None:
            return detections

        for box in results.boxes:
            cls_id = int(box.cls[0])
            confidence = float(box.conf[0])

            # COCO person class
            if cls_id != 0 or confidence < self.confidence_threshold:
                continue

            x1, y1, x2, y2 = box.xyxy[0].tolist()
            detections.append(
                {
                    "confidence": confidence,
                    "bbox": [float(x1), float(y1), float(x2), float(y2)],
                }
            )

        return detections

    def detect(self, frame: Any) -> List[Dict[str, Any]]:
        if self.backend == "ultralytics" and self.model is not None:
            try:
                return self._detect_with_ultralytics(frame)
            except Exception:
                self._init_hog()
                return self._detect_with_hog(frame)

        return self._detect_with_hog(frame)
