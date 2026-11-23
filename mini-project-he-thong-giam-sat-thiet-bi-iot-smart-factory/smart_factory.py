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
