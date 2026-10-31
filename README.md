# Phân tích hiệu quả chiến dịch marketing ngân hàng

Mã Python tổng hợp nội dung tính toán của tiểu luận Chương 1–5, dùng dữ liệu gốc do người dùng cung cấp. Toàn bộ xử lý nằm trong `bank_marketing.py`.

## Mở và chạy trong VS Code

1. Cài Python 3.10 trở lên và extension Python của Microsoft trong VS Code.
2. Giải nén, chọn **File > Open Folder**, mở thư mục `bank_marketing_project`.
3. Mở **Terminal > New Terminal**, chạy:

```bash
python -m venv .venv
```

Windows PowerShell (không cần kích hoạt môi trường):

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe bank_marketing.py
```

macOS/Linux:

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python bank_marketing.py
```

Trong VS Code có thể chọn **Python: Select Interpreter**, chọn `.venv` rồi dùng nút chạy file.
Mặc định chương trình đọc `data/bank-additional-full.csv` cạnh file code; không phụ thuộc thư mục đang mở terminal.
Có thể chỉ định dữ liệu khác bằng `--data` và thư mục đầu ra bằng `--output`.

## Đối chiếu với tiểu luận

| Chương | Hàm | Đầu ra |
|---|---|---|
| 1 | `chapter1` | Mục tiêu, phạm vi và công thức trong Markdown; chương lý thuyết không có phép tính thực nghiệm riêng |
| 2 | `chapter2` | Chất lượng, unknown, dòng trùng, miền giá trị, thống kê số, đối chiếu lịch sử, CSV 26 cột |
| 3 | `chapter3` | Tổng quan; tuổi; nghề; hôn nhân; học vấn; vay nhà; vay cá nhân; bảng CSV và biểu đồ PNG |
| 4 | `chapter4` | Tháng; thứ; số lần; kênh; lịch sử; kết quả trước; pdays hợp lệ; campaign/duration theo y; tương quan |
| 5 | `chapter5` | Bảng nhóm cần xem xét, tổng hợp số liệu tính lại và đề xuất trong Markdown |

Tất cả kết quả được tạo trong `outputs/`. CSV đầu ra dùng dấu phẩy và UTF-8 BOM. Dữ liệu gốc dùng dấu chấm phẩy.
Các biểu đồ được vẽ lại từ dữ liệu, không cam kết giống màu hoặc bố cục ảnh trong Word.
Phần kiến nghị là nội dung diễn giải theo tiểu luận, không phải mô hình tự động chứng minh hiệu quả.

## Quy tắc tái lập

Giữ 41.188 quan sát, bao gồm 12 dòng trùng dư theo cách giữ lần đầu; giữ nhãn unknown và ngoại lệ.
Tạo 5 biến: dang_ky, nhom_tuoi, nhom_so_lan_lien_he, co_lich_su, pdays_thuc_te.
Lịch sử xác định bằng previous > 0. Mã pdays=999 chỉ chuyển thành thiếu ở cột pdays_thuc_te.
Tỷ lệ và chênh lệch tính từ số chưa làm tròn; trình bày hai chữ số có thể khác khi trừ hai tỷ lệ đã làm tròn.
Thống kê chính: 41.188 dòng × 21 cột gốc; 4.640 yes; 36.548 no; tỷ lệ 11,265417%.
Không thêm Logistic Regression vì tiểu luận chỉ nêu là hướng mở rộng.
Duration chỉ dùng mô tả sau cuộc gọi, không dùng chọn khách hàng trước cuộc gọi.
Không suy luận nhân quả, không tính ROI, không suy ra nhóm kết hợp từ tỷ lệ đơn biến.

Đã chạy kiểm tra toàn bộ pipeline trên dữ liệu đính kèm. Thông tin phiên bản thư viện và SHA-256 tệp đầu vào nằm trong `outputs/thong_tin_lan_chay.json` sau khi chạy.

## Đưa lên GitHub

Tạo repository mới, chọn **Add file > Upload files**, đưa nội dung thư mục dự án lên và commit.
Hoặc dùng Source Control trong VS Code để khởi tạo repository và Publish to GitHub.
File `.gitignore` loại môi trường ảo và kết quả sinh ra; muốn chia sẻ một số kết quả thì thêm chúng có chủ đích.
Gói này chưa được đăng lên GitHub thay bạn.

## Nguồn theo tiểu luận

- Bank Marketing, UCI Machine Learning Repository: https://archive.ics.uci.edu/dataset/222/bank+marketing ; DOI: 10.24432/C5K306.
- Moro, S., Cortez, P., Rita, P. (2014). A Data-Driven Approach to Predict the Success of Bank Telemarketing. Decision Support Systems, 62, 22–31. DOI: 10.1016/j.dss.2014.03.001.
- Nội dung phương pháp và kiến nghị đối chiếu 5 tệp Word người dùng cung cấp.
