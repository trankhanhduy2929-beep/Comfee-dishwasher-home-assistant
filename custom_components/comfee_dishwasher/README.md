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
- Thêm sáu sensor tiêu thụ **ước tính**: điện/nước lần rửa gần nhất, tổng hôm
  nay và tổng tháng này. Tracker dùng bộ nhớ cục bộ của Home Assistant, không
  gọi cloud.

Các khóa sensor tương ứng là `estimated_energy_last_cycle`,
`estimated_water_last_cycle`, `estimated_energy_today`,
`estimated_water_today`, `estimated_energy_this_month` và
`estimated_water_this_month`.

Lưu ý: firmware E1 `760EY095` không cung cấp số kWh hoặc lít thực tế qua LAN.
Các sensor tiêu thụ cộng định mức tham khảo của profile E1 `7600024L` khi máy
chuyển sang `complete`; đây chưa phải thông số đã xác nhận riêng cho `760EY095`.
Chu kỳ bị hủy hoặc lỗi không được cộng. Đây là ước tính theo chương trình,
không phải số đo công tơ. Nếu chương trình chưa có định mức, sensor lần rửa
gần nhất sẽ là `Unknown` và tổng không thay đổi. Chu kỳ diễn ra hoàn toàn khi
Home Assistant tắt sẽ không thể được ghi nhận.

Hướng dẫn cài đặt và sử dụng nằm trong README ở thư mục gốc repository.

Không cấu hình cùng một máy đồng thời trong integration này và integration
Midea tích hợp sẵn của Home Assistant.
