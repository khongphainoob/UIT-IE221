"""
Abstract Base Class for all Financial Analytics & Machine Learning Serving Engines.
Enforces strict OOP Principles (Map 1:1 with StarUML Class Diagram):
- Encapsulation (`_` attributes: `_raw_data`, `_dataframe`, `_is_preprocessed`)
- Abstraction (`@abstractmethod`: `preprocess`, `execute_analysis`)
- Template Method (`run`, `run_inference`, `analyze`, `export_report`)
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import pandas as pd


class BaseFinancialAnalyzer(ABC):
    """
    Lớp trừu tượng cơ sở cho toàn bộ các Engine phân tích dữ liệu tài chính sinh viên.
    Đóng gói dữ liệu thô và DataFrame nội bộ thông qua tiền tố `_`.
    """

    def __init__(self, raw_transactions: List[Dict[str, Any]]):
        self._raw_data: List[Dict[str, Any]] = raw_transactions or []
        self._dataframe: pd.DataFrame = pd.DataFrame()
        self._is_preprocessed: bool = False
        self._last_report: Dict[str, Any] = {}

    @property
    def dataframe(self) -> pd.DataFrame:
        """Read-only property returning a defensive copy of the internal DataFrame."""
        return self._dataframe.copy()

    @property
    def is_preprocessed(self) -> bool:
        """Check whether `preprocess()` has been executed."""
        return self._is_preprocessed

    @abstractmethod
    def preprocess(self) -> pd.DataFrame:
        """
        Chuẩn hóa dữ liệu thô sang Pandas DataFrame (ép kiểu số thực, chuẩn hóa chuỗi thời gian).
        Bắt buộc các lớp con phải override.
        """
        raise NotImplementedError

    @abstractmethod
    def execute_analysis(self) -> Dict[str, Any]:
        """
        Thực thi thuật toán phân tích thống kê / học máy và trả về kết quả dạng Dictionary.
        Bắt buộc các lớp con phải override.
        """
        raise NotImplementedError

    def analyze(self, dataframe: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Phương thức `analyze(dataframe)` khớp 1:1 với StarUML Class Diagram.
        """
        if dataframe is not None:
            self._dataframe = dataframe.copy()
            self._is_preprocessed = True
        elif not self._is_preprocessed:
            self.preprocess()
        self._last_report = self.execute_analysis()
        return self._last_report

    def export_report(self) -> Dict[str, Any]:
        """
        Phương thức `export_report()` khớp 1:1 với StarUML Class Diagram.
        """
        if not self._last_report:
            return self.run()
        return self._last_report

    def run_inference(self) -> Dict[str, Any]:
        """
        Template Method điều phối quy trình chuẩn: Preprocess -> Execute Analysis.
        """
        if not self._is_preprocessed:
            self.preprocess()
        self._last_report = self.execute_analysis()
        return self._last_report

    def run(self) -> Dict[str, Any]:
        """Alias ngắn gọn cho `run_inference()`."""
        return self.run_inference()
