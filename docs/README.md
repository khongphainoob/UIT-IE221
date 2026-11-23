# Kho Tài Liệu Thiết Kế & Sơ Đồ Kiến Trúc — Đồ Án IE221 (UIT)

Tài liệu đặc tả yêu cầu, sơ đồ thiết kế (Draw.io / PNG / PDF) và cẩm nang giải trình bảo vệ đồ án **Hệ thống Backend RESTful API Quản lý & Phân tích Dự báo Chi tiêu Sinh viên**.

---

## 1. Bộ Sơ Đồ Thiết Kế (`Draw.io` + `PDF Vector` + `PNG 2x`)

| Loại sơ đồ | File nguồn `.drawio` (Chỉnh sửa được) | Bản xuất PDF | Ảnh PNG độ phân giải cao (2x) |
| :--- | :--- | :--- | :--- |
| **Sơ đồ Lớp (Class Diagram — 4 trang UML 2.5)** | [`UIT-IE221_Class_Diagram_Final.drawio`](../UIT-IE221_Class_Diagram_Final.drawio) | [`UIT-IE221_Class_Diagram_Final.pdf`](diagrams/UIT-IE221_Class_Diagram_Final.pdf) *(4 trang)* | • [Trang 01 — Domain Models (7 Bảng 3NF)](diagrams/class_01_domain_models.png)<br>• [Trang 02 — Kiến trúc MVT Mở Rộng](diagrams/class_02_mvt_extended_layers.png)<br>• [Trang 03 — OOP & Design Patterns (ML & Export)](diagrams/class_03_oop_design_patterns.png)<br>• [Trang 04 — Vòng đời Request MVT & Service/Repo/Engine](diagrams/class_04_request_flow_mvt.png) |
| **Lược đồ Cơ sở Dữ liệu 3NF (Crow's Foot ERD)** | [`UIT-IE221_ERD_Database_3NF.drawio`](../UIT-IE221_ERD_Database_3NF.drawio) | [`UIT-IE221_ERD_Database_3NF.pdf`](diagrams/UIT-IE221_ERD_Database_3NF.pdf) *(1 trang)* | • [ERD PostgreSQL 16 — 7 Bảng Chuẩn 3NF](diagrams/erd_01_database_3nf.png) |
| **Phân rã Chức năng (FDD) & Use Case** | [`UIT-IE221_Functional_Decomposition_FDD.drawio`](../UIT-IE221_Functional_Decomposition_FDD.drawio) | [`UIT-IE221_Functional_Decomposition_FDD.pdf`](diagrams/UIT-IE221_Functional_Decomposition_FDD.pdf) *(2 trang)* | • [Trang 01 — FDD 5 Phân hệ / 22 Chức năng](diagrams/fdd_01_functional_decomposition.png)<br>• [Trang 02 — Use Case (Sinh viên UIT & Admin)](diagrams/fdd_02_use_case.png) |

---

## 2. Tài Liệu Giải Trình & Đặc Tả (`docs/*.md`)

| Tài liệu | Nội dung chính |
| :--- | :--- |
| **[`class_diagram_business_walkthrough.md`](class_diagram_business_walkthrough.md)** | Giải thích chi tiết từng trang sơ đồ Class (4 trang), ERD 7 bảng 3NF, FDD 22 chức năng, Use Case và câu hỏi phân biệt `View` / `Controller` vs `Service` / `Repository` / `Engine`. |
| **[`architecture_rationale_qa.md`](architecture_rationale_qa.md)** | Giải thích cấu trúc thư mục dự án, ánh xạ chuẩn Django MVT + Extended Layers, phân tích ưu/nhược điểm (trade-offs) và cẩm nang trả lời vấn đáp. |
| **[`functional_requirements_srs.md`](functional_requirements_srs.md)** | Đặc tả phạm vi đề tài, 2 tác nhân (`STUDENT`, `ADMIN`) và danh mục 5 phân hệ – 22 chức năng (`FR-01` → `FR-22`) cùng 3 bài toán ML/DL Serving. |
| **[`seed_data_guide.md`](seed_data_guide.md)** | Kết quả khảo sát bộ dữ liệu mẫu (Kaggle/GitHub), cấu trúc 180 giao dịch / 60 ngày và hướng dẫn chạy `manage.py seed_data` (`--reset`, idempotent). |
| **[`core_usage_guide.md`](core_usage_guide.md)** | Hướng dẫn sử dụng tầng nền tảng dùng chung `core/` (`BaseModel`, `BaseRepository<T>`, `APIResponse`, `exceptions.py`, `permissions.py`). |
| **[`uml_templates.md`](uml_templates.md)** | Mô tả văn bản chuẩn hóa UML & danh sách lớp tham chiếu cho StarUML / báo cáo Word. |
| **[`report_draft_ie221.md`](report_draft_ie221.md)** | Khung nội dung dự thảo báo cáo đồ án môn học IE221. |
| **[`demo_script_8_plus_8.md`](demo_script_8_plus_8.md)** | Kịch bản demo trực tiếp API, Dashboard và kịch bản kiểm thử 8+8. |
