"""
MLModelRegistry (Singleton Pattern) for Real-time Machine Learning & Deep Learning Serving.
Strictly separated from model training: ONLY loads pre-trained serialized artifacts
(`artifacts/*.joblib`) into RAM once and serves them for real-time inference.
"""
from pathlib import Path
from threading import Lock
from typing import Any, Dict
import joblib
from django.conf import settings


class MLModelRegistry:
    """
    Singleton Pattern quản lý nạp và lưu đệm (RAM Caching) các mô hình đã huấn luyện sẵn:
    - `burn_rate_huber`: Pre-trained HuberRegressor (`artifacts/burn_rate_huber.joblib`)
    - `anomaly_iforest`: Pre-trained IsolationForest (`artifacts/anomaly_iforest.joblib`)
    - `risk_rf_classifier`: Pre-trained RandomForestClassifier (`artifacts/risk_rf_classifier.joblib`)
    - `deep_mlp_risk`: Pre-trained Deep Neural Network MLPClassifier (`artifacts/deep_mlp_risk.joblib`)
    """

    _instance: "MLModelRegistry | None" = None
    _lock: Lock = Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._models: Dict[str, Any] = {}
        self._artifact_dir: Path = Path(settings.BASE_DIR) / "artifacts"
        self._initialized = True

    @classmethod
    def get_instance(cls) -> "MLModelRegistry":
        """Trả về thực thể duy nhất (Singleton instance) của MLModelRegistry."""
        return cls()

    def get_model(self, model_name: str) -> Any:
        """
        Lấy pre-trained model từ bộ nhớ đệm RAM (`_models`).
        Nếu chưa có trên RAM thì đọc 1 lần duy nhất từ file `artifacts/<model_name>.joblib`.
        Tuyệt đối không huấn luyện (fit) trong luồng Serving trực tuyến.
        """
        if model_name in self._models:
            return self._models[model_name]

        artifact_path = self._artifact_dir / f"{model_name}.joblib"
        if not artifact_path.exists():
            raise FileNotFoundError(
                f"Không tìm thấy pre-trained artifact tại '{artifact_path}'. "
                f"Hãy chạy `python scripts/train_offline_artifacts.py` trước khi khởi động server."
            )

        model = joblib.load(artifact_path)
        self._models[model_name] = model
        return model
