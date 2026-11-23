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
