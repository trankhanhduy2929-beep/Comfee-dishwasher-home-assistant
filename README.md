<p align="center">
  <img src="custom_components/comfee_dishwasher/brand/logo.png" alt="Comfee" width="560">
</p>

# Comfee / Midea Local Appliances for Home Assistant

[![Validate](https://github.com/trankhanhduy2929-beep/Comfee-dishwasher-home-assistant/actions/workflows/validate.yml/badge.svg)](https://github.com/trankhanhduy2929-beep/Comfee-dishwasher-home-assistant/actions/workflows/validate.yml)
[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=trankhanhduy2929-beep&repository=Comfee-dishwasher-home-assistant&category=integration)

Custom integration không chính thức để kết nối thiết bị thuộc hệ sinh thái
Midea với Home Assistant qua mạng nội bộ. Bản `0.7.0` giữ nguyên domain
`comfee_dishwasher` để không làm mất cấu hình máy rửa bát Comfee hiện có, đồng
thời mở rộng discovery và đọc trạng thái cho toàn bộ 36 driver có sẵn trong
`midea-local >= 11.0.1`.

Tài khoản cloud chỉ được dùng trong bước cấu hình để lấy token/key LAN. Sau khi
thêm thiết bị, Home Assistant đọc trạng thái và gửi các lệnh đã cho phép trực
tiếp đến thiết bị qua LAN.

> [!IMPORTANT]
> Đây là dự án cộng đồng, không liên kết hoặc được Comfee, Midea hay các hãng
> tương thích chứng thực. Home Assistant hiện có integration `midea` chính
> thức dùng cùng thư viện `midea-local`. Không cấu hình cùng một thiết bị đồng
> thời trong integration này và integration `midea` chính thức (hay bất kỳ
> integration Midea nào khác), nếu không thiết bị sẽ cạnh tranh kết nối LAN.

## Cài đặt qua HACS

### Cài một chạm

Nhấn nút **Open in HACS** phía trên, chọn **Download**, sau đó restart Home
Assistant.

### Thêm repository thủ công

1. Mở **HACS → Integrations**.
2. Chọn menu góc trên bên phải → **Custom repositories**.
3. Nhập repository:
   `https://github.com/trankhanhduy2929-beep/Comfee-dishwasher-home-assistant`
4. Chọn loại **Integration**, rồi nhấn **Add**.
5. Mở repository **Comfee / Midea Local Appliances**, chọn **Download** và
   restart Home Assistant.
6. Vào **Settings → Devices & services → Add integration → Comfee / Midea
   Local Appliances**.

## Cách kết nối

### Tài khoản ứng dụng — khuyến nghị

Chọn đúng ứng dụng/cloud đã dùng để đăng ký thiết bị:

- **MSmartHome / SmartHome**
- **NetHome Plus**
- **Midea Air / Arctic King**
- **Ariston Clima**
- **OS Comfort**
- **Toshiba Iolife**
- **Midea Meiju / 美的美居** cho tài khoản Trung Quốc

Nhập tài khoản và mật khẩu của ứng dụng đó. Mật khẩu, tài khoản và tên cloud
không được lưu trong config entry; chỉ device ID, IP, model, loại thiết bị,
token/key LAN và metadata không nhạy cảm cần cho kết nối cục bộ được lưu.

Nếu có nhiều thiết bị tương thích trong tài khoản, config flow sẽ cho chọn một
thiết bị. Chạy lại quy trình để thêm thiết bị tiếp theo.

Khi ứng dụng/cloud từ chối, màn hình thêm thiết bị báo đúng nguyên nhân bằng
tiếng Việt thay vì báo lỗi chung:

| Thông báo | Nguyên nhân và cách xử lý |
| --- | --- |
| Không đăng nhập được tài khoản | Sai email/mật khẩu hoặc sai app đã dùng để đăng ký máy |
| Phiên đăng nhập cloud đã hết hạn | Đăng nhập lại app thiết bị rồi thử lại |
| Tài khoản bị khóa tạm thời | Đăng nhập sai nhiều lần, đợi vài phút rồi thử lại |
| Quá nhiều thiết bị đang đăng nhập | Đăng xuất bớt một số thiết bị |
| Ứng dụng/cloud không khớp | Chọn đúng app đã dùng để đăng ký máy rửa bát |
| Cloud từ chối yêu cầu | Mất Internet hoặc lỗi tạm thời, thử lại hoặc nhập LAN thủ công |
| Không có thiết bị LAN nào thuộc tài khoản | Máy đang được đăng ký bởi tài khoản khác |

### Thông tin LAN thủ công

Dùng khi đã có device ID, IP, protocol version, loại thiết bị, subtype, token và
key từ một phiên ứng dụng được ủy quyền hoặc từ cấu hình local đang hoạt động.
Chọn đúng mã loại `0x..`; integration từ chối loại không có driver thay vì thử
kết nối sai.

## Mức hỗ trợ

### Máy rửa bát Comfee/Midea `0xE1`

- Đã xác minh thực tế trên Comfee `760EY095`, protocol V3.
- Có entity riêng cho trạng thái, chương trình, tiến độ, cửa, cảnh báo, sấy,
  UV, cấp nước, nguồn, khóa trẻ em và bảo quản/sấy khí.
- Có select chương trình và nút start nhưng bị tắt mặc định để tránh máy tự chạy.
- Có điện/nước ước tính cho lần rửa gần nhất, hôm nay và tháng này.

### Máy rửa bát dạng bồn `0x34`

- Đọc các thuộc tính mà driver LAN trả về.
- Có switch nguồn, khóa trẻ em và bảo quản nếu model công bố các thuộc tính đó.
- Không dùng select/start hoặc định mức điện nước dành riêng cho E1.

### Các loại thiết bị còn lại

- Tạo sensor cho số, chuỗi, enum, danh sách hoặc dữ liệu chẩn đoán.
- Tạo binary sensor cho trạng thái boolean như cửa, đang chạy, cảnh báo và lỗi.
- Thuộc tính quan trọng được bật mặc định; thuộc tính hiếm/chẩn đoán bị tắt mặc
  định để giảm số state ghi vào Recorder và tránh làm nặng Home Assistant.
- Chỉ tạo switch cho thuộc tính nằm trong allow-list của đúng driver. Các
  switch generic bị tắt mặc định; chỉ bật sau khi đối chiếu tính năng trong app.
- Chưa tạo giao diện chuyên dụng kiểu `climate`, `fan`, `vacuum`, `light` hoặc
  `water_heater`. Các thiết bị này hiện dùng entity generic an toàn trước.

## Loại thiết bị

Catalog `0.7.0` có 36 loại driver LAN:

| Nhóm | Mã loại và thiết bị |
| --- | --- |
| Chiếu sáng | `0x13` đèn thông minh |
| Không khí và tiện nghi | `0x26` máy sưởi nhà tắm, `0x40` quạt trần tích hợp, `0xA1` máy hút ẩm, `0xAC` điều hòa, `0xAD` cảm biến không khí, `0xCC` bộ điều khiển điều hòa, `0xCE` cấp gió tươi, `0xCF` bơm nhiệt, `0xFA` quạt, `0xFB` máy sưởi, `0xFC` máy lọc không khí, `0xFD` máy tạo ẩm |
| Nhà bếp | `0x34` máy rửa bát dạng bồn, `0xB0` lò vi sóng, `0xB1` lò nướng, `0xB3` tủ khử khuẩn, `0xB4` máy nướng bánh mì, `0xB6` máy hút mùi, `0xBF` lò hấp/vi sóng, `0xE1` máy rửa bát, `0xE8` nồi nấu chậm, `0xEA` nồi cơm, `0xEC` nồi áp suất |
| Giặt sấy | `0xDA` máy giặt cửa trên, `0xDB` máy giặt cửa trước, `0xDC` máy sấy |
| Nước, nhiệt và phòng tắm | `0xC2` bồn cầu thông minh, `0xC3` bộ điều khiển bơm nhiệt, `0xCD` bình nóng lạnh bơm nhiệt, `0xE2` bình nóng lạnh điện, `0xE3` bình nóng lạnh gas, `0xE6` lò hơi gas, `0xED` máy lọc/làm mềm nước |
| Làm lạnh | `0xCA` tủ lạnh |
| Làm sạch | `0xB8` robot hút bụi |

Một driver tồn tại không có nghĩa mọi model của loại đó đều tương thích hoàn
toàn. Firmware có thể trả về ít hoặc nhiều thuộc tính khác nhau; integration
chỉ tạo entity cho dữ liệu model thực tế công bố.

## Hãng tương thích

Giao thức này xuất hiện trên thiết bị Midea và nhiều thương hiệu OEM. Integration
nhận diện tên hãng từ metadata dạng chữ, gồm Comfee, Midea, Toshiba, Carrier,
COLMO, Little Swan, Electrolux, Eureka, Rotenso, Ariston, Arctic King, Inventor,
Pro Breeze, MDV, Wahin, Netsu, Beverly, Bugu, Vandelo và một số nhãn khác.

Không suy đoán hãng chỉ từ manufacturer code vì mã có thể thay đổi theo vùng.
Nếu cloud trả về trường tên hãng hợp lệ, integration giữ tên OEM đó ngay cả khi
chưa có trong danh sách alias. Nếu metadata không đủ rõ, Home Assistant hiển thị
tên trung lập **Midea ecosystem**. Khả năng kết nối vẫn phụ thuộc loại driver,
firmware và app/cloud đã dùng để đăng ký thiết bị.

## Kiến trúc mạng

- Cloud chỉ được gọi lúc thêm integration để lấy token/key LAN.
- Mỗi thiết bị dùng một thread nền của `midea-local` để giữ kết nối TCP cục bộ,
  thường ở cổng `6444`.
- Thông báo LAN được đưa vào hàng đợi ngắn, gộp các thay đổi liên tiếp rồi cập
  nhật Home Assistant trên event loop. Cách này giữ cập nhật gần thời gian thực
  nhưng tránh tạo quá nhiều state/event.
- Truy vấn local định kỳ của driver được giữ làm dự phòng cho firmware không
  chủ động phát mọi thay đổi.
- Connect, refresh, reconnect, command và teardown đều chạy ngoài event loop.
- Home Assistant và thiết bị phải liên lạc được trong cùng LAN/VLAN. Client
  isolation hoặc firewall có thể chặn discovery và TCP local.
- Sau khi cấu hình, integration có thể hoạt động khi mất Internet nếu LAN và
  token/key của thiết bị không thay đổi.
- Nên đặt DHCP reservation. Khi setup lại, integration có thể dò lại IP theo
  device ID nếu địa chỉ đã đổi.

## Điện và nước máy rửa bát E1

Firmware Comfee E1 `760EY095` không trả về công tơ kWh/lít qua giao thức local.
Sáu sensor tiêu thụ của E1 vì vậy là **ước tính**, dùng định mức tham khảo theo
chương trình của profile `7600024L`, không phải số đo thực tế riêng của
`760EY095`:

- `eco_wash`: 0,99 kWh / 10,4 L
- `strong_wash`: 1,28 kWh / 13,9 L
- `hour_wash`: 0,91 kWh / 10,4 L
- `soak_wash`: 0,02 kWh / 3,4 L
- `self_clean`: 1,524 kWh / 10,3 L
- `germ`: 0,765 kWh / 9,9 L
- `fruit_wash`: 1,625 kWh / 13,3 L

Chương trình chưa có định mức hiển thị `Unknown` và không tăng tổng. Chu kỳ bị
hủy/lỗi không được cộng. Dữ liệu ngày/tháng được lưu cục bộ và reset theo múi
giờ Home Assistant. Nếu Home Assistant tắt trong toàn bộ chu kỳ thì chu kỳ đó
không thể được ghi nhận.

> [!CAUTION]
> Với protocol E1, chọn chương trình có thể khởi chạy máy ngay. Select chương
> trình và nút start vì vậy bị disable mặc định. Với thiết bị generic, chỉ bật
> switch sau khi xác nhận model có đúng tùy chọn tương ứng trong ứng dụng hãng.

## Việt hóa

Config flow, lỗi, tên entity E1 và tên thuộc tính generic đều có tiếng Việt.
Các khóa kỹ thuật như `entity_id`, device type `0x..`, model và tên thuộc tính
giao thức được giữ ổn định để automation không bị thay đổi.

## Chẩn đoán

Trang **Download diagnostics** của Home Assistant che device ID, IP, MAC,
serial, token và key trước khi xuất dữ liệu. Khi báo lỗi, nên gửi diagnostics
và ghi rõ hãng, model, app/cloud, mã loại thiết bị, phiên bản Home Assistant và
phiên bản integration.

## Cài thủ công

Tải asset `comfee_dishwasher.zip` từ trang **Releases**, tạo thư mục
`/config/custom_components/comfee_dishwasher/`, rồi giải nén trực tiếp các file
trong ZIP vào thư mục đó. Cấu trúc đúng là:

```text
/config/custom_components/comfee_dishwasher/manifest.json
```

Không để thành:

```text
/config/custom_components/comfee_dishwasher/comfee_dishwasher/manifest.json
```

Nếu từng gặp lỗi thư mục lồng sau khi update, xóa riêng thư mục
`comfee_dishwasher` nằm bên trong, cài lại bản ZIP mới rồi restart Home
Assistant.

## Build và kiểm tra

```bash
ruff check .
ruff format --check .
python3 -m compileall -q custom_components
python3 build_component.py
pytest -q
```

Builder tạo `dist/comfee_dishwasher.zip` có cấu trúc phẳng và file SHA-256
tương ứng. GitHub Actions chạy HACS validation và Hassfest cho mọi push/pull
request; tag dạng `v*` sẽ tạo GitHub Release.

Comfee, Midea và các tên hãng khác là nhãn hiệu của chủ sở hữu tương ứng. Logo
và biểu tượng Comfee trong repository chỉ dùng để nhận diện integration gốc.
