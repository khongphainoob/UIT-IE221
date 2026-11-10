"""
Report Exporter Engine applying Strategy Pattern (Polymorphism - Map 1:1 with StarUML).
`CSVReportExporter` and `ExcelReportExporter` both override `generate()`.
"""
import csv
import io
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from openpyxl import Workbook


class BaseReportExporter(ABC):
    """
    Lớp cơ sở trừu tượng cho bộ xuất báo cáo tài chính sinh viên (Strategy Pattern).
    """

    content_type: str
    file_extension: str

    def __init__(self, transactions: List[Dict[str, Any]], summary: Dict[str, Any]):
        self._transactions = transactions or []
        self._summary = summary or {}

    @abstractmethod
    def generate(self) -> bytes:
        """Phương thức đa hình `generate()` tạo nội dung file nhị phân (CSV hoặc Excel)."""
        raise NotImplementedError


class CSVReportExporter(BaseReportExporter):
    """Xuất báo cáo giao dịch chi tiêu ra định dạng CSV (UTF-8 with BOM hỗ trợ Tiếng Việt)."""

    content_type = "text/csv; charset=utf-8"
    file_extension = "csv"

    def generate(self) -> bytes:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "Mã Giao Dịch",
                "Ngày Giao Dịch",
                "Danh Mục",
                "Thiết Yếu",
                "Ví Thanh Toán",
                "Số Tiền (VNĐ)",
                "Bất Thường (Anomaly)",
                "Ghi Chú",
            ]
        )
        for tx in self._transactions:
            writer.writerow(
                [
                    str(tx.get("id", "")),
                    str(tx.get("transaction_date", "")),
                    tx.get("category__name") or "Chưa phân loại",
                    "Có" if tx.get("category__is_essential", True) else "Không",
                    tx.get("wallet__name") or "",
                    float(tx.get("amount", 0)),
                    "BẤT THƯỜNG" if tx.get("is_anomaly") else "Bình thường",
                    tx.get("note", ""),
                ]
            )
        return buffer.getvalue().encode("utf-8-sig")


class ExcelReportExporter(BaseReportExporter):
    """Xuất báo cáo giao dịch chi tiêu ra định dạng Microsoft Excel (`.xlsx`) bằng `openpyxl`."""

    content_type = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    file_extension = "xlsx"

    def generate(self) -> bytes:
        wb = Workbook()
        ws = wb.active
        ws.title = "Chi Tieu Sinh Vien UIT"

        headers = [
            "Mã Giao Dịch",
            "Ngày Giao Dịch",
            "Danh Mục",
            "Thiết Yếu",
            "Ví Thanh Toán",
            "Số Tiền (VNĐ)",
            "Bất Thường (Anomaly)",
            "Ghi Chú",
        ]
        ws.append(headers)

        for tx in self._transactions:
            tx_date = tx.get("transaction_date")
            tx_date_str = (
                tx_date.strftime("%Y-%m-%d %H:%M")
                if hasattr(tx_date, "strftime")
                else str(tx_date or "")
            )
            ws.append(
                [
                    str(tx.get("id", "")),
                    tx_date_str,
                    tx.get("category__name") or "Chưa phân loại",
                    "Thiết yếu" if tx.get("category__is_essential", True) else "Giải trí",
                    tx.get("wallet__name") or "",
                    float(tx.get("amount", 0)),
                    "BẤT THƯỜNG" if tx.get("is_anomaly") else "Bình thường",
                    tx.get("note", ""),
                ]
            )

        output = io.BytesIO()
        wb.save(output)
        return output.getvalue()

