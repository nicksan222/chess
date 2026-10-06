"""I2C rise time and low level on the routed bus at the firmware's bus rate (S5).

Limits: NXP UM10204 table 10 / TI TCA9554 SCPS233E 6.6 (tr 1000 ns at 100 kHz,
300 ns at 400 kHz, Cb 400 pF) and 6.5 (SDA VOL 0.4 V at 3 mA). The pull-ups are the
Pi's 1.8 kOhm alone or with an OLED-module pull-up of 4.7 kOhm (verification
ASSUMPTION "OLED pull-ups").
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from shared import wiring
from spice import datasheets
from spice.i2c_bus import OLED_CORNERS, I2cBus, firmware_i2c_hz
from spice.plane_mesh import routed_board
from spice.support import board_circuits, run_circuit


class I2cSpiceTest(unittest.TestCase):
    """I2C bus capacitance, rise time and sink current at the firmware rate over the OLED pull-up corners."""

    bus: I2cBus

    @classmethod
    def setUpClass(cls) -> None:
        """Build the bus capacitance model from the routed board once."""
        cls.bus = I2cBus(board_circuits(), routed_board())

    def test_bus_capacitance_stays_inside_the_specification(self) -> None:
        for net in (wiring.SDA_NET, wiring.SCL_NET):
            with self.subTest(net=net):
                self.assertLessEqual(
                    self.bus.buses[net].farads, datasheets.I2C_BUS_FARADS_MAX
                )

    def test_firmware_rate_is_one_the_bus_passes(self) -> None:
        self.assertLessEqual(firmware_i2c_hz(), self.bus.fastest_passing_hz())

    def test_edges_and_low_level_at_the_firmware_rate(self) -> None:
        limit = datasheets.I2C_RISE_NS[firmware_i2c_hz()]
        for net in (wiring.SDA_NET, wiring.SCL_NET):
            for oled in OLED_CORNERS:
                with self.subTest(net=net, oled=oled):
                    circuit = self.bus.edge(net, oled_ohms=oled)
                    # SPICE must agree with 0.8473 R C within 2 % and meet the limit.
                    calc = self.bus.rise_ns(net, oled_ohms=oled)
                    self.assertLessEqual(calc, limit)
                    circuit.expect("rise", 0.98 * calc, min(1.02 * calc, limit))
                    circuit.expect("low", 0.0, datasheets.I2C_VOL_VOLTS)
                    run_circuit(f"test_i2c_{net.lower()}_{oled or 'none'}.py", circuit)

    def test_firmware_rate_parser_ignores_comments_and_takes_the_last_value(
        self,
    ) -> None:
        # Reviewer m7: a commented line must not count, and a later assignment wins.
        with tempfile.TemporaryDirectory() as directory:
            yocto = Path(directory)
            (yocto / "kas").mkdir()
            (yocto / "meta-firmware").mkdir()
            config = yocto / "kas" / "firmware.yml"
            config.write_text('#ENABLE_I2C = "1"\nENABLE_I2C = "0"\n')
            with self.assertRaises(ValueError):
                firmware_i2c_hz(yocto)
            config.write_text(
                'ENABLE_I2C = "1"\n'
                'RPI_EXTRA_CONFIG = "dtparam=i2c_arm_baudrate=400000"\n'
                '# RPI_EXTRA_CONFIG = "dtparam=i2c_arm_baudrate=1000000"\n'
                'RPI_EXTRA_CONFIG = "dtparam=i2c_arm_baudrate=100000"\n'
            )
            self.assertEqual(firmware_i2c_hz(yocto), 100_000)
