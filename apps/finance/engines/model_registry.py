"""
MLModelRegistry (Singleton Pattern) for Real-time Machine Learning Serving.
Loads and caches serialized Scikit-learn artifacts (`artifacts/*.joblib`) into RAM once.
"""
from pathlib import Path
from threading import Lock
from typing import Any, Dict
import joblib
import numpy as np
from django.conf import settings
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.linear_model import HuberRegressor


class MLModelRegistry:
    """
    Singleton Pattern quản lý vòng đời các mô hình Học máy (Artifact Serialization & RAM Caching):
    - `burn_rate_huber`: HuberRegressor kháng nhiễu cho dự báo tốc độ tiêu tiền
    - `anomaly_iforest`: IsolationForest cho phát hiện giao dịch bất thường
    - `risk_rf_classifier`: RandomForestClassifier cho phân loại rủi ro vỡ ngân sách cuối tháng
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
        self._artifact_dir.mkdir(parents=True, exist_ok=True)
        self._initialized = True

    @classmethod
    def get_instance(cls) -> "MLModelRegistry":
        """Trả về thực thể duy nhất (Singleton instance) của MLModelRegistry."""
        return cls()

    def get_model(self, model_name: str) -> Any:
        """
        Lấy model từ bộ nhớ đệm RAM; nếu chưa nạp thì đọc từ `artifacts/<model_name>.joblib`.
        Nếu file artifact chưa tồn tại, tự động khởi tạo & huấn luyện baseline rồi lưu đĩa.
        """
        if model_name in self._models:
            return self._models[model_name]

        artifact_path = self._artifact_dir / f"{model_name}.joblib"
        if artifact_path.exists():
            model = joblib.load(artifact_path)
        else:
            model = self._build_and_persist_default_model(model_name, artifact_path)

        self._models[model_name] = model
        return model

    def _build_and_persist_default_model(
        self, model_name: str, artifact_path: Path
    ) -> Any:
        """Huấn luyện baseline model với dữ liệu sinh viên đặc trưng và đóng gói bằng joblib."""
        rng = np.random.RandomState(221)

        if model_name == "burn_rate_huber":
            model = HuberRegressor(max_iter=200, alpha=1.35)
            X_syn = np.arange(30, dtype=float).reshape(-1, 1)
            y_syn = 85000.0 * np.arange(1, 31, dtype=float)
            model.fit(X_syn, y_syn)

        elif model_name == "anomaly_iforest":
            normal_tx = rng.normal(loc=45000.0, scale=15000.0, size=(120, 1))
            outliers = np.array([[850000.0], [1200000.0], [1500000.0]])
            X_syn = np.vstack([np.clip(normal_tx, 10000.0, None), outliers])
            model = IsolationForest(
                n_estimators=100, contamination=0.05, random_state=221
            )
            model.fit(X_syn)

        elif model_name == "risk_rf_classifier":
            # Features: [budget_usage_ratio, burn_to_allowance_ratio, non_essential_ratio, anomaly_ratio]
            # Classes: 0 = SAFE, 1 = WARNING, 2 = HIGH_RISK_BROKE
            X_safe = np.column_stack(
                [
                    rng.uniform(0.1, 0.65, 60),
                    rng.uniform(0.3, 0.85, 60),
                    rng.uniform(0.05, 0.30, 60),
                    rng.uniform(0.0, 0.03, 60),
                ]
            )
            y_safe = np.zeros(60, dtype=int)

            X_warn = np.column_stack(
                [
                    rng.uniform(0.66, 0.90, 60),
                    rng.uniform(0.86, 1.15, 60),
                    rng.uniform(0.25, 0.50, 60),
                    rng.uniform(0.02, 0.08, 60),
                ]
            )
            y_warn = np.ones(60, dtype=int)

            X_broke = np.column_stack(
                [
                    rng.uniform(0.91, 1.60, 60),
                    rng.uniform(1.16, 2.50, 60),
                    rng.uniform(0.40, 0.85, 60),
                    rng.uniform(0.05, 0.25, 60),
                ]
            )
            y_broke = np.full(60, 2, dtype=int)

            X_train = np.vstack([X_safe, X_warn, X_broke])
            y_train = np.concatenate([y_safe, y_warn, y_broke])

            model = RandomForestClassifier(
                n_estimators=100, max_depth=6, random_state=221
            )
            model.fit(X_train, y_train)
        else:
            raise ValueError(f"Model '{model_name}' không được hỗ trợ trong MLModelRegistry.")

        joblib.dump(model, artifact_path)
        return model

