# Comfee Dishwasher

Custom integration cho Home Assistant, kết nối máy rửa bát Comfee/Midea loại
thiết bị `0xE1` bằng giao thức local của `midea-local`.

- Cloud chỉ được dùng lúc cấu hình để lấy token/key LAN.
- Sau khi cấu hình, trạng thái và lệnh điều khiển đi thẳng qua mạng nội bộ,
  thường qua TCP `6444`.
- Một thread nền duy nhất nhận thông báo LAN và tự cập nhật entity; truy vấn
  khoảng 30 giây là dự phòng khi firmware không phát đủ thông báo.
- Callback được gộp trước khi báo Home Assistant, còn mọi I/O và teardown chạy
  ngoài event loop để tránh làm nặng hoặc treo Home Assistant.
- Mật khẩu tài khoản MSmartHome không được lưu trong config entry.
- Integration hiển thị các trường E1 mà máy trả về, gồm UV, sấy, van cấp nước,
  mã chẩn đoán và cảnh báo thao tác nếu firmware có hỗ trợ.
- Nút cập nhật trạng thái và kết nối lại chỉ đọc qua LAN, không gửi lệnh vận
  hành.
- Chỉ ba điều khiển ghi LAN đã được xác nhận an toàn: nguồn, khóa trẻ em và
  bảo quản/sấy khí.
- Chọn chương trình và nút khởi động bị tắt mặc định vì một số firmware E1 có
  thể bắt đầu chu trình ngay khi nhận lệnh chọn chương trình.

Hướng dẫn cài đặt và sử dụng nằm trong README ở thư mục gốc repository.

Không cấu hình cùng một máy đồng thời trong integration này và integration
Midea tích hợp sẵn của Home Assistant.
