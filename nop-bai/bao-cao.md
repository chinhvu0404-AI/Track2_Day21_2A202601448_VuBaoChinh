# Báo Cáo Lab Day 21 - CI/CD cho AI Systems

| | |
|---|---|
| Họ và tên | Vũ Bảo Chinh |
| MSSV | 2A202601448 |
| Lớp / Khóa | 3B |
| Repo GitHub | https://github.com/chinhvu0404-AI/Track2_Day21_2A202601448_VuBaoChinh |
| Ngày nộp | 21/08/2026 |

---

## 1. Bộ Siêu Tham Số Đã Chọn và Lý Do

| Lần chạy | n_estimators | learning_rate | max_depth | f1_score | accuracy |
|---|---|---|---|---|---|
| 1 | 50 | 0.05 | 2 | 0.6051 | 0.8460 |
| 2 | 100 | 0.10 | 3 | 0.7109 | 0.8780 |
| 3 | 100 | 0.20 | 3 | 0.7290 | 0.8840 |

**Bộ siêu tham số đã chọn:** `n_estimators=100`, `learning_rate=0.2`, `max_depth=3`.

**Lý do:** Tôi quản lý năm lần chạy bằng MLflow và chọn cấu hình theo F1 của lớp thu nhập cao. Cấu hình cuối đạt F1 0,7290 và accuracy 0,8840, đều cao nhất trong thí nghiệm, nhưng quyết định vẫn dựa trên F1 vì dữ liệu mất cân bằng. Tăng từ 50 cây, learning rate 0,05 lên 100 cây với learning rate 0,10 hoặc 0,20 giúp nhận diện lớp dương tốt hơn. Ngược lại, tăng tiếp lên 200 cây không cải thiện F1, cho thấy thêm cây làm tăng chi phí mà không bảo đảm tổng quát hóa tốt hơn.

---

## 2. Vì Sao Ngưỡng Chất Lượng Đặt Trên F1 Chứ Không Phải Accuracy

Tập Adult chỉ có 24,8% mẫu thu nhập trên 50K. Mô hình luôn trả lời “thu nhập thấp” vẫn đạt accuracy khoảng 75,2% dù không phát hiện được lớp cần quan tâm, nên accuracy có thể gây hiểu nhầm. F1 của lớp dương kết hợp precision và recall, chỉ cao khi mô hình vừa hạn chế dự đoán dương sai, vừa tìm được đủ mẫu thu nhập cao. Vì vậy quality gate kiểm tra `f1_score >= 0.65`. Tôi tính F1 nhị phân cho nhãn dương, không dùng `average="weighted"` vì lớp đa số có thể che khuất thất bại, cũng không dùng `average="macro"` vì mục tiêu là đánh giá riêng lớp thu nhập cao.

---

## 3. Khó Khăn Gặp Phải và Cách Giải Quyết

| Khó khăn | Nguyên nhân | Cách giải quyết |
|---|---|---|
| VM không có size ban đầu | Azure thiếu capacity và policy giới hạn region | Dùng `Standard_B2als_v2` tại Korea Central. |
| VM cần đọc Blob riêng tư | Không nên lưu connection string trên server | Dùng Managed Identity với quyền `Storage Blob Data Reader`. |
| Thư viện trên VM xung đột | NumPy mới không tương thích scikit-learn | Pin NumPy 1.26.4 và kiểm tra lại service. |

---

## 4. So Sánh Bước 2 và Bước 3 (bắt buộc, 2 - 3 câu)

| | f1_score | accuracy |
|---|---|---|
| Bước 2 (chỉ `train_batch1`) | 0.7290 | 0.8840 |
| Bước 3 (thêm `train_batch2`) | 0.7330 | 0.8820 |

**Nhận xét:** Khi dữ liệu tăng từ 22.361 lên 44.722 mẫu, F1 tăng 0,0041 nhưng accuracy giảm 0,0020. Batch mới hỗ trợ lớp thu nhập cao ở mức nhỏ do có phân phối gần batch đầu; thêm dữ liệu không bảo đảm mọi chỉ số cùng tăng.
