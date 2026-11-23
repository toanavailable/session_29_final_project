# Mini Project - Hệ thống giám sát & quản lý thiết bị IoT Smart Factory

## Đề bài

### Mục tiêu

- Dùng Lớp trừu tượng (ABC) làm khung nguyên mẫu, đóng gói dữ liệu vận hành bằng biến private + `@property`, chặn thao túng từ bên ngoài.
- Xây dựng lớp lai (đa kế thừa) và vận dụng MRO để xử lý xung đột phương thức / thuộc tính trùng tên.
- Bỏ if-else thủ công bằng cách gọi đồng nhất một phương thức nhưng hành vi đổi theo từng loại đối tượng (đa hình).
- Nạp chồng toán tử `+` và `<` trên đối tượng tự tạo để kiểm kê, lượng hóa dữ liệu sản xuất.
- Thiết kế hàm toàn cục lỏng lẻo (Loosely Coupled) kết nối hàng trăm cổng dịch vụ bên thứ ba mà không sửa mã gốc (Duck Typing).
- Bẫy lỗi nâng cao bằng try-except kết hợp module `logging` thay cho lệnh in thô.

### Mô tả

Chương trình CLI "Rikkei Smart Factory IoT Simulator" quản lý, đo lường hiệu suất và điều phối 3 dòng thiết bị: **Robot sản xuất lắp ráp (Production Robot)**, **Cảm biến nhiệt độ phân xưởng (Thermal Sensor)** và dòng lai cao cấp **Thiết bị truyền động thông minh (Hybrid Smart Actuator)**. Yêu cầu chi tiết lấy theo tài liệu SRS: đặc tả lớp, 7 chức năng, logging, mô hình dữ liệu, 6 mã lỗi, 6 tình huống biên và quy ước UI.

