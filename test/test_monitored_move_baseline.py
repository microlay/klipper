import pathlib
import sys
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from klippy.extras.monitored_move import build_z_axis_measurement


def _history(*positions):
    return [
        {
            "measurement_version": 2,
            "measurement_type": "z_axis_baseline",
            "z_position": position,
            "plate_id": index + 1,
        }
        for index, position in enumerate(positions)
    ]


class ZAxisDynamicBaselineTests(unittest.TestCase):
    def test_stable_config_offset_is_reference_mismatch_not_step_loss(self):
        measurement = build_z_axis_measurement(
            _history(77.895937, 77.897812, 77.900937, 77.896562),
            123.0,
            "2026-05-28 12:00:00",
            77.903750,
            77.106000,
            1,
        )

        self.assertEqual(measurement["alert_code"], "z_reference_mismatch")
        self.assertEqual(measurement["measurement_type"], "z_reference_mismatch")
        self.assertIsNone(measurement["step_loss"])
        self.assertAlmostEqual(measurement["delta_to_config"], 0.797750, places=6)
        self.assertLess(abs(measurement["delta_to_runtime_baseline"]), 0.05)

    def test_runtime_drift_over_warning_threshold_generates_warning(self):
        measurement = build_z_axis_measurement(
            _history(77.900000, 77.902000, 77.901000),
            123.0,
            "2026-05-28 12:00:00",
            77.965000,
            77.106000,
            1,
        )

        self.assertEqual(measurement["alert_code"], "z_axis_drift_detected")
        self.assertEqual(measurement["alert_severity"], "medium")
        self.assertAlmostEqual(measurement["step_loss"], 0.064000, places=6)

    def test_runtime_drift_over_step_loss_threshold_is_suspected_step_loss(self):
        measurement = build_z_axis_measurement(
            _history(77.900000, 77.902000, 77.901000),
            123.0,
            "2026-05-28 12:00:00",
            78.025000,
            77.106000,
            1,
        )

        self.assertEqual(measurement["alert_code"], "z_step_loss_suspected")
        self.assertEqual(measurement["alert_severity"], "high")
        self.assertAlmostEqual(measurement["step_loss"], 0.124000, places=6)


if __name__ == "__main__":
    unittest.main()
