<p align="center">
  <img src="custom_components/comfee_dishwasher/brand/logo.png" alt="Comfee" width="560">
</p>

# Comfee Dishwasher for Home Assistant

[![Validate](https://github.com/trankhanhduy2929-beep/Comfee-dishwasher-home-assistant/actions/workflows/validate.yml/badge.svg)](https://github.com/trankhanhduy2929-beep/Comfee-dishwasher-home-assistant/actions/workflows/validate.yml)
[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=trankhanhduy2929-beep&repository=Comfee-dishwasher-home-assistant&category=integration)

Custom integration không chính thức để kết nối máy rửa bát Comfee/Midea loại
`0xE1` với Home Assistant. Integration dùng tài khoản MSmartHome **chỉ trong
bước cấu hình** để lấy token/key LAN; sau đó Home Assistant đọc trạng thái và
gửi lệnh trực tiếp đến máy qua mạng nội bộ.

> [!IMPORTANT]
> Đây là dự án cộng đồng, không liên kết hoặc được Comfee/Midea chứng thực.
> Không cấu hình cùng một máy đồng thời trong integration **Midea** chính thức
> và **Comfee Dishwasher**.

## Cài đặt qua HACS

### Cài một chạm

Nhấn nút **Open in HACS** phía trên, chọn **Download**, sau đó restart Home
Assistant.

HACS sẽ lấy bản ZIP từ GitHub Release. Nếu repository chưa xuất hiện trong HACS,
hãy thêm repository thủ công theo hướng dẫn dưới đây.

### Thêm repository thủ công

1. Mở **HACS → Integrations**.
2. Chọn menu góc trên bên phải → **Custom repositories**.
3. Nhập repository:
   `https://github.com/trankhanhduy2929-beep/Comfee-dishwasher-home-assistant`
4. Chọn loại **Integration**, rồi nhấn **Add**.
5. Mở repository **Comfee Dishwasher**, chọn **Download** và restart Home
   Assistant.
6. Vào **Settings → Devices & services → Add integration → Comfee Dishwasher**.

## Cách kết nối

### MSmartHome account — khuyến nghị

Nhập tài khoản đã liên kết với máy rửa bát. Password chỉ tồn tại trong phiên
config flow và **không được lưu**. Config entry chỉ lưu thông tin cần thiết để
xác thực LAN, gồm token/key cục bộ của thiết bị.

### Manual LAN credentials

Dùng khi bạn đã có device ID, IP, protocol version, token và key từ một phiên
MSmartHome được ủy quyền hoặc từ cấu hình local đang hoạt động.

## Kiến trúc mạng

- Cloud chỉ được gọi lúc thêm integration để lấy token/key LAN.
- Một thread nền duy nhất của `midea-local` giữ kết nối local TCP, thường là
  cổng `6444`, nhận phản hồi và thông báo trạng thái từ máy.
- Khi máy phát thông báo LAN, sensor/entity được cập nhật gần như ngay lập tức.
  Truy vấn local mỗi khoảng 30 giây vẫn được giữ làm dự phòng cho firmware
  không chủ động báo mọi thay đổi.
- Callback từ thread thiết bị chỉ đưa dữ liệu vào hàng đợi ngắn, gộp các thay
  đổi liên tiếp rồi cập nhật Home Assistant trên event loop. Mọi thao tác mạng
  hoặc dừng thread đều chạy trong executor để không block Home Assistant.
- Home Assistant và máy rửa bát phải ở cùng LAN/VLAN; client isolation hoặc
  firewall có thể chặn discovery.
- Sau khi cấu hình xong, integration vẫn có thể hoạt động khi mất Internet nếu
  mạng LAN và token/key của thiết bị không thay đổi.
- Nên đặt DHCP reservation. Nếu IP thay đổi, integration sẽ thử tìm lại thiết
  bị theo device ID trong lần setup kế tiếp.

## Entity

- Trạng thái, chương trình hiện tại, giai đoạn rửa, thời gian còn lại và nhiệt độ nước.
- Mức độ ẩm, mức chất trợ xả, mức làm mềm nước, thời gian bảo quản còn lại và mã chẩn đoán.
- Cửa, thiếu chất trợ xả, thiếu muối, thiếu nước, sấy, bảo quản/sấy khí, UV và van cấp nước.
- Cảnh báo lỗi/thao tác và trạng thái kết nối LAN để dùng trong automation.
- Switch nguồn, khóa trẻ em và bảo quản/sấy khí; đây là ba lệnh ghi LAN đã được thư viện xác nhận.
- Nút cập nhật trạng thái, kết nối lại LAN và nút khởi động chương trình hiện tại.
- Select chương trình vẫn tắt mặc định vì một số firmware E1 chạy ngay khi chọn.
- Điện và nước **ước tính** cho lần rửa hoàn tất gần nhất, tổng trong ngày và
  tổng trong tháng; dữ liệu được lưu cục bộ để không mất sau khi Home Assistant
  khởi động lại.

> [!NOTE]
> Firmware E1 của Comfee `760EY095` không trả về công tơ kWh/lít qua giao thức
> local. Các sensor tiêu thụ dùng định mức tham khảo theo chương trình của
> profile E1 `7600024L` (không phải thông số đã xác nhận riêng cho `760EY095`,
> và không phải số đo thực tế): `eco_wash` 0,99 kWh / 10,4 L, `strong_wash` 1,28 kWh /
> 13,9 L, `hour_wash` 0,91 kWh / 10,4 L, `soak_wash` 0,02 kWh / 3,4 L,
> `self_clean` 1,524 kWh / 10,3 L, `germ` 0,765 kWh / 9,9 L và `fruit_wash`
> 1,625 kWh / 13,3 L. Chương trình chưa có định mức sẽ hiện `Unknown` và không
> làm tăng tổng. Chu kỳ được tính theo thời điểm máy báo hoàn tất; nếu
> Home Assistant tắt suốt cả chu kỳ thì chu kỳ đó không thể được ghi nhận.

Các entity trạng thái E1 chỉ đọc được tạo theo dữ liệu mà máy thực tế trả về.
Vì vậy model E1 khác có thể có ít hoặc nhiều trạng thái hơn; sáu sensor tiêu
thụ ở trên là giá trị tính cục bộ từ trạng thái chu kỳ. Nút **Cập nhật trạng thái**
và
**Kết nối lại LAN** không gọi cloud và không gửi lệnh vận hành máy. Nút cập
nhật chỉ gửi một truy vấn đọc; thread nền vẫn là nơi duy nhất đọc socket.

> [!CAUTION]
> Với protocol E1, chọn một chương trình có thể khởi chạy chương trình đó ngay.
> Vì vậy select chương trình và nút start bị disable mặc định. Chỉ enable khi
> máy trống/an toàn, cửa đóng, máy đang bật và bạn chấp nhận máy có thể bắt đầu
> chạy. Integration không tự gửi lệnh tạm dừng/hủy vì `midea-local` chưa xác
> nhận định dạng LAN an toàn cho các lệnh đó.

## Việt hóa

Khi Home Assistant dùng ngôn ngữ tiếng Việt, tên entity và các trạng thái
chương trình được hiển thị bằng tiếng Việt. Các giá trị kỹ thuật như `entity_id`,
device type `0xE1`, model và khóa giao thức vẫn giữ nguyên để automation không
bị thay đổi.

## Chẩn đoán

Trang **Download diagnostics** của Home Assistant có thể dùng để gửi thông tin
debug. Integration tự che device ID, IP, MAC, serial, token và key trước khi
trả về diagnostics.

## Tương thích

- Device type: `0xE1`.
- Local protocol: V2/V3 do thư viện `midea-local` hỗ trợ.
- Đã xác minh trên Comfee model `760EY095`, protocol V3.
- Các model E1 khác có thể dùng được nhưng chưa được kiểm thử đầy đủ.

## Cài thủ công

Tải asset `comfee_dishwasher.zip` từ trang **Releases**, giải nén vào
`/config/custom_components/`, rồi restart Home Assistant. Cấu trúc sau khi giải
nén phải là:

```text
/config/custom_components/comfee_dishwasher/manifest.json
```

## Build và kiểm tra

```bash
python3 build_component.py
python3 -m unittest discover -s tests
```

Builder tạo `dist/comfee_dishwasher.zip` và file SHA-256 tương ứng. GitHub
Actions chạy HACS validation và Hassfest cho mọi push/pull request; tag dạng
`v*` sẽ tự build một GitHub Release.

## Báo lỗi

Khi mở issue, hãy ghi model máy, phiên bản Home Assistant, phiên bản integration
và log đã xóa account, password, token, key, device ID, MAC và serial number.

Comfee và Midea là nhãn hiệu của chủ sở hữu tương ứng; hình ảnh thương hiệu
trong repository chỉ dùng để nhận diện integration. Logo và biểu tượng Comfee
được lấy từ các tài nguyên thương hiệu công khai trên website chính thức
Comfee.