Tài liệu đặc tả: [SRS - Hệ thống Giám sát và Quản lý thiết bị IoT Smart Factory](https://docs.google.com/document/d/1iX5MilYi6K3-vB08n8ANkOTyPWwJqBFZ/edit?tab=t.0)

### Thiết kế lớp bắt buộc

| Lớp | Yêu cầu |
|---|---|
| `BaseDevice` (ABC) | Class Attributes `factory_name = "Rikkei Smart Factory"`, `base_maintenance_cost = 1000000`; private `__operating_hours` (= 0), `@property operating_hours` **không setter**; `@abstractmethod track_performance()`, `run_diagnostic()`; `__add__` (cộng giờ chạy), `__lt__` (so sánh giờ chạy) |
| `ProductionRobot` | Thêm `completed_products`, định danh chuyển lên lớp cha bằng `super().__init__()`; OEE = `completed_products / (operating_hours * 50)`; cảnh báo bảo dưỡng cơ khí khi sản lượng > 10,000 |
| `ThermalSensor` | Thêm `current_temperature`, `safety_threshold` (VD 80.0 độ C); `track_performance()` trả biên độ nhiệt so với ngưỡng; vượt ngưỡng → cảnh báo nguy hiểm cấp 1 |
| `HybridSmartActuator` | Kế thừa `ProductionRobot` và `ThermalSensor`; MRO: `HybridSmartActuator → ProductionRobot → ThermalSensor → BaseDevice → object`; chạy logic tổng hợp: vừa đánh giá sản lượng, vừa quét nhiệt độ |
| Static & Class Method | `validate_device_code(device_code)`: đúng 10 ký tự, bắt đầu bằng tiền tố nhà máy (`IOT1234567`); `update_maintenance_cost(cls, new_cost)`: đổi chi phí bảo trì cho toàn hệ thống |

### Menu

```
===== RIKKEI SMART FACTORY IOT SIMULATOR =====
1. Đăng ký & Khởi tạo thiết bị IoT mới
2. Xem thông tin thiết bị & Thứ tự kế thừa (MRO)
3. Check-in giờ vận hành & Cập nhật chỉ số hiệu suất (Đa hình)
4. Thực thi quy trình tự chẩn đoán kỹ thuật (Diagnostic)
5. Cộng gộp thời gian tải & So sánh hao mòn (Overloading)
6. Xuất dữ liệu vận hành ra Cổng ngoại vi (Duck Typing)
7. Thoát chương trình
==================================================
Chọn chức năng (1-7):
```

- **Chức năng 1 - Đăng ký thiết bị:** Chọn loại (1: Robot, 2: Cảm biến, 3: Hybrid), nhập mã và tên; sai mã thì báo ERR-IOT-01 và nhập lại ngay bước đó; tên qua setter (xóa khoảng trắng thừa, IN HOA); Cảm biến / Hybrid nhập thêm nhiệt độ hiện tại và ngưỡng an toàn; thêm vào `devices_list`, gán `current_device`.
- **Chức năng 2 - Thông tin & MRO:** `current_device` là `None` thì ERR-IOT-02; có thì in thông số và chuỗi `__mro__`.
- **Chức năng 3 - Check-in (Đa hình):** Nhập giờ chạy mới + số liệu đặc thù (sản lượng / nhiệt độ) bằng vòng lặp while + try-except; gọi đồng nhất `track_performance()`: Robot → OEE, Cảm biến → biên độ nhiệt, Hybrid → cả hai.
- **Chức năng 4 - Tự chẩn đoán:** Gọi đa hình `run_diagnostic()`, đối chiếu ngưỡng (nhiệt độ, sản lượng, giờ chạy); an toàn thì báo `[Thành công]`, bất thường thì in từng hạng mục, trạng thái và chi phí bảo trì dự kiến theo `base_maintenance_cost`.
- **Chức năng 5 - Cộng gộp & So sánh:** In bảng thiết bị khác (căn lề f-string), nhập mã đối ứng; không tồn tại thì hủy thao tác; dùng `<` và `+`; sai kiểu → ERR-IOT-04.
- **Chức năng 6 - Xuất dữ liệu (Duck Typing):** Hàm toàn cục `export_telemetry_data(data_gateway, device_object)` chỉ gọi `process_stream()`; `MQTTEngineGateway`, `ERPReportGateway` dùng được; cổng không tương thích → ERR-IOT-05.
- **Chức năng 7 - Thoát:** "Cảm ơn bạn đã sử dụng hệ thống Quản lý Thiết bị Rikkei Smart Factory IoT Pro!"

## 1. Phân tích yêu cầu

### Danh mục mã lỗi

| Mã lỗi | Thông báo (sau tiền tố `[Lỗi] (Mã_Lỗi):`) | Nguyên nhân |
|---|---|---|
| ERR-IOT-01 | Mã thiết bị không hợp lệ! Phải gồm đúng 10 ký tự và bắt đầu bằng tiền tố quy định. | Sai độ dài / sai tiền tố khi đăng ký (chương trình dùng thêm cho mã bị trùng) |
| ERR-IOT-02 | Thao tác bị từ chối! Hệ thống chưa có thông tin thiết bị hoạt động. | Chọn chức năng 2-6 khi chưa có thiết bị (dùng thêm khi mã đối ứng không tồn tại) |
| ERR-IOT-03 | Định dạng dữ liệu sai! Giá trị nhập vào phải là số lớn hơn 0. | Nhập chữ hoặc số ≤ 0 vào giờ chạy, sản lượng, nhiệt độ |
| ERR-IOT-04 | Lỗi kiểu dữ liệu! Không thể thực hiện toán tử với đối tượng ngoài hệ thống. | `+` / `<` với đối tượng không kế thừa `BaseDevice` |
| ERR-IOT-05 | Xung đột kiến trúc! Không thể xuất dữ liệu do cấu hình cổng ngoại vi không tương thích. | Cổng không có `process_stream` |
| ERR-IOT-06 | Lựa chọn không hợp lệ! Vui lòng nhập đúng số thứ tự chức năng từ 1 đến 7. | Nhập chữ hoặc số ngoài [1, 7] ở menu chính (dùng thêm cho menu con) |

### Tình huống biên (Edge Cases)

| Vị trí | Tình huống | Cách xử lý |
|---|---|---|
| Menu chính | Nhập "xyz" hoặc số ngoài [1, 7] | `int()` trong try-except ValueError → ERR-IOT-06, quay lại menu |
| Chức năng 1 | Tên rỗng / toàn khoảng trắng | Kiểm tra `.strip()`, báo lỗi và bắt nhập lại tên |
| Chức năng 1 | Tạo trực tiếp `BaseDevice` | Python ném `TypeError`; `register_device` bắt `(TypeError, ValueError)` khi khởi tạo; unit test kiểm chứng |
| Chức năng 3 | Giờ chạy ≤ 0 hoặc sai kiểu | `input_positive()`: while + try-except, ERR-IOT-03; chỉ ghi vào đối tượng khi mọi giá trị đều hợp lệ (giữ nguyên giá trị cũ) |
| Chức năng 5 | Mã đối ứng không có trong `devices_list` | `find_device()` quét danh sách, trả `None` → báo lỗi, về menu |
| Chức năng 6 | Cổng không có `process_stream` | try-except AttributeError → ERR-IOT-05, chương trình không văng lỗi |

### Logging

Định dạng: `[yyyy-mm-dd HH:MM:SS] - [LEVEL] - [Thông điệp]`, ghi vào `smart_factory.log`.

| Cấp độ | Sử dụng tại |
|---|---|
| DEBUG | Dòng đầu của `add_operating_hours`, `track_performance`, `run_diagnostic`, `__add__`, `__lt__`, `export_telemetry_data`: ghi tham số đầu vào |
| INFO | Khởi động, khởi tạo thiết bị thành công, check-in, chẩn đoán an toàn, kết nối cổng MQTT / ERP thành công, thoát |
| WARNING | Từng hạng mục chẩn đoán bất thường (vượt ngưỡng nhiệt, sản lượng > 10,000, giờ chạy > 1,000) |
| ERROR | Mọi lỗi in ra console (ERR-IOT-01 → 06), giá trị nhập sai, chi tiết TypeError / AttributeError trong khối except |

## 2. Thiết kế giải pháp

| Lớp | Kế thừa | Thành phần chính | Vai trò |
|---|---|---|---|
| `BaseDevice` | `metaclass=ABCMeta` | `_id`, `_name` (protected), `__operating_hours`, `add_operating_hours()`, `diagnose()` (template method), `metric_prompts()`, `record_metrics()`, `detail_lines()`, `__add__`, `__lt__`, static / class method | Khung nguyên mẫu, đóng gói giờ chạy |
| `ProductionRobot` | `BaseDevice` | `completed_products`, `oee()`, `track_performance` (+OEE), `run_diagnostic` (> 10,000 sản phẩm) | Robot sản xuất |
| `ThermalSensor` | `BaseDevice` | `current_temperature`, `safety_threshold`, `track_performance` (+biên độ nhiệt), `run_diagnostic` (NGUY HIỂM CẤP 1) | Cảm biến nhiệt |
| `HybridSmartActuator` | `ProductionRobot`, `ThermalSensor` | chỉ `__init__`; mọi hành vi tổng hợp có sẵn nhờ chuỗi `super()` | Thiết bị lai |
| `MQTTEngineGateway`, `ERPReportGateway` | (không) | `process_stream(device)` | Cổng ngoại vi Duck Typing |
| `LegacyModbusGateway` | (không) | chỉ có `send_packet()` | Cổng lỗi để kiểm thử ERR-IOT-05 |

**Vì sao dùng `metaclass=ABCMeta` thay vì kế thừa `ABC`?**

Kế thừa `ABC` sẽ chèn thêm lớp `ABC` vào MRO (`... → BaseDevice → ABC → object`), lệch với đặc tả `... → BaseDevice → object`. Khai báo `class BaseDevice(metaclass=ABCMeta)` vẫn có đầy đủ cơ chế `@abstractmethod` (tạo trực tiếp vẫn báo `TypeError`) nhưng MRO đúng như yêu cầu.

**Hybrid chạy "logic tổng hợp" mà không viết lại phương thức thế nào?**

`track_performance`, `run_diagnostic`, `metric_prompts`, `record_metrics`, `detail_lines` đều viết kiểu **cooperative**: mỗi lớp xử lý phần của mình rồi gọi `super()`. Với Hybrid, `super()` trong `ProductionRobot` trỏ tới `ThermalSensor` (lớp kế tiếp trong MRO), rồi mới tới `BaseDevice`. Vì vậy một lời gọi `hybrid.track_performance()` trả về cả `oee_percent` lẫn `temperature_gap`; `run_diagnostic()` gom đủ cảnh báo sản lượng, nhiệt độ và giờ chạy. File log ghi lại đúng chuỗi DEBUG `ProductionRobot → ThermalSensor → BaseDevice`.

**Chức năng 3 loại bỏ if-else theo loại thiết bị ra sao?**

Mỗi lớp khai báo số liệu đặc thù của mình qua `metric_prompts()` (Robot: sản lượng, Cảm biến: nhiệt độ; Hybrid tự có cả hai theo MRO). Menu chỉ duyệt danh sách đó để hỏi người dùng, gọi `record_metrics(**metrics)` và `track_performance()`; không có `if isinstance(...)` nào cho từng loại.

**Đóng gói và chống thao túng dữ liệu?**

`__operating_hours` bị name mangling thành `_BaseDevice__operating_hours`; `operating_hours` là property chỉ đọc → gán trực tiếp báo `AttributeError`. Giờ chạy chỉ tăng qua `add_operating_hours()` có kiểm tra số dương. `_id`, `_name` là protected đúng mô hình dữ liệu SRS; tên luôn đi qua setter chuẩn hóa.

**Chi phí bảo trì được tính thế nào?**

`diagnose()` (template method ở lớp cha) gọi `run_diagnostic()` đa hình, xếp trạng thái (AN TOÀN / CẦN BẢO TRÌ / NGUY HIỂM CẤP 1) và tính chi phí = `base_maintenance_cost × số hạng mục bất thường`. Mỗi hạng mục được ghi log WARNING.

Thuật toán các phương thức chính:

```
ProductionRobot.track_performance():
    TRẢ VỀ {oee_percent: products / (hours * 50) * 100} + super().track_performance()

ThermalSensor.track_performance():
    TRẢ VỀ {temperature_gap: current_temperature - safety_threshold} + super().track_performance()

BaseDevice.run_diagnostic():                       # phần lõi (abstract có thân)
    NẾU operating_hours > 1000: TRẢ VỀ [(CẦN BẢO TRÌ, "Vượt định mức giờ vận hành")]

BaseDevice.diagnose():                             # template method
    issues ← run_diagnostic()                       # đa hình, Hybrid gom đủ 3 nguồn
    status ← NGUY HIỂM CẤP 1 nếu có, CẦN BẢO TRÌ nếu có hạng mục, ngược lại AN TOÀN
    cost   ← base_maintenance_cost * len(issues)

input_positive(prompt):
    LẶP: THỬ value ← số(input(prompt)); NẾU value > 0: TRẢ VỀ value
         BẮT ValueError → ERR-IOT-03, hỏi lại

export_telemetry_data(gateway, device):
    THỬ gateway.process_stream(device)              # Duck Typing
    BẮT AttributeError → ERR-IOT-05
```

## 3. Mã nguồn

File: [`smart_factory.py`](smart_factory.py) (sơ đồ lớp ở đầu file)

```python
"""
====================================================================
RIKKEI SMART FACTORY IOT SIMULATOR - THIẾT KẾ LỚP
====================================================================
                    BaseDevice (metaclass=ABCMeta)
     factory_name, base_maintenance_cost | _id, _name | __operating_hours
     @property operating_hours (KHÔNG setter) | add_operating_hours()
     @abstractmethod track_performance / run_diagnostic (có phần lõi)
     __add__ / __lt__ | @staticmethod validate_device_code
     @classmethod update_maintenance_cost
                 /                                 \\
       ProductionRobot                         ThermalSensor
     + completed_products                   + current_temperature, safety_threshold
     OEE = products / (hours * 50)          biên độ = nhiệt độ - ngưỡng
     cảnh báo khi products > 10,000         NGUY HIỂM CẤP 1 khi vượt ngưỡng
                 \\                                 /
           HybridSmartActuator(ProductionRobot, ThermalSensor)

MRO: HybridSmartActuator -> ProductionRobot -> ThermalSensor -> BaseDevice -> object
(dùng metaclass=ABCMeta thay vì kế thừa ABC để MRO đúng như đặc tả.)
track_performance / run_diagnostic / metric_prompts / record_metrics viết kiểu
cooperative (mỗi lớp làm phần của mình rồi gọi super()), nên Hybrid tự chạy
logic tổng hợp: vừa đánh giá sản lượng Robot, vừa quét nhiệt độ Cảm biến.
Cổng ngoại vi (Duck Typing): MQTTEngineGateway, ERPReportGateway có
process_stream(device); LegacyModbusGateway thì không (dùng để kiểm thử).
====================================================================
"""

import logging
import os
from abc import ABCMeta, abstractmethod

# ---------------------------------------------------------------------
# CẤU HÌNH LOGGING: [yyyy-mm-dd HH:MM:SS] - [LEVEL] - [Thông điệp]
# ---------------------------------------------------------------------
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "smart_factory.log")
logger = logging.getLogger("smart_factory")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    _handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    _handler.setFormatter(logging.Formatter("[%(asctime)s] - [%(levelname)s] - [%(message)s]",
                                            datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(_handler)

# ---------------------------------------------------------------------
# HẰNG SỐ & DANH MỤC MÃ LỖI
# ---------------------------------------------------------------------
CODE_PREFIX = "IOT"
CODE_LENGTH = 10
STANDARD_CAPACITY = 50            # công suất chuẩn: 50 sản phẩm / giờ
PRODUCT_MAINTENANCE_LIMIT = 10_000
MAX_OPERATING_HOURS = 1_000       # quá số giờ này cần đại tu
MENU_LINE = "=" * 50
STATUS_SAFE = "AN TOÀN"
STATUS_MAINTENANCE = "CẦN BẢO TRÌ"
STATUS_DANGER = "NGUY HIỂM CẤP 1"

ERRORS = {
    "ERR-IOT-01": "Mã thiết bị không hợp lệ! Phải gồm đúng 10 ký tự và bắt đầu bằng "
                  "tiền tố quy định.",
    "ERR-IOT-02": "Thao tác bị từ chối! Hệ thống chưa có thông tin thiết bị hoạt động.",
    "ERR-IOT-03": "Định dạng dữ liệu sai! Giá trị nhập vào phải là số lớn hơn 0.",
    "ERR-IOT-04": "Lỗi kiểu dữ liệu! Không thể thực hiện toán tử với đối tượng ngoài hệ thống.",
    "ERR-IOT-05": "Xung đột kiến trúc! Không thể xuất dữ liệu do cấu hình cổng ngoại vi "
                  "không tương thích.",
    "ERR-IOT-06": "Lựa chọn không hợp lệ! Vui lòng nhập đúng số thứ tự chức năng từ 1 đến 7.",
}


def error_text(code, detail=None):
    """'[Lỗi] (Mã_Lỗi): nội dung' - nội dung mặc định tra trong ERRORS."""
    return f"[Lỗi] ({code}): {detail or ERRORS[code]}"


def show_error(code, detail=None):
    """In lỗi ra console và ghi log ERROR."""
    message = error_text(code, detail)
    print(message)
    logger.error(message)


def num(value):
    """120.0 -> '120', 2.5 -> '2.5', 10500 -> '10,500'."""
    return f"{value:,.2f}".rstrip("0").rstrip(".")


def vnd(amount):
    """1000000 -> '1,000,000 VND'."""
    return f"{amount:,.0f} VND"


# =====================================================================
# LỚP TRỪU TƯỢNG
# =====================================================================
class BaseDevice(metaclass=ABCMeta):
    """Khung nguyên mẫu cho mọi thiết bị - không khởi tạo trực tiếp."""

    factory_name = "Rikkei Smart Factory"     # Class Attributes dùng chung
    base_maintenance_cost = 1_000_000         # VND / hạng mục bảo trì
    type_label = "Thiết bị IoT"

    def __init__(self, device_id, name, **kwargs):
        """Kiểm tra mã, chuẩn hóa tên qua setter, giờ vận hành ban đầu = 0."""
        super().__init__(**kwargs)            # cooperative theo MRO
        if not BaseDevice.validate_device_code(device_id):
            raise ValueError(ERRORS["ERR-IOT-01"])
        self._id = device_id                  # protected
        self._name = ""
        self.name = name                      # đi qua setter
        self.__operating_hours = 0            # private: _BaseDevice__operating_hours

    # ---------------- Properties ----------------
    @property
    def device_id(self):
        """Mã thiết bị (chỉ đọc)."""
        return self._id

    @property
    def name(self):
        """Tên thiết bị."""
        return self._name

    @name.setter
    def name(self, new_name):
        """Xóa khoảng trắng thừa, IN HOA; rỗng thì ValueError."""
        normalized = " ".join(str(new_name).split()).upper()
        if not normalized:
            raise ValueError("Tên thiết bị không được để trống!")
        self._name = normalized

    @property
    def operating_hours(self):
        """Giờ vận hành tích lũy - chỉ đọc, KHÔNG setter."""
        return self.__operating_hours

    @staticmethod
    def _check_positive(value):
        """Số liệu vận hành phải là số > 0 (ERR-IOT-03)."""
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
            raise ValueError(ERRORS["ERR-IOT-03"])

    def add_operating_hours(self, hours):
        """Check-in giờ chạy - cửa duy nhất thay đổi __operating_hours."""
        logger.debug(f"add_operating_hours(device={self._id}, hours={hours!r})")
        BaseDevice._check_positive(hours)
        self.__operating_hours += hours

    # ---------------- Abstract methods (có phần lõi) ----------------
    @abstractmethod
    def track_performance(self):
        """Phần lõi: dict chỉ số rỗng. Lớp con bổ sung chỉ số rồi gọi super()."""
        logger.debug(f"BaseDevice.track_performance(device={self._id}, "
                     f"hours={self.__operating_hours})")
        return {}

    @abstractmethod
    def run_diagnostic(self):
        """Phần lõi: kiểm tra số giờ chạy. Trả về list (mức độ, thông điệp)."""
        logger.debug(f"BaseDevice.run_diagnostic(device={self._id}, "
                     f"hours={self.__operating_hours})")
        if self.__operating_hours > MAX_OPERATING_HOURS:
            return [(STATUS_MAINTENANCE,
                     f"Cần đại tu: Vượt định mức giờ vận hành! ({num(self.__operating_hours)} "
                     f"giờ / tối đa {num(MAX_OPERATING_HOURS)} giờ)")]
        return []

    # ---------------- Cooperative helpers ----------------
    @classmethod
    def metric_prompts(cls):
        """Danh sách (khóa, câu nhắc, kiểu) số liệu đặc thù cần nhập khi check-in."""
        return []

    def record_metrics(self, **metrics):
        """Ghi số liệu đặc thù - lớp con lấy phần của mình rồi gọi super()."""

    def info_lines(self):
        """Thông tin chung + detail_lines() đa hình của lớp con."""
        return [f"Loại thiết bị: {self.device_type()}",
                f"Nhà máy: {BaseDevice.factory_name}",
                f"Mã thiết bị: {self._id}",
                f"Tên thiết bị: {self._name}",
                f"Số giờ vận hành: {num(self.operating_hours)} giờ"] + self.detail_lines()

    def detail_lines(self):
        """Dòng thông tin riêng - lớp con: dòng của mình + super() (đúng thứ tự MRO)."""
        return []

    def device_type(self):
        """Tên class của thiết bị."""
        return type(self).__name__

    def diagnose(self):
        """Template method: chạy run_diagnostic() đa hình, xếp trạng thái, tính chi phí."""
        issues = self.run_diagnostic()
        levels = [level for level, _ in issues]
        if STATUS_DANGER in levels:
            status = STATUS_DANGER
        elif levels:
            status = STATUS_MAINTENANCE
        else:
            status = STATUS_SAFE
        cost = BaseDevice.base_maintenance_cost * len(issues)
        for _, message in issues:
            logger.warning(f"{self._id}: {message}")
        return status, [message for _, message in issues], cost

    # ---------------- Operator Overloading ----------------
    def __add__(self, other):
        """A + B -> tổng giờ vận hành (số)."""
        logger.debug(f"__add__(self={self._id}, other={other!r})")
        if not isinstance(other, BaseDevice):
            return NotImplemented
        return self.operating_hours + other.operating_hours

    def __lt__(self, other):
        """A < B -> A có số giờ chạy ít hơn (ít hao mòn hơn)."""
        logger.debug(f"__lt__(self={self._id}, other={other!r})")
        if not isinstance(other, BaseDevice):
            return NotImplemented
        return self.operating_hours < other.operating_hours

    def __repr__(self):
        return f"{self.device_type()}({self._id})"

    # ---------------- Static / Class Method ----------------
    @staticmethod
    def validate_device_code(device_code):
        """Đúng 10 ký tự, bắt đầu bằng tiền tố 'IOT' (VD: IOT1234567)."""
        return (isinstance(device_code, str) and len(device_code) == CODE_LENGTH
                and device_code.startswith(CODE_PREFIX))

    @classmethod
    def update_maintenance_cost(cls, new_cost):
        """Đổi chi phí bảo trì cơ bản cho TOÀN BỘ thiết bị (gán vào BaseDevice)."""
        BaseDevice._check_positive(new_cost)
        BaseDevice.base_maintenance_cost = new_cost
        logger.info(f"Cập nhật chi phí bảo trì cơ bản toàn hệ thống: {vnd(new_cost)}")


# =====================================================================
# LỚP CON
# =====================================================================
class ProductionRobot(BaseDevice):
    """Robot sản xuất lắp ráp / Cobot."""

    type_label = "Robot sản xuất"

    def __init__(self, device_id, name, **kwargs):
        """Thêm completed_products = 0; định danh chuyển lên lớp cha qua super()."""
        super().__init__(device_id=device_id, name=name, **kwargs)
        self.completed_products = 0

    def oee(self):
        """OEE = completed_products / (operating_hours * 50); 0 giờ -> 0."""
        if self.operating_hours == 0:
            return 0.0
        return self.completed_products / (self.operating_hours * STANDARD_CAPACITY)

    def track_performance(self):
        """Bổ sung chỉ số OEE (%)."""
        logger.debug(f"ProductionRobot.track_performance(device={self._id}, "
                     f"products={self.completed_products}, hours={self.operating_hours})")
        return {"oee_percent": round(self.oee() * 100, 2), **super().track_performance()}

    def run_diagnostic(self):
        """Cảnh báo bảo dưỡng cơ khí khi sản lượng > 10,000."""
        logger.debug(f"ProductionRobot.run_diagnostic(device={self._id}, "
                     f"products={self.completed_products})")
        issues = []
        if self.completed_products > PRODUCT_MAINTENANCE_LIMIT:
            issues.append((STATUS_MAINTENANCE,
                           f"Cần bảo dưỡng cơ khí: Sản lượng vượt định mức! "
                           f"({num(self.completed_products)} sản phẩm / định mức "
                           f"{num(PRODUCT_MAINTENANCE_LIMIT)} sản phẩm)"))
        return issues + super().run_diagnostic()

    @classmethod
    def metric_prompts(cls):
        """Robot cần nhập sản lượng mới."""
        return [("completed_products", "Nhập số lượng sản phẩm hoàn thành mới bổ sung: ", int)
                ] + super().metric_prompts()

    def record_metrics(self, completed_products=None, **metrics):
        """Cộng dồn sản lượng."""
        if completed_products is not None:
            BaseDevice._check_positive(completed_products)
            self.completed_products += completed_products
        super().record_metrics(**metrics)

    def detail_lines(self):
        """Dòng sản lượng."""
        return [f"Sản phẩm hoàn thành: {num(self.completed_products)} sản phẩm"
                ] + super().detail_lines()


class ThermalSensor(BaseDevice):
    """Cảm biến nhiệt độ lò nung / phòng máy chủ."""

    type_label = "Cảm biến nhiệt độ"

    def __init__(self, device_id, name, current_temperature, safety_threshold=80.0,
                 **kwargs):
        """Thêm nhiệt độ hiện tại và ngưỡng an toàn (đều phải > 0)."""
        super().__init__(device_id=device_id, name=name, **kwargs)
        BaseDevice._check_positive(current_temperature)
        BaseDevice._check_positive(safety_threshold)
        self.current_temperature = float(current_temperature)
        self.safety_threshold = float(safety_threshold)

    def track_performance(self):
        """Bổ sung biên độ nhiệt = nhiệt độ hiện tại - ngưỡng an toàn."""
        logger.debug(f"ThermalSensor.track_performance(device={self._id}, "
                     f"temp={self.current_temperature}, threshold={self.safety_threshold})")
        gap = round(self.current_temperature - self.safety_threshold, 2)
        return {"temperature_gap": gap, **super().track_performance()}

    def run_diagnostic(self):
        """Vượt ngưỡng -> cưỡng bức chuyển sang NGUY HIỂM CẤP 1."""
        logger.debug(f"ThermalSensor.run_diagnostic(device={self._id}, "
                     f"temp={self.current_temperature}, threshold={self.safety_threshold})")
        issues = []
        if self.current_temperature > self.safety_threshold:
            issues.append((STATUS_DANGER,
                           f"Nguy hiểm: Vượt ngưỡng nhiệt! (Nhiệt độ hiện tại: "
                           f"{self.current_temperature:.1f} độ C / Ngưỡng an toàn: "
                           f"{self.safety_threshold:.1f} độ C)"))
        return issues + super().run_diagnostic()

    @classmethod
    def metric_prompts(cls):
        """Cảm biến cần nhập nhiệt độ mới."""
        return [("current_temperature", "Nhập nhiệt độ hiện tại ghi nhận (độ C): ", float)
                ] + super().metric_prompts()

    def record_metrics(self, current_temperature=None, **metrics):
        """Ghi nhiệt độ mới."""
        if current_temperature is not None:
            BaseDevice._check_positive(current_temperature)
            self.current_temperature = float(current_temperature)
        super().record_metrics(**metrics)

    def detail_lines(self):
        """Dòng nhiệt độ."""
        return [f"Nhiệt độ hiện tại: {self.current_temperature:.1f} độ C",
                f"Ngưỡng an toàn: {self.safety_threshold:.1f} độ C"] + super().detail_lines()


class HybridSmartActuator(ProductionRobot, ThermalSensor):
    """Thiết bị truyền động thông minh tích hợp cảm biến nhiệt (đa kế thừa)."""

    type_label = "Thiết bị truyền động lai"

    def __init__(self, device_id, name, current_temperature, safety_threshold=80.0):
        """Một lần super() khởi tạo Robot -> Sensor -> BaseDevice theo MRO."""
        super().__init__(device_id=device_id, name=name,
                         current_temperature=current_temperature,
                         safety_threshold=safety_threshold)

    # track_performance / run_diagnostic: KHÔNG override.
    # Chuỗi super(): ProductionRobot (OEE, sản lượng) -> ThermalSensor (nhiệt độ)
    # -> BaseDevice (giờ chạy) => logic tổng hợp tự động.


# =====================================================================
# CỔNG NGOẠI VI (DUCK TYPING) - không kế thừa lớp nào
# =====================================================================
class MQTTEngineGateway:
    """Đẩy dữ liệu lên Cloud qua MQTT."""

    def process_stream(self, device):
        """Đóng gói telemetry."""
        print("[Hệ thống MQTT Engine]: Đang khởi tạo băng thông kết nối dữ liệu IoT...")
        logger.info(f"Kết nối thành công cổng MQTT Engine cho thiết bị {device.device_id}")


class ERPReportGateway:
    """Đồng bộ số liệu vào phần mềm ERP."""

    def process_stream(self, device):
        """Đồng bộ số liệu tài sản."""
        print(f"[Hệ thống ERP]: Đang đồng bộ số liệu thiết bị {device.device_id} vào "
              "phân hệ quản trị tài sản...")
        logger.info(f"Kết nối thành công cổng ERP cho thiết bị {device.device_id}")


class LegacyModbusGateway:
    """Cổng đời cũ - KHÔNG có process_stream (dùng để kiểm thử ERR-IOT-05)."""

    def send_packet(self, payload):
        """Giao thức cũ."""
        return payload


def export_telemetry_data(data_gateway, device_object):
    """Hàm toàn cục: không kiểm tra kiểu, chỉ gọi process_stream()."""
    logger.debug(f"export_telemetry_data(gateway={type(data_gateway).__name__}, "
                 f"device={device_object!r})")
    try:
        data_gateway.process_stream(device_object)
    except AttributeError as error:
        show_error("ERR-IOT-05")
        logger.error(f"Chi tiết AttributeError: {error}")
        return False
    print("Xác thực cổng ngoại vi bằng Duck Typing thành công!")
    print(f"Dữ liệu của thiết bị {device_object.device_id} đã được đóng gói và xuất "
          "chuỗi luồng thành công.")
    return True


# =====================================================================
# HÀM GIAO DIỆN & NHẬP LIỆU
# =====================================================================
DEVICE_TYPES = {"1": ("Production Robot (Robot sản xuất lắp ráp)", ProductionRobot),
                "2": ("Thermal Sensor (Cảm biến nhiệt độ)", ThermalSensor),
                "3": ("Hybrid Smart Actuator (Thiết bị truyền động lai)",
                      HybridSmartActuator)}
PERFORMANCE_LABELS = {
    "oee_percent": lambda v: f"Chỉ số hiệu suất thiết bị tổng thể (OEE): {v:.1f}%",
    "temperature_gap": lambda v: (f"Biên độ nhiệt so với ngưỡng an toàn: {v:+.1f} độ C "
                                  f"({'VƯỢT NGƯỠNG' if v > 0 else 'trong ngưỡng'})"),
}


def input_positive(prompt, cast=float):
    """Vòng lặp while + try-except: chỉ thoát khi nhập số dương hợp lệ (ERR-IOT-03)."""
    while True:
        text = input(prompt).strip().replace(",", "")
        try:
            value = cast(text)
            BaseDevice._check_positive(value)
            return value
        except ValueError:
            show_error("ERR-IOT-03")
            logger.error(f"Giá trị nhập sai: {text!r} (prompt: {prompt.strip()})")


def find_device(devices_list, device_id):
    """Vòng quét tìm thiết bị theo mã; không thấy trả None."""
    for device in devices_list:
        if device.device_id == device_id:
            return device
    return None


def register_device(devices_list):
    """Chức năng 1: đăng ký thiết bị; sai ở bước nào nhập lại ngay bước đó."""
    print("--- ĐĂNG KÝ THIẾT BỊ IOT MỚI ---")
    for key, (label, _) in DEVICE_TYPES.items():
        print(f"{key}. {label}")
    while True:
        kind = input("Chọn phân loại thiết bị (1-3): ").strip()
        if kind in DEVICE_TYPES:
            break
        show_error("ERR-IOT-06", "Lựa chọn không hợp lệ! Vui lòng chọn phân loại thiết bị "
                                 "từ 1 đến 3.")
    device_class = DEVICE_TYPES[kind][1]
    while True:
        device_id = input("Nhập mã thiết bị 10 ký tự: ").strip()
        if not BaseDevice.validate_device_code(device_id):
            show_error("ERR-IOT-01")
        elif find_device(devices_list, device_id) is not None:
            show_error("ERR-IOT-01", f"Mã thiết bị {device_id} đã tồn tại trong hệ thống! "
                                     "Vui lòng nhập mã khác.")
        else:
            break
    while True:
        name = input("Nhập tên thiết bị: ")
        if name.strip():
            break
        print("[Lỗi]: Tên thiết bị không được để trống! Vui lòng nhập lại.")
        logger.error("Tên thiết bị rỗng hoặc chỉ chứa khoảng trắng")
    params = {}
    if issubclass(device_class, ThermalSensor):
        params["current_temperature"] = input_positive(
            "Nhập nhiệt độ hiện tại ghi nhận (độ C): ")
        params["safety_threshold"] = input_positive("Nhập ngưỡng nhiệt độ an toàn (độ C): ")
    try:
        device = device_class(device_id, name, **params)
    except (TypeError, ValueError) as error:
        print(f"[Lỗi]: Khởi tạo thất bại - {error}")
        logger.error(f"Khởi tạo thiết bị thất bại: {error}")
        return None
    devices_list.append(device)
    print(f"[Thành công]: Đăng ký {device.type_label} thành công!")
    print(f"Tên thiết bị: {device.name}")
    logger.info(f"Khởi tạo thành công {device.device_type()} {device.device_id} - "
                f"{device.name}")
    return device


def show_device_info(device):
    """Chức năng 2: thông tin (đa hình info_lines) + __mro__."""
    print("--- THÔNG TIN THIẾT BỊ HIỆN TẠI ---")
    print("\n".join(device.info_lines()))
    print("[Hệ thống MRO]: " + " -> ".join(cls.__name__ for cls in type(device).__mro__))


def check_in(device):
    """Chức năng 3: nhập giờ chạy + số liệu đặc thù, gọi track_performance() đa hình."""
    print("--- GHI NHẬN SỐ LIỆU VẬN HÀNH ---")
    hours = input_positive("Nhập số giờ chạy mới phát sinh: ")
    metrics = {key: input_positive(prompt, cast)
               for key, prompt, cast in device.metric_prompts()}
    device.add_operating_hours(hours)          # chỉ ghi khi mọi giá trị đều hợp lệ
    device.record_metrics(**metrics)
    print("[Thành công]: Đã cập nhật số liệu vận hành.")
    print(f"Tổng số giờ chạy tích lũy: {num(device.operating_hours)} giờ.")
    for key, value in device.track_performance().items():
        print(PERFORMANCE_LABELS[key](value))
    logger.info(f"Check-in {device.device_id}: +{num(hours)} giờ, số liệu {metrics}")


def run_device_diagnostic(device):
    """Chức năng 4: tự chẩn đoán (đa hình run_diagnostic)."""
    print("--- QUY TRÌNH TỰ CHẨN ĐOÁN LỖI KỸ THUẬT ---")
    status, messages, cost = device.diagnose()
    if not messages:
        print(f"[Thành công]: Thiết bị {device.device_id} đã hoàn thành quy trình tự chẩn "
              "đoán kỹ thuật. Trạng thái: An Toàn.")
        logger.info(f"Chẩn đoán {device.device_id}: An toàn")
        return
    print("[Cảnh báo hệ thống]: Thiết bị phát hiện trạng thái bất thường!")
    for message in messages:
        print(f"Kết quả chẩn đoán: {message}")
    print(f"Trạng thái thiết bị: {status}")
    print(f"Định mức chi phí bảo trì hệ thống dự kiến: {vnd(cost)}")


def compare_devices(device_a, device_b):
    """Gọi ngầm __lt__ và __add__; sai kiểu -> ERR-IOT-04."""
    try:
        is_less = device_a < device_b
        is_more = device_b < device_a
        total = device_a + device_b
    except TypeError as error:
        show_error("ERR-IOT-04")
        logger.error(f"Chi tiết TypeError: {error}")
        return None
    result = "ÍT HƠN" if is_less else ("NHIỀU HƠN" if is_more else "BẰNG")
    print(f"[Kết quả So sánh (__lt__)]: Hao mòn (số giờ chạy) của thiết bị A {result} "
          "thiết bị B.")
    print(f"[Kết quả Tổng hợp (__add__)]: Tổng thời gian tải vận hành của cả 2 thiết bị "
          f"là: {num(total)} giờ.")
    return total


def print_device_table(devices):
    """Bảng căn lề: chữ căn trái (<), số căn phải (>)."""
    header = f"{'Mã thiết bị':<12} | {'Tên thiết bị':<26} | {'Loại':<20} | {'Giờ chạy':>10}"
    print(header)
    print("-" * len(header))
    for item in devices:
        print(f"{item.device_id:<12} | {item.name:<26} | {item.device_type():<20} | "
              f"{num(item.operating_hours):>10}")


def load_comparison(devices_list, device):
    """Chức năng 5: chọn thiết bị đối ứng rồi so sánh / cộng gộp."""
    print("--- KIỂM KÊ & SO SÁNH TẢI (OPERATOR OVERLOADING) ---")
    others = [item for item in devices_list if item is not device]
    if not others:
        show_error("ERR-IOT-02", "Thao tác bị từ chối! Cần ít nhất 2 thiết bị trong hệ "
                                 "thống để so sánh.")
        return
    print(f"Thiết bị hiện tại (A): {device.device_id} (Số giờ chạy: "
          f"{num(device.operating_hours)} giờ)")
    print("Danh sách thiết bị đối ứng:")
    print_device_table(others)
    other = find_device(others, input("Chọn mã thiết bị đối ứng (B) từ danh sách: ").strip())
    if other is None:
        show_error("ERR-IOT-02", "Thao tác bị từ chối! Mã thiết bị đối ứng không tồn tại "
                                 "trong danh sách.")
        return
    print(f"Thiết bị đối ứng (B): {other.device_id} ({other.name} - Số giờ chạy: "
          f"{num(other.operating_hours)} giờ)")
    compare_devices(device, other)


def export_data(device):
    """Chức năng 6: chọn cổng rồi gọi hàm toàn cục export_telemetry_data()."""
    print("--- XUẤT DỮ LIỆU VẬN HÀNH RA CỔNG NGOẠI VI ---")
    print("1. Xuất dữ liệu qua cổng MQTT (Cloud Stream)")
    print("2. Đồng bộ số liệu vào hệ thống quản trị ERP")
    print("3. Cổng Modbus đời cũ (Legacy - kiểm thử tương thích)")
    gateways = {"1": MQTTEngineGateway, "2": ERPReportGateway, "3": LegacyModbusGateway}
    choice = input("Chọn cổng kết nối ngoại vi (1-3): ").strip()
    if choice not in gateways:
        show_error("ERR-IOT-06", "Lựa chọn không hợp lệ! Vui lòng chọn cổng kết nối từ "
                                 "1 đến 3.")
        return
    export_telemetry_data(gateways[choice](), device)


def display_menu():
    """In menu chính."""
    print("\n===== RIKKEI SMART FACTORY IOT SIMULATOR =====")
    print("1. Đăng ký & Khởi tạo thiết bị IoT mới")
    print("2. Xem thông tin thiết bị & Thứ tự kế thừa (MRO)")
    print("3. Check-in giờ vận hành & Cập nhật chỉ số hiệu suất (Đa hình)")
    print("4. Thực thi quy trình tự chẩn đoán kỹ thuật (Diagnostic)")
    print("5. Cộng gộp thời gian tải & So sánh hao mòn (Overloading)")
    print("6. Xuất dữ liệu vận hành ra Cổng ngoại vi (Duck Typing)")
    print("7. Thoát chương trình")
    print(MENU_LINE)


def main():
    """devices_list = [], current_device = None; vòng lặp while True."""
    devices_list = []
    current_device = None
    logger.info("Khởi động Rikkei Smart Factory IoT Simulator")
    while True:
        display_menu()
        text = input("Chọn chức năng (1-7): ").strip()
        try:
            choice = int(text)
        except ValueError:
            show_error("ERR-IOT-06")
            continue
        if not 1 <= choice <= 7:
            show_error("ERR-IOT-06")
            continue
        if 2 <= choice <= 6 and current_device is None:
            show_error("ERR-IOT-02")
            continue
        if choice == 1:
            current_device = register_device(devices_list) or current_device
        elif choice == 2:
            show_device_info(current_device)
        elif choice == 3:
            check_in(current_device)
        elif choice == 4:
            run_device_diagnostic(current_device)
        elif choice == 5:
            load_comparison(devices_list, current_device)
        elif choice == 6:
            export_data(current_device)
        else:
            print("Cảm ơn bạn đã sử dụng hệ thống Quản lý Thiết bị Rikkei Smart Factory "
                  "IoT Pro!")
            logger.info("Đóng chương trình an toàn")
            break


if __name__ == "__main__":
    main()
```

## 4. Kết quả chạy thử

Kịch bản: chức năng 2 khi chưa có thiết bị (ERR-IOT-02) → menu "xyz", "9" (ERR-IOT-06) → đăng ký Cảm biến (mã IOT99 sai, nhập lại; nhiệt độ "abc" sai) → check-in 250 giờ, nhiệt độ -5 (ERR-IOT-03) rồi 85 → chẩn đoán vượt ngưỡng → đăng ký Robot (mã trùng, tên rỗng) → check-in 40 giờ / 1,200 sản phẩm (OEE 60%), 1,100 giờ / 9,500 sản phẩm → chẩn đoán 2 hạng mục (2,000,000 VND) → đăng ký Hybrid ROBOTIC ARM ALPHA (loại 4 sai, mã sai) → check-in 0 giờ (lỗi), 100 giờ / 3,000 sản phẩm / 36 độ C → thông tin + MRO → chẩn đoán an toàn → check-in 20 giờ / 1,500 / 85 độ C (OEE 75%, +5 độ C) → chẩn đoán nguy hiểm → so sánh với mã không tồn tại, rồi với IOT0099999 → xuất MQTT, ERP, Legacy (ERR-IOT-05), cổng 4 → thoát. Khung menu lặp lại được ẩn.

```
Chọn chức năng (1-7): 2
[Lỗi] (ERR-IOT-02): Thao tác bị từ chối! Hệ thống chưa có thông tin thiết bị hoạt động.

Chọn chức năng (1-7): xyz
[Lỗi] (ERR-IOT-06): Lựa chọn không hợp lệ! Vui lòng nhập đúng số thứ tự chức năng từ 1 đến 7.

Chọn chức năng (1-7): 9
[Lỗi] (ERR-IOT-06): Lựa chọn không hợp lệ! Vui lòng nhập đúng số thứ tự chức năng từ 1 đến 7.

Chọn chức năng (1-7): 1
--- ĐĂNG KÝ THIẾT BỊ IOT MỚI ---
1. Production Robot (Robot sản xuất lắp ráp)
2. Thermal Sensor (Cảm biến nhiệt độ)
3. Hybrid Smart Actuator (Thiết bị truyền động lai)
Chọn phân loại thiết bị (1-3): 2
Nhập mã thiết bị 10 ký tự: IOT99
[Lỗi] (ERR-IOT-01): Mã thiết bị không hợp lệ! Phải gồm đúng 10 ký tự và bắt đầu bằng tiền tố quy định.
Nhập mã thiết bị 10 ký tự: IOT0099999
Nhập tên thiết bị:    cam bien nhiet lo nung  
Nhập nhiệt độ hiện tại ghi nhận (độ C): abc
[Lỗi] (ERR-IOT-03): Định dạng dữ liệu sai! Giá trị nhập vào phải là số lớn hơn 0.
Nhập nhiệt độ hiện tại ghi nhận (độ C): 92
Nhập ngưỡng nhiệt độ an toàn (độ C): 80
[Thành công]: Đăng ký Cảm biến nhiệt độ thành công!
Tên thiết bị: CAM BIEN NHIET LO NUNG

Chọn chức năng (1-7): 3
--- GHI NHẬN SỐ LIỆU VẬN HÀNH ---
Nhập số giờ chạy mới phát sinh: 250
Nhập nhiệt độ hiện tại ghi nhận (độ C): -5
[Lỗi] (ERR-IOT-03): Định dạng dữ liệu sai! Giá trị nhập vào phải là số lớn hơn 0.
Nhập nhiệt độ hiện tại ghi nhận (độ C): 85
[Thành công]: Đã cập nhật số liệu vận hành.
Tổng số giờ chạy tích lũy: 250 giờ.
Biên độ nhiệt so với ngưỡng an toàn: +5.0 độ C (VƯỢT NGƯỠNG)

Chọn chức năng (1-7): 4
--- QUY TRÌNH TỰ CHẨN ĐOÁN LỖI KỸ THUẬT ---
[Cảnh báo hệ thống]: Thiết bị phát hiện trạng thái bất thường!
Kết quả chẩn đoán: Nguy hiểm: Vượt ngưỡng nhiệt! (Nhiệt độ hiện tại: 85.0 độ C / Ngưỡng an toàn: 80.0 độ C)
Trạng thái thiết bị: NGUY HIỂM CẤP 1
Định mức chi phí bảo trì hệ thống dự kiến: 1,000,000 VND

Chọn chức năng (1-7): 1
--- ĐĂNG KÝ THIẾT BỊ IOT MỚI ---
1. Production Robot (Robot sản xuất lắp ráp)
2. Thermal Sensor (Cảm biến nhiệt độ)
3. Hybrid Smart Actuator (Thiết bị truyền động lai)
Chọn phân loại thiết bị (1-3): 1
Nhập mã thiết bị 10 ký tự: IOT0099999
[Lỗi] (ERR-IOT-01): Mã thiết bị IOT0099999 đã tồn tại trong hệ thống! Vui lòng nhập mã khác.
Nhập mã thiết bị 10 ký tự: IOT0055555
Nhập tên thiết bị:    
[Lỗi]: Tên thiết bị không được để trống! Vui lòng nhập lại.
Nhập tên thiết bị: robot han diem
[Thành công]: Đăng ký Robot sản xuất thành công!
Tên thiết bị: ROBOT HAN DIEM

Chọn chức năng (1-7): 3
--- GHI NHẬN SỐ LIỆU VẬN HÀNH ---
Nhập số giờ chạy mới phát sinh: 40
Nhập số lượng sản phẩm hoàn thành mới bổ sung: 1200
[Thành công]: Đã cập nhật số liệu vận hành.
Tổng số giờ chạy tích lũy: 40 giờ.
Chỉ số hiệu suất thiết bị tổng thể (OEE): 60.0%

Chọn chức năng (1-7): 3
--- GHI NHẬN SỐ LIỆU VẬN HÀNH ---
Nhập số giờ chạy mới phát sinh: 1100
Nhập số lượng sản phẩm hoàn thành mới bổ sung: 9500
[Thành công]: Đã cập nhật số liệu vận hành.
Tổng số giờ chạy tích lũy: 1,140 giờ.
Chỉ số hiệu suất thiết bị tổng thể (OEE): 18.8%

Chọn chức năng (1-7): 4
--- QUY TRÌNH TỰ CHẨN ĐOÁN LỖI KỸ THUẬT ---
[Cảnh báo hệ thống]: Thiết bị phát hiện trạng thái bất thường!
Kết quả chẩn đoán: Cần bảo dưỡng cơ khí: Sản lượng vượt định mức! (10,700 sản phẩm / định mức 10,000 sản phẩm)
Kết quả chẩn đoán: Cần đại tu: Vượt định mức giờ vận hành! (1,140 giờ / tối đa 1,000 giờ)
Trạng thái thiết bị: CẦN BẢO TRÌ
Định mức chi phí bảo trì hệ thống dự kiến: 2,000,000 VND

Chọn chức năng (1-7): 1
--- ĐĂNG KÝ THIẾT BỊ IOT MỚI ---
1. Production Robot (Robot sản xuất lắp ráp)
2. Thermal Sensor (Cảm biến nhiệt độ)
3. Hybrid Smart Actuator (Thiết bị truyền động lai)
Chọn phân loại thiết bị (1-3): 4
[Lỗi] (ERR-IOT-06): Lựa chọn không hợp lệ! Vui lòng chọn phân loại thiết bị từ 1 đến 3.
Chọn phân loại thiết bị (1-3): 3
Nhập mã thiết bị 10 ký tự: 5
[Lỗi] (ERR-IOT-01): Mã thiết bị không hợp lệ! Phải gồm đúng 10 ký tự và bắt đầu bằng tiền tố quy định.
Nhập mã thiết bị 10 ký tự: IOT0012345
Nhập tên thiết bị:   robotic arm alpha  
Nhập nhiệt độ hiện tại ghi nhận (độ C): 35.5
Nhập ngưỡng nhiệt độ an toàn (độ C): 80
[Thành công]: Đăng ký Thiết bị truyền động lai thành công!
Tên thiết bị: ROBOTIC ARM ALPHA

Chọn chức năng (1-7): 3
--- GHI NHẬN SỐ LIỆU VẬN HÀNH ---
Nhập số giờ chạy mới phát sinh: 0
[Lỗi] (ERR-IOT-03): Định dạng dữ liệu sai! Giá trị nhập vào phải là số lớn hơn 0.
Nhập số giờ chạy mới phát sinh: 100
Nhập số lượng sản phẩm hoàn thành mới bổ sung: abc
[Lỗi] (ERR-IOT-03): Định dạng dữ liệu sai! Giá trị nhập vào phải là số lớn hơn 0.
Nhập số lượng sản phẩm hoàn thành mới bổ sung: 3000
Nhập nhiệt độ hiện tại ghi nhận (độ C): 36
[Thành công]: Đã cập nhật số liệu vận hành.
Tổng số giờ chạy tích lũy: 100 giờ.
Chỉ số hiệu suất thiết bị tổng thể (OEE): 60.0%
Biên độ nhiệt so với ngưỡng an toàn: -44.0 độ C (trong ngưỡng)

Chọn chức năng (1-7): 2
--- THÔNG TIN THIẾT BỊ HIỆN TẠI ---
Loại thiết bị: HybridSmartActuator
Nhà máy: Rikkei Smart Factory
Mã thiết bị: IOT0012345
Tên thiết bị: ROBOTIC ARM ALPHA
Số giờ vận hành: 100 giờ
Sản phẩm hoàn thành: 3,000 sản phẩm
Nhiệt độ hiện tại: 36.0 độ C
Ngưỡng an toàn: 80.0 độ C
[Hệ thống MRO]: HybridSmartActuator -> ProductionRobot -> ThermalSensor -> BaseDevice -> object

Chọn chức năng (1-7): 4
--- QUY TRÌNH TỰ CHẨN ĐOÁN LỖI KỸ THUẬT ---
[Thành công]: Thiết bị IOT0012345 đã hoàn thành quy trình tự chẩn đoán kỹ thuật. Trạng thái: An Toàn.

Chọn chức năng (1-7): 3
--- GHI NHẬN SỐ LIỆU VẬN HÀNH ---
Nhập số giờ chạy mới phát sinh: 20
Nhập số lượng sản phẩm hoàn thành mới bổ sung: 1500
Nhập nhiệt độ hiện tại ghi nhận (độ C): 85
[Thành công]: Đã cập nhật số liệu vận hành.
Tổng số giờ chạy tích lũy: 120 giờ.
Chỉ số hiệu suất thiết bị tổng thể (OEE): 75.0%
Biên độ nhiệt so với ngưỡng an toàn: +5.0 độ C (VƯỢT NGƯỠNG)

Chọn chức năng (1-7): 4
--- QUY TRÌNH TỰ CHẨN ĐOÁN LỖI KỸ THUẬT ---
[Cảnh báo hệ thống]: Thiết bị phát hiện trạng thái bất thường!
Kết quả chẩn đoán: Nguy hiểm: Vượt ngưỡng nhiệt! (Nhiệt độ hiện tại: 85.0 độ C / Ngưỡng an toàn: 80.0 độ C)
Trạng thái thiết bị: NGUY HIỂM CẤP 1
Định mức chi phí bảo trì hệ thống dự kiến: 1,000,000 VND

Chọn chức năng (1-7): 5
--- KIỂM KÊ & SO SÁNH TẢI (OPERATOR OVERLOADING) ---
Thiết bị hiện tại (A): IOT0012345 (Số giờ chạy: 120 giờ)
Danh sách thiết bị đối ứng:
Mã thiết bị  | Tên thiết bị               | Loại                 |   Giờ chạy
-----------------------------------------------------------------------------
IOT0099999   | CAM BIEN NHIET LO NUNG     | ThermalSensor        |        250
IOT0055555   | ROBOT HAN DIEM             | ProductionRobot      |      1,140
Chọn mã thiết bị đối ứng (B) từ danh sách: IOT0000000
[Lỗi] (ERR-IOT-02): Thao tác bị từ chối! Mã thiết bị đối ứng không tồn tại trong danh sách.

Chọn chức năng (1-7): 5
--- KIỂM KÊ & SO SÁNH TẢI (OPERATOR OVERLOADING) ---
Thiết bị hiện tại (A): IOT0012345 (Số giờ chạy: 120 giờ)
Danh sách thiết bị đối ứng:
Mã thiết bị  | Tên thiết bị               | Loại                 |   Giờ chạy
-----------------------------------------------------------------------------
IOT0099999   | CAM BIEN NHIET LO NUNG     | ThermalSensor        |        250
IOT0055555   | ROBOT HAN DIEM             | ProductionRobot      |      1,140
Chọn mã thiết bị đối ứng (B) từ danh sách: IOT0099999
Thiết bị đối ứng (B): IOT0099999 (CAM BIEN NHIET LO NUNG - Số giờ chạy: 250 giờ)
[Kết quả So sánh (__lt__)]: Hao mòn (số giờ chạy) của thiết bị A ÍT HƠN thiết bị B.
[Kết quả Tổng hợp (__add__)]: Tổng thời gian tải vận hành của cả 2 thiết bị là: 370 giờ.

Chọn chức năng (1-7): 6
--- XUẤT DỮ LIỆU VẬN HÀNH RA CỔNG NGOẠI VI ---
1. Xuất dữ liệu qua cổng MQTT (Cloud Stream)
2. Đồng bộ số liệu vào hệ thống quản trị ERP
3. Cổng Modbus đời cũ (Legacy - kiểm thử tương thích)
Chọn cổng kết nối ngoại vi (1-3): 1
[Hệ thống MQTT Engine]: Đang khởi tạo băng thông kết nối dữ liệu IoT...
Xác thực cổng ngoại vi bằng Duck Typing thành công!
Dữ liệu của thiết bị IOT0012345 đã được đóng gói và xuất chuỗi luồng thành công.

Chọn chức năng (1-7): 6
--- XUẤT DỮ LIỆU VẬN HÀNH RA CỔNG NGOẠI VI ---
1. Xuất dữ liệu qua cổng MQTT (Cloud Stream)
2. Đồng bộ số liệu vào hệ thống quản trị ERP
3. Cổng Modbus đời cũ (Legacy - kiểm thử tương thích)
Chọn cổng kết nối ngoại vi (1-3): 2
[Hệ thống ERP]: Đang đồng bộ số liệu thiết bị IOT0012345 vào phân hệ quản trị tài sản...
Xác thực cổng ngoại vi bằng Duck Typing thành công!
Dữ liệu của thiết bị IOT0012345 đã được đóng gói và xuất chuỗi luồng thành công.

Chọn chức năng (1-7): 6
--- XUẤT DỮ LIỆU VẬN HÀNH RA CỔNG NGOẠI VI ---
1. Xuất dữ liệu qua cổng MQTT (Cloud Stream)
2. Đồng bộ số liệu vào hệ thống quản trị ERP
3. Cổng Modbus đời cũ (Legacy - kiểm thử tương thích)
Chọn cổng kết nối ngoại vi (1-3): 3
[Lỗi] (ERR-IOT-05): Xung đột kiến trúc! Không thể xuất dữ liệu do cấu hình cổng ngoại vi không tương thích.

Chọn chức năng (1-7): 6
--- XUẤT DỮ LIỆU VẬN HÀNH RA CỔNG NGOẠI VI ---
1. Xuất dữ liệu qua cổng MQTT (Cloud Stream)
2. Đồng bộ số liệu vào hệ thống quản trị ERP
3. Cổng Modbus đời cũ (Legacy - kiểm thử tương thích)
Chọn cổng kết nối ngoại vi (1-3): 4
[Lỗi] (ERR-IOT-06): Lựa chọn không hợp lệ! Vui lòng chọn cổng kết nối từ 1 đến 3.

Cảm ơn bạn đã sử dụng hệ thống Quản lý Thiết bị Rikkei Smart Factory IoT Pro!
```

### File log `smart_factory.log`

```
[2026-11-23 22:08:48] - [INFO] - [Khởi động Rikkei Smart Factory IoT Simulator]
[2026-11-23 22:08:48] - [ERROR] - [[Lỗi] (ERR-IOT-02): Thao tác bị từ chối! Hệ thống chưa có thông tin thiết bị hoạt động.]
[2026-11-23 22:08:48] - [ERROR] - [[Lỗi] (ERR-IOT-06): Lựa chọn không hợp lệ! Vui lòng nhập đúng số thứ tự chức năng từ 1 đến 7.]
[2026-11-23 22:08:48] - [ERROR] - [[Lỗi] (ERR-IOT-06): Lựa chọn không hợp lệ! Vui lòng nhập đúng số thứ tự chức năng từ 1 đến 7.]
[2026-11-23 22:08:48] - [ERROR] - [[Lỗi] (ERR-IOT-01): Mã thiết bị không hợp lệ! Phải gồm đúng 10 ký tự và bắt đầu bằng tiền tố quy định.]
[2026-11-23 22:08:48] - [ERROR] - [[Lỗi] (ERR-IOT-03): Định dạng dữ liệu sai! Giá trị nhập vào phải là số lớn hơn 0.]
[2026-11-23 22:08:48] - [ERROR] - [Giá trị nhập sai: 'abc' (prompt: Nhập nhiệt độ hiện tại ghi nhận (độ C):)]
[2026-11-23 22:08:48] - [INFO] - [Khởi tạo thành công ThermalSensor IOT0099999 - CAM BIEN NHIET LO NUNG]
[2026-11-23 22:08:48] - [ERROR] - [[Lỗi] (ERR-IOT-03): Định dạng dữ liệu sai! Giá trị nhập vào phải là số lớn hơn 0.]
[2026-11-23 22:08:48] - [ERROR] - [Giá trị nhập sai: '-5' (prompt: Nhập nhiệt độ hiện tại ghi nhận (độ C):)]
[2026-11-23 22:08:48] - [DEBUG] - [add_operating_hours(device=IOT0099999, hours=250.0)]
[2026-11-23 22:08:48] - [DEBUG] - [ThermalSensor.track_performance(device=IOT0099999, temp=85.0, threshold=80.0)]
[2026-11-23 22:08:48] - [DEBUG] - [BaseDevice.track_performance(device=IOT0099999, hours=250.0)]
[2026-11-23 22:08:48] - [INFO] - [Check-in IOT0099999: +250 giờ, số liệu {'current_temperature': 85.0}]
[2026-11-23 22:08:48] - [DEBUG] - [ThermalSensor.run_diagnostic(device=IOT0099999, temp=85.0, threshold=80.0)]
[2026-11-23 22:08:48] - [DEBUG] - [BaseDevice.run_diagnostic(device=IOT0099999, hours=250.0)]
[2026-11-23 22:08:48] - [WARNING] - [IOT0099999: Nguy hiểm: Vượt ngưỡng nhiệt! (Nhiệt độ hiện tại: 85.0 độ C / Ngưỡng an toàn: 80.0 độ C)]
[2026-11-23 22:08:48] - [ERROR] - [[Lỗi] (ERR-IOT-01): Mã thiết bị IOT0099999 đã tồn tại trong hệ thống! Vui lòng nhập mã khác.]
[2026-11-23 22:08:48] - [ERROR] - [Tên thiết bị rỗng hoặc chỉ chứa khoảng trắng]
[2026-11-23 22:08:48] - [INFO] - [Khởi tạo thành công ProductionRobot IOT0055555 - ROBOT HAN DIEM]
[2026-11-23 22:08:48] - [DEBUG] - [add_operating_hours(device=IOT0055555, hours=40.0)]
[2026-11-23 22:08:48] - [DEBUG] - [ProductionRobot.track_performance(device=IOT0055555, products=1200, hours=40.0)]
[2026-11-23 22:08:48] - [DEBUG] - [BaseDevice.track_performance(device=IOT0055555, hours=40.0)]
[2026-11-23 22:08:48] - [INFO] - [Check-in IOT0055555: +40 giờ, số liệu {'completed_products': 1200}]
[2026-11-23 22:08:48] - [DEBUG] - [add_operating_hours(device=IOT0055555, hours=1100.0)]
[2026-11-23 22:08:48] - [DEBUG] - [ProductionRobot.track_performance(device=IOT0055555, products=10700, hours=1140.0)]
[2026-11-23 22:08:48] - [DEBUG] - [BaseDevice.track_performance(device=IOT0055555, hours=1140.0)]
[2026-11-23 22:08:48] - [INFO] - [Check-in IOT0055555: +1,100 giờ, số liệu {'completed_products': 9500}]
[2026-11-23 22:08:48] - [DEBUG] - [ProductionRobot.run_diagnostic(device=IOT0055555, products=10700)]
[2026-11-23 22:08:48] - [DEBUG] - [BaseDevice.run_diagnostic(device=IOT0055555, hours=1140.0)]
[2026-11-23 22:08:48] - [WARNING] - [IOT0055555: Cần bảo dưỡng cơ khí: Sản lượng vượt định mức! (10,700 sản phẩm / định mức 10,000 sản phẩm)]
[2026-11-23 22:08:48] - [WARNING] - [IOT0055555: Cần đại tu: Vượt định mức giờ vận hành! (1,140 giờ / tối đa 1,000 giờ)]
[2026-11-23 22:08:48] - [ERROR] - [[Lỗi] (ERR-IOT-06): Lựa chọn không hợp lệ! Vui lòng chọn phân loại thiết bị từ 1 đến 3.]
[2026-11-23 22:08:48] - [ERROR] - [[Lỗi] (ERR-IOT-01): Mã thiết bị không hợp lệ! Phải gồm đúng 10 ký tự và bắt đầu bằng tiền tố quy định.]
[2026-11-23 22:08:48] - [INFO] - [Khởi tạo thành công HybridSmartActuator IOT0012345 - ROBOTIC ARM ALPHA]
[2026-11-23 22:08:48] - [ERROR] - [[Lỗi] (ERR-IOT-03): Định dạng dữ liệu sai! Giá trị nhập vào phải là số lớn hơn 0.]
[2026-11-23 22:08:48] - [ERROR] - [Giá trị nhập sai: '0' (prompt: Nhập số giờ chạy mới phát sinh:)]
[2026-11-23 22:08:48] - [ERROR] - [[Lỗi] (ERR-IOT-03): Định dạng dữ liệu sai! Giá trị nhập vào phải là số lớn hơn 0.]
[2026-11-23 22:08:48] - [ERROR] - [Giá trị nhập sai: 'abc' (prompt: Nhập số lượng sản phẩm hoàn thành mới bổ sung:)]
[2026-11-23 22:08:48] - [DEBUG] - [add_operating_hours(device=IOT0012345, hours=100.0)]
[2026-11-23 22:08:48] - [DEBUG] - [ProductionRobot.track_performance(device=IOT0012345, products=3000, hours=100.0)]
[2026-11-23 22:08:48] - [DEBUG] - [ThermalSensor.track_performance(device=IOT0012345, temp=36.0, threshold=80.0)]
[2026-11-23 22:08:48] - [DEBUG] - [BaseDevice.track_performance(device=IOT0012345, hours=100.0)]
[2026-11-23 22:08:48] - [INFO] - [Check-in IOT0012345: +100 giờ, số liệu {'completed_products': 3000, 'current_temperature': 36.0}]
[2026-11-23 22:08:48] - [DEBUG] - [ProductionRobot.run_diagnostic(device=IOT0012345, products=3000)]
[2026-11-23 22:08:48] - [DEBUG] - [ThermalSensor.run_diagnostic(device=IOT0012345, temp=36.0, threshold=80.0)]
[2026-11-23 22:08:48] - [DEBUG] - [BaseDevice.run_diagnostic(device=IOT0012345, hours=100.0)]
[2026-11-23 22:08:48] - [INFO] - [Chẩn đoán IOT0012345: An toàn]
[2026-11-23 22:08:48] - [DEBUG] - [add_operating_hours(device=IOT0012345, hours=20.0)]
[2026-11-23 22:08:48] - [DEBUG] - [ProductionRobot.track_performance(device=IOT0012345, products=4500, hours=120.0)]
[2026-11-23 22:08:48] - [DEBUG] - [ThermalSensor.track_performance(device=IOT0012345, temp=85.0, threshold=80.0)]
[2026-11-23 22:08:48] - [DEBUG] - [BaseDevice.track_performance(device=IOT0012345, hours=120.0)]
[2026-11-23 22:08:48] - [INFO] - [Check-in IOT0012345: +20 giờ, số liệu {'completed_products': 1500, 'current_temperature': 85.0}]
[2026-11-23 22:08:48] - [DEBUG] - [ProductionRobot.run_diagnostic(device=IOT0012345, products=4500)]
[2026-11-23 22:08:48] - [DEBUG] - [ThermalSensor.run_diagnostic(device=IOT0012345, temp=85.0, threshold=80.0)]
[2026-11-23 22:08:48] - [DEBUG] - [BaseDevice.run_diagnostic(device=IOT0012345, hours=120.0)]
[2026-11-23 22:08:48] - [WARNING] - [IOT0012345: Nguy hiểm: Vượt ngưỡng nhiệt! (Nhiệt độ hiện tại: 85.0 độ C / Ngưỡng an toàn: 80.0 độ C)]
[2026-11-23 22:08:48] - [ERROR] - [[Lỗi] (ERR-IOT-02): Thao tác bị từ chối! Mã thiết bị đối ứng không tồn tại trong danh sách.]
[2026-11-23 22:08:48] - [DEBUG] - [__lt__(self=IOT0012345, other=ThermalSensor(IOT0099999))]
[2026-11-23 22:08:48] - [DEBUG] - [__lt__(self=IOT0099999, other=HybridSmartActuator(IOT0012345))]
[2026-11-23 22:08:48] - [DEBUG] - [__add__(self=IOT0012345, other=ThermalSensor(IOT0099999))]
[2026-11-23 22:08:48] - [DEBUG] - [export_telemetry_data(gateway=MQTTEngineGateway, device=HybridSmartActuator(IOT0012345))]
[2026-11-23 22:08:48] - [INFO] - [Kết nối thành công cổng MQTT Engine cho thiết bị IOT0012345]
[2026-11-23 22:08:48] - [DEBUG] - [export_telemetry_data(gateway=ERPReportGateway, device=HybridSmartActuator(IOT0012345))]
[2026-11-23 22:08:48] - [INFO] - [Kết nối thành công cổng ERP cho thiết bị IOT0012345]
[2026-11-23 22:08:48] - [DEBUG] - [export_telemetry_data(gateway=LegacyModbusGateway, device=HybridSmartActuator(IOT0012345))]
[2026-11-23 22:08:48] - [ERROR] - [[Lỗi] (ERR-IOT-05): Xung đột kiến trúc! Không thể xuất dữ liệu do cấu hình cổng ngoại vi không tương thích.]
[2026-11-23 22:08:48] - [ERROR] - [Chi tiết AttributeError: 'LegacyModbusGateway' object has no attribute 'process_stream']
[2026-11-23 22:08:48] - [ERROR] - [[Lỗi] (ERR-IOT-06): Lựa chọn không hợp lệ! Vui lòng chọn cổng kết nối từ 1 đến 3.]
[2026-11-23 22:08:48] - [INFO] - [Đóng chương trình an toàn]
```

### Bảng kiểm thử chức năng

| Kịch bản | Dữ liệu | Kết quả |
|---|---|---|
| Menu sai | "xyz", 9 | ERR-IOT-06, quay lại menu |
| Chưa có thiết bị | Chọn 2 | ERR-IOT-02 |
| Mã sai / trùng | IOT99, 5, IOT0099999 (đã có) | ERR-IOT-01, nhập lại ngay bước đó |
| Tên rỗng | "   " | Báo lỗi, nhập lại tên |
| Chuẩn hóa tên | "  robotic arm alpha  " | ROBOTIC ARM ALPHA |
| Số liệu sai | "abc", -5, 0 | ERR-IOT-03, hỏi lại, giữ giá trị cũ |
| OEE Robot | 40 giờ, 1,200 sản phẩm | 60.0% |
| Chẩn đoán Robot | 1,140 giờ, 10,700 sản phẩm | 2 hạng mục, CẦN BẢO TRÌ, 2,000,000 VND |
| Hybrid tổng hợp | 120 giờ, 4,500 sản phẩm, 85 độ C | OEE 75.0% + biên độ +5.0 độ C |
| Chẩn đoán Hybrid | 36 độ C / 85 độ C | An Toàn / NGUY HIỂM CẤP 1, 1,000,000 VND |
| MRO | Chức năng 2 | HybridSmartActuator → ProductionRobot → ThermalSensor → BaseDevice → object |
| Mã đối ứng không tồn tại | IOT0000000 | Hủy thao tác, về menu |
| So sánh / cộng gộp | 120 vs 250 giờ | A ÍT HƠN B; tổng 370 giờ |
| Duck Typing | MQTT / ERP / Legacy | Thành công / thành công / ERR-IOT-05 |
| Khởi tạo BaseDevice, toán tử sai kiểu | Unit test | TypeError; ERR-IOT-04 |

## 5. Unit Test

File: [`test_smart_factory.py`](test_smart_factory.py) - 20 ca kiểm thử cho lớp trừu tượng, đóng gói, static / class method, đa hình, MRO, toán tử và Duck Typing.

```python
"""Unit test cho Rikkei Smart Factory IoT Simulator.

Chạy: python -m unittest test_smart_factory -v   (hoặc: pytest test_smart_factory.py)
"""

import io
import unittest
from contextlib import redirect_stdout

from smart_factory import (BaseDevice, ProductionRobot, ThermalSensor, HybridSmartActuator,
                           MQTTEngineGateway, ERPReportGateway, LegacyModbusGateway,
                           export_telemetry_data, compare_devices, STATUS_DANGER,
                           STATUS_MAINTENANCE, STATUS_SAFE)


def run_quietly(func, *args):
    """Chạy hàm, trả về (kết quả, chuỗi đã in)."""
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        result = func(*args)
    return result, buffer.getvalue()


class TestAbstractAndEncapsulation(unittest.TestCase):
    """Lớp trừu tượng, đóng gói, setter."""

    def test_cannot_instantiate_base_device(self):
        """Edge case: tạo trực tiếp BaseDevice -> TypeError."""
        with self.assertRaises(TypeError):
            BaseDevice("IOT0000001", "x")

    def test_operating_hours_has_no_setter(self):
        """Gán trực tiếp operating_hours -> AttributeError."""
        robot = ProductionRobot("IOT0000001", "robot")
        with self.assertRaises(AttributeError):
            robot.operating_hours = 9999
        self.assertEqual(robot.operating_hours, 0)

    def test_name_setter_normalizes(self):
        """Tên: xóa khoảng trắng thừa, IN HOA."""
        robot = ProductionRobot("IOT0000001", "   robotic   arm alpha ")
        self.assertEqual(robot.name, "ROBOTIC ARM ALPHA")

    def test_empty_name_rejected(self):
        """Tên rỗng / toàn khoảng trắng -> ValueError."""
        with self.assertRaises(ValueError):
            ProductionRobot("IOT0000001", "    ")

    def test_non_positive_hours_rejected(self):
        """Giờ chạy <= 0 -> ValueError (ERR-IOT-03), giữ nguyên giá trị cũ."""
        robot = ProductionRobot("IOT0000001", "robot")
        robot.add_operating_hours(10)
        for bad in (0, -5):
            with self.assertRaises(ValueError):
                robot.add_operating_hours(bad)
        self.assertEqual(robot.operating_hours, 10)


class TestStaticAndClassMethod(unittest.TestCase):
    """validate_device_code, update_maintenance_cost."""

    def test_validate_device_code(self):
        self.assertTrue(BaseDevice.validate_device_code("IOT1234567"))
        for bad in ("IOT99", "iot1234567", "ABC1234567", "IOT12345678", 1234567890):
            self.assertFalse(BaseDevice.validate_device_code(bad))

    def test_update_maintenance_cost_applies_to_all(self):
        """Gọi từ lớp con vẫn đổi chi phí cho toàn hệ thống."""
        original = BaseDevice.base_maintenance_cost
        try:
            ThermalSensor.update_maintenance_cost(2_500_000)
            self.assertEqual(BaseDevice.base_maintenance_cost, 2_500_000)
            self.assertEqual(ProductionRobot.base_maintenance_cost, 2_500_000)
        finally:
            BaseDevice.base_maintenance_cost = original


class TestPolymorphism(unittest.TestCase):
    """track_performance / run_diagnostic đa hình."""

    def test_robot_oee(self):
        """OEE = 1500 / (120 * 50) = 25%."""
        robot = ProductionRobot("IOT0000001", "robot")
        robot.add_operating_hours(120)
        robot.record_metrics(completed_products=1500)
        self.assertEqual(robot.track_performance(), {"oee_percent": 25.0})

    def test_robot_oee_zero_hours(self):
        """Chưa chạy giờ nào -> OEE 0, không ZeroDivisionError."""
        self.assertEqual(ProductionRobot("IOT0000001", "r").track_performance(),
                         {"oee_percent": 0.0})

    def test_sensor_gap_and_danger(self):
        """85 độ / ngưỡng 80 -> biên độ +5, NGUY HIỂM CẤP 1."""
        sensor = ThermalSensor("IOT0000002", "sensor", 85, 80)
        self.assertEqual(sensor.track_performance(), {"temperature_gap": 5.0})
        status, messages, cost = sensor.diagnose()
        self.assertEqual(status, STATUS_DANGER)
        self.assertEqual(len(messages), 1)
        self.assertEqual(cost, BaseDevice.base_maintenance_cost)

    def test_robot_maintenance_over_10000_products(self):
        robot = ProductionRobot("IOT0000001", "robot")
        robot.add_operating_hours(100)
        robot.record_metrics(completed_products=10_001)
        status, messages, _ = robot.diagnose()
        self.assertEqual(status, STATUS_MAINTENANCE)
        self.assertIn("bảo dưỡng cơ khí", messages[0])

    def test_safe_device(self):
        robot = ProductionRobot("IOT0000001", "robot")
        robot.add_operating_hours(10)
        self.assertEqual(robot.diagnose(), (STATUS_SAFE, [], 0))


class TestHybridMRO(unittest.TestCase):
    """Đa kế thừa & logic tổng hợp."""

    def setUp(self):
        self.hybrid = HybridSmartActuator("IOT0012345", "arm", 35.5, 80)

    def test_mro_order(self):
        names = [cls.__name__ for cls in HybridSmartActuator.__mro__]
        self.assertEqual(names, ["HybridSmartActuator", "ProductionRobot", "ThermalSensor",
                                 "BaseDevice", "object"])

    def test_hybrid_combined_performance(self):
        """Hybrid trả về cả OEE lẫn biên độ nhiệt."""
        self.hybrid.add_operating_hours(120)
        self.hybrid.record_metrics(completed_products=4500, current_temperature=85)
        self.assertEqual(self.hybrid.track_performance(),
                         {"oee_percent": 75.0, "temperature_gap": 5.0})

    def test_hybrid_combined_diagnostic(self):
        """Vượt cả sản lượng, nhiệt độ, giờ chạy -> 3 hạng mục, 3 x chi phí."""
        self.hybrid.add_operating_hours(1_200)
        self.hybrid.record_metrics(completed_products=12_000, current_temperature=90)
        status, messages, cost = self.hybrid.diagnose()
        self.assertEqual(status, STATUS_DANGER)
        self.assertEqual(len(messages), 3)
        self.assertEqual(cost, 3 * BaseDevice.base_maintenance_cost)


class TestOperatorOverloading(unittest.TestCase):
    """__add__ / __lt__ và ERR-IOT-04."""

    def setUp(self):
        self.a = ProductionRobot("IOT0000001", "a")
        self.b = ThermalSensor("IOT0000002", "b", 30, 80)
        self.a.add_operating_hours(120)
        self.b.add_operating_hours(250)

    def test_add_and_lt(self):
        self.assertEqual(self.a + self.b, 370)
        self.assertTrue(self.a < self.b)
        self.assertFalse(self.b < self.a)
        self.assertEqual([d.device_id for d in sorted([self.b, self.a])],
                         ["IOT0000001", "IOT0000002"])

    def test_wrong_type_raises_type_error(self):
        with self.assertRaises(TypeError):
            _ = self.a + "abc"
        with self.assertRaises(TypeError):
            _ = self.a < 100

    def test_compare_devices_prints_err_iot_04(self):
        result, output = run_quietly(compare_devices, self.a, "abc")
        self.assertIsNone(result)
        self.assertIn("ERR-IOT-04", output)


class TestDuckTyping(unittest.TestCase):
    """export_telemetry_data và ERR-IOT-05."""

    def setUp(self):
        self.device = ProductionRobot("IOT0000001", "robot")

    def test_valid_gateways(self):
        for gateway in (MQTTEngineGateway(), ERPReportGateway()):
            result, output = run_quietly(export_telemetry_data, gateway, self.device)
            self.assertTrue(result)
            self.assertIn("Duck Typing thành công", output)

    def test_incompatible_gateway(self):
        for gateway in (LegacyModbusGateway(), object(), "gateway"):
            result, output = run_quietly(export_telemetry_data, gateway, self.device)
            self.assertFalse(result)
            self.assertIn("ERR-IOT-05", output)


if __name__ == "__main__":
    unittest.main()
```

Kết quả:

```
test_cannot_instantiate_base_device (TestAbstractAndEncapsulation)
Edge case: tạo trực tiếp BaseDevice -> TypeError. ... ok
test_empty_name_rejected (TestAbstractAndEncapsulation)
Tên rỗng / toàn khoảng trắng -> ValueError. ... ok
test_name_setter_normalizes (TestAbstractAndEncapsulation)
Tên: xóa khoảng trắng thừa, IN HOA. ... ok
test_non_positive_hours_rejected (TestAbstractAndEncapsulation)
Giờ chạy <= 0 -> ValueError (ERR-IOT-03), giữ nguyên giá trị cũ. ... ok
test_operating_hours_has_no_setter (TestAbstractAndEncapsulation)
Gán trực tiếp operating_hours -> AttributeError. ... ok
test_incompatible_gateway (TestDuckTyping) ... ok
test_valid_gateways (TestDuckTyping) ... ok
test_hybrid_combined_diagnostic (TestHybridMRO)
Vượt cả sản lượng, nhiệt độ, giờ chạy -> 3 hạng mục, 3 x chi phí. ... ok
test_hybrid_combined_performance (TestHybridMRO)
Hybrid trả về cả OEE lẫn biên độ nhiệt. ... ok
test_mro_order (TestHybridMRO) ... ok
test_add_and_lt (TestOperatorOverloading) ... ok
test_compare_devices_prints_err_iot_04 (TestOperatorOverloading) ... ok
test_wrong_type_raises_type_error (TestOperatorOverloading) ... ok
test_robot_maintenance_over_10000_products (TestPolymorphism) ... ok
test_robot_oee (TestPolymorphism)
OEE = 1500 / (120 * 50) = 25%. ... ok
test_robot_oee_zero_hours (TestPolymorphism)
Chưa chạy giờ nào -> OEE 0, không ZeroDivisionError. ... ok
test_safe_device (TestPolymorphism) ... ok
test_sensor_gap_and_danger (TestPolymorphism)
85 độ / ngưỡng 80 -> biên độ +5, NGUY HIỂM CẤP 1. ... ok
test_update_maintenance_cost_applies_to_all (TestStaticAndClassMethod)
Gọi từ lớp con vẫn đổi chi phí cho toàn hệ thống. ... ok
test_validate_device_code (TestStaticAndClassMethod) ... ok
Ran 20 tests in 0.003s
OK
```

## Ghi chú

- Tiền tố mã thiết bị chọn là `IOT` theo ví dụ của đề (`IOT1234567`, `IOT0012345`).
- Ví dụ đề có OEE 25.0% với 120 giờ, tức 1,500 sản phẩm tích lũy (1,500 / (120 × 50)); nhưng ví dụ chức năng 2 lại ghi 6,500 sản phẩm ở 120 giờ (OEE sẽ là 108.3%). Chương trình làm đúng công thức OEE; unit test kiểm chứng trường hợp 25%.
- Đặc tả không nêu ngưỡng "số giờ chạy quá cao": chương trình dùng 1,000 giờ (hằng `MAX_OPERATING_HOURS`).
- Chi phí bảo trì dự kiến = `base_maintenance_cost` × số hạng mục bất thường (khớp ví dụ 1 hạng mục → 1,000,000 VND).
- Khi đăng ký, Cảm biến / Hybrid nhập nhiệt độ hiện tại (ví dụ chức năng 2 có hiển thị nhiệt độ ngay sau khi tạo) và ngưỡng an toàn.
- Chức năng 6 có thêm cổng số 3 `LegacyModbusGateway` (không có `process_stream`) để chứng minh ERR-IOT-05 ngay trên menu.
- Log ghi vào file `smart_factory.log` (cạnh `smart_factory.py`) để không lẫn với giao diện console; file trong thư mục là log của kịch bản chạy thử.

## Cách chạy

Yêu cầu Python 3.9+, không cần thư viện ngoài.

```bash
python smart_factory.py
python -m unittest test_smart_factory -v
```
