# Comfee / Midea Local Appliances

Custom integration cho Home Assistant, kết nối thiết bị thuộc hệ sinh thái
Midea bằng giao thức LAN của `midea-local 10.1.0`.

- Giữ domain `comfee_dishwasher` để tương thích cấu hình Comfee E1 cũ.
- Hỗ trợ discovery cho 36 loại driver: điều hòa, quạt, lọc khí, hút ẩm, tạo
  ẩm, giặt/sấy, tủ lạnh, bình nóng lạnh, thiết bị bếp, robot hút bụi, máy lọc
  nước và hai loại máy rửa bát `0xE1`/`0x34`.
- Hỗ trợ lấy token/key qua MSmartHome/SmartHome, NetHome Plus, Midea Air/Arctic
  King, Ariston Clima và Midea Meiju.
- Cloud chỉ dùng trong config flow; tài khoản và mật khẩu không được lưu.
- Sau khi cấu hình, trạng thái và lệnh đã cho phép đi trực tiếp qua LAN.
- Một thread nền trên mỗi thiết bị nhận thông báo và truy vấn dự phòng. Callback
  được gộp trước khi cập nhật entity để tránh làm nặng Home Assistant.
- Thiết bị ngoài E1 dùng sensor/binary sensor generic. Thuộc tính chẩn đoán hiếm
  bị disable mặc định để giảm dữ liệu Recorder.
- Chỉ thuộc tính boolean trong allow-list của đúng driver mới được tạo switch;
  switch generic bị disable mặc định.
- Chưa có giao diện chuyên dụng `climate`, `fan`, `vacuum`, `light` hoặc
  `water_heater`; các loại đó hiện ưu tiên đọc trạng thái an toàn qua entity
  generic.

Máy rửa bát E1 giữ toàn bộ entity riêng, select/start an toàn và sáu sensor điện
nước **ước tính** cho lần rửa gần nhất, hôm nay và tháng này. Máy rửa bát `0x34`
không dùng chương trình hoặc định mức E1.

Firmware E1 `760EY095` không cung cấp số kWh/lít thực tế qua LAN. Tracker chỉ
cộng định mức tham khảo của profile `7600024L` khi máy báo hoàn tất; chu kỳ lỗi,
hủy hoặc chương trình chưa có định mức không được cộng.

Xem README ở thư mục gốc repository để biết bảng loại thiết bị, mức hỗ trợ,
cảnh báo điều khiển và hướng dẫn cài HACS.
