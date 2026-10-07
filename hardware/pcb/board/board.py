"""The chessboard declared using concrete components and the circuit harness.

`Board()` declares all 327 PCB components and their complete connections.
Coordinates use the physical PCB centre; shared playing-area coordinates are
translated by `_placement`. `generate.py` exports its KiCad project, connection
schematics, PCB, BOM, netlist and review reports. This definition owns physical
features and design rules; `wiring.py` declares routing intent for the harness.
Board tests model sensing and button behavior; full electrical and physical
release validation remain pending.
"""

from pcb.components.capacitors.capacitor_1_microfarad import Capacitor1Microfarad
from pcb.components.capacitors.capacitor_1_nanofarad import Capacitor1Nanofarad
from pcb.components.capacitors.capacitor_10_microfarad import Capacitor10Microfarad
from pcb.components.capacitors.capacitor_10_nanofarad import Capacitor10Nanofarad
from pcb.components.capacitors.capacitor_100_nanofarad import Capacitor100Nanofarad
from pcb.components.capacitors.polarized_capacitor_560_microfarad import (
    PolarizedCapacitor560Microfarad,
)
from pcb.components.connectors.host_gpio_socket_40_pin import HostGpioSocket40Pin
from pcb.components.connectors.oled_connector_4_pin import OledConnector4Pin
from pcb.components.connectors.power_connector_4_pin import PowerConnector4Pin
from pcb.components.connectors.test_point import TestPoint
from pcb.components.gpio_expanders.gpio_expander_8_bit import GpioExpander8Bit
from pcb.components.hall_sensors.hall_sensor import HallSensor
from pcb.components.leds.clocked_rgb_led import ClockedRgbLed
from pcb.components.level_shifters.logic_level_shifter_4_channel import (
    LogicLevelShifter4Channel,
)
from pcb.components.logic_gates.led_enable_logic_gate import LedEnableLogicGate
from pcb.components.mosfets.led_power_mosfet import LedPowerMosfet
from pcb.components.mosfets.led_switch_driver_mosfet import LedSwitchDriverMosfet
from pcb.components.power.electronic_fuse import ElectronicFuse
from pcb.components.power.fuse_2_ampere import Fuse2Ampere
from pcb.components.resistors.precision_resistor_169_kilohm import (
    PrecisionResistor169Kilohm,
)
from pcb.components.resistors.precision_resistor_604_kilohm import (
    PrecisionResistor604Kilohm,
)
from pcb.components.resistors.resistor_1_65_kilohm import Resistor1Point65Kilohm
from pcb.components.resistors.resistor_1_kilohm import Resistor1Kilohm
from pcb.components.resistors.resistor_10_kilohm import Resistor10Kilohm
from pcb.components.resistors.resistor_56_ohm import Resistor56Ohm
from pcb.components.resistors.resistor_100_kilohm import Resistor100Kilohm
from pcb.components.resistors.resistor_261_kilohm import Resistor261Kilohm
from pcb.components.switches.tactile_button import TactileButton
from pcb.components.tvs_diodes.bidirectional_tvs_12_volt import BidirectionalTvs12Volt
from pcb.harness import (
    BoardOutline,
    Circuit,
    CopperLayer,
    Net,
    NetRoute,
    NoConnect,
    Placement,
    Point,
)
from pcb.harness.base.geometry import Side
from pcb.harness.base.pcbnew.design_rules import DesignRules
from pcb.harness.base.pcbnew.layout import BoardLayout, Label, Line, MountingHole, Plane
from pcb.harness.base.pcbnew.routing.settings import RoutingSettings
from shared import dimensions, wiring
from shared.electronics import Tca9554Pin
from shared.panel_buttons import PANEL_BUTTONS


class BoardNet(Net):
    THREE_VOLTS_THREE = "+3V3"
    FIVE_VOLTS = "+5V"
    BTN_DOWN = "BTN_DOWN"
    BTN_F1 = "BTN_F1"
    BTN_F2 = "BTN_F2"
    BTN_F3 = "BTN_F3"
    BTN_F4 = "BTN_F4"
    BTN_F5 = "BTN_F5"
    BTN_LEFT = "BTN_LEFT"
    BTN_OK = "BTN_OK"
    BTN_PASS = "BTN_PASS"
    BTN_RESET = "BTN_RESET"
    BTN_RIGHT = "BTN_RIGHT"
    BTN_UP = "BTN_UP"
    DC_FUSED = "DC_FUSED"
    DC_IN = "DC_IN"
    EFUSE_DVDT = "EFUSE_DVDT"
    EFUSE_EN = "EFUSE_EN"
    EFUSE_ILM = "EFUSE_ILM"
    EFUSE_ITIMER = "EFUSE_ITIMER"
    EFUSE_OVLO = "EFUSE_OVLO"
    GROUND = "GND"
    I2C_SCL = "I2C_SCL"
    I2C_SDA = "I2C_SDA"
    LED_5V = "LED_5V"
    LED_CLK_5V = "LED_CLK_5V"
    LED_DATA_5V = "LED_DATA_5V"
    LED_DATA_BUF = "LED_DATA_BUF"
    LED_EN = "LED_EN"
    LED_EN_GATE = "LED_EN_GATE"
    LED_EN_N = "LED_EN_N"
    LED_OE_N = "LED_OE_N"
    LED_SW_GATE = "LED_SW_GATE"
    RUN = "RUN"
    SPI_CLK_3V3 = "SPI_CLK_3V3"
    SPI_DATA_3V3 = "SPI_DATA_3V3"
    SQ_A1 = "SQ_A1"
    SQ_A2 = "SQ_A2"
    SQ_A3 = "SQ_A3"
    SQ_A4 = "SQ_A4"
    SQ_A5 = "SQ_A5"
    SQ_A6 = "SQ_A6"
    SQ_A7 = "SQ_A7"
    SQ_A8 = "SQ_A8"
    SQ_B1 = "SQ_B1"
    SQ_B2 = "SQ_B2"
    SQ_B3 = "SQ_B3"
    SQ_B4 = "SQ_B4"
    SQ_B5 = "SQ_B5"
    SQ_B6 = "SQ_B6"
    SQ_B7 = "SQ_B7"
    SQ_B8 = "SQ_B8"
    SQ_C1 = "SQ_C1"
    SQ_C2 = "SQ_C2"
    SQ_C3 = "SQ_C3"
    SQ_C4 = "SQ_C4"
    SQ_C5 = "SQ_C5"
    SQ_C6 = "SQ_C6"
    SQ_C7 = "SQ_C7"
    SQ_C8 = "SQ_C8"
    SQ_D1 = "SQ_D1"
    SQ_D2 = "SQ_D2"
    SQ_D3 = "SQ_D3"
    SQ_D4 = "SQ_D4"
    SQ_D5 = "SQ_D5"
    SQ_D6 = "SQ_D6"
    SQ_D7 = "SQ_D7"
    SQ_D8 = "SQ_D8"
    SQ_E1 = "SQ_E1"
    SQ_E2 = "SQ_E2"
    SQ_E3 = "SQ_E3"
    SQ_E4 = "SQ_E4"
    SQ_E5 = "SQ_E5"
    SQ_E6 = "SQ_E6"
    SQ_E7 = "SQ_E7"
    SQ_E8 = "SQ_E8"
    SQ_F1 = "SQ_F1"
    SQ_F2 = "SQ_F2"
    SQ_F3 = "SQ_F3"
    SQ_F4 = "SQ_F4"
    SQ_F5 = "SQ_F5"
    SQ_F6 = "SQ_F6"
    SQ_F7 = "SQ_F7"
    SQ_F8 = "SQ_F8"
    SQ_G1 = "SQ_G1"
    SQ_G2 = "SQ_G2"
    SQ_G3 = "SQ_G3"
    SQ_G4 = "SQ_G4"
    SQ_G5 = "SQ_G5"
    SQ_G6 = "SQ_G6"
    SQ_G7 = "SQ_G7"
    SQ_G8 = "SQ_G8"
    SQ_H1 = "SQ_H1"
    SQ_H2 = "SQ_H2"
    SQ_H3 = "SQ_H3"
    SQ_H4 = "SQ_H4"
    SQ_H5 = "SQ_H5"
    SQ_H6 = "SQ_H6"
    SQ_H7 = "SQ_H7"
    SQ_H8 = "SQ_H8"
    LED_DATA_A1_TO_B1 = "LED_DATA_A1_TO_B1"
    LED_CLOCK_A1_TO_B1 = "LED_CLOCK_A1_TO_B1"
    LED_DATA_B1_TO_C1 = "LED_DATA_B1_TO_C1"
    LED_CLOCK_B1_TO_C1 = "LED_CLOCK_B1_TO_C1"
    LED_DATA_C1_TO_D1 = "LED_DATA_C1_TO_D1"
    LED_CLOCK_C1_TO_D1 = "LED_CLOCK_C1_TO_D1"
    LED_DATA_D1_TO_E1 = "LED_DATA_D1_TO_E1"
    LED_CLOCK_D1_TO_E1 = "LED_CLOCK_D1_TO_E1"
    LED_DATA_E1_TO_F1 = "LED_DATA_E1_TO_F1"
    LED_CLOCK_E1_TO_F1 = "LED_CLOCK_E1_TO_F1"
    LED_DATA_F1_TO_G1 = "LED_DATA_F1_TO_G1"
    LED_CLOCK_F1_TO_G1 = "LED_CLOCK_F1_TO_G1"
    LED_DATA_G1_TO_H1 = "LED_DATA_G1_TO_H1"
    LED_CLOCK_G1_TO_H1 = "LED_CLOCK_G1_TO_H1"
    LED_DATA_H1_TO_H2 = "LED_DATA_H1_TO_H2"
    LED_CLOCK_H1_TO_H2 = "LED_CLOCK_H1_TO_H2"
    LED_DATA_H2_TO_G2 = "LED_DATA_H2_TO_G2"
    LED_CLOCK_H2_TO_G2 = "LED_CLOCK_H2_TO_G2"
    LED_DATA_G2_TO_F2 = "LED_DATA_G2_TO_F2"
    LED_CLOCK_G2_TO_F2 = "LED_CLOCK_G2_TO_F2"
    LED_DATA_F2_TO_E2 = "LED_DATA_F2_TO_E2"
    LED_CLOCK_F2_TO_E2 = "LED_CLOCK_F2_TO_E2"
    LED_DATA_E2_TO_D2 = "LED_DATA_E2_TO_D2"
    LED_CLOCK_E2_TO_D2 = "LED_CLOCK_E2_TO_D2"
    LED_DATA_D2_TO_C2 = "LED_DATA_D2_TO_C2"
    LED_CLOCK_D2_TO_C2 = "LED_CLOCK_D2_TO_C2"
    LED_DATA_C2_TO_B2 = "LED_DATA_C2_TO_B2"
    LED_CLOCK_C2_TO_B2 = "LED_CLOCK_C2_TO_B2"
    LED_DATA_B2_TO_A2 = "LED_DATA_B2_TO_A2"
    LED_CLOCK_B2_TO_A2 = "LED_CLOCK_B2_TO_A2"
    LED_DATA_A2_TO_A3 = "LED_DATA_A2_TO_A3"
    LED_CLOCK_A2_TO_A3 = "LED_CLOCK_A2_TO_A3"
    LED_DATA_A2_TO_A3_SRC = "LED_DATA_A2_TO_A3_SRC"
    LED_DATA_A3_TO_B3 = "LED_DATA_A3_TO_B3"
    LED_CLOCK_A3_TO_B3 = "LED_CLOCK_A3_TO_B3"
    LED_DATA_B3_TO_C3 = "LED_DATA_B3_TO_C3"
    LED_CLOCK_B3_TO_C3 = "LED_CLOCK_B3_TO_C3"
    LED_DATA_C3_TO_D3 = "LED_DATA_C3_TO_D3"
    LED_CLOCK_C3_TO_D3 = "LED_CLOCK_C3_TO_D3"
    LED_DATA_D3_TO_E3 = "LED_DATA_D3_TO_E3"
    LED_CLOCK_D3_TO_E3 = "LED_CLOCK_D3_TO_E3"
    LED_DATA_E3_TO_F3 = "LED_DATA_E3_TO_F3"
    LED_CLOCK_E3_TO_F3 = "LED_CLOCK_E3_TO_F3"
    LED_DATA_F3_TO_G3 = "LED_DATA_F3_TO_G3"
    LED_CLOCK_F3_TO_G3 = "LED_CLOCK_F3_TO_G3"
    LED_DATA_G3_TO_H3 = "LED_DATA_G3_TO_H3"
    LED_CLOCK_G3_TO_H3 = "LED_CLOCK_G3_TO_H3"
    LED_DATA_H3_TO_H4 = "LED_DATA_H3_TO_H4"
    LED_CLOCK_H3_TO_H4 = "LED_CLOCK_H3_TO_H4"
    LED_DATA_H4_TO_G4 = "LED_DATA_H4_TO_G4"
    LED_CLOCK_H4_TO_G4 = "LED_CLOCK_H4_TO_G4"
    LED_DATA_G4_TO_F4 = "LED_DATA_G4_TO_F4"
    LED_CLOCK_G4_TO_F4 = "LED_CLOCK_G4_TO_F4"
    LED_DATA_F4_TO_E4 = "LED_DATA_F4_TO_E4"
    LED_CLOCK_F4_TO_E4 = "LED_CLOCK_F4_TO_E4"
    LED_DATA_E4_TO_D4 = "LED_DATA_E4_TO_D4"
    LED_CLOCK_E4_TO_D4 = "LED_CLOCK_E4_TO_D4"
    LED_DATA_D4_TO_C4 = "LED_DATA_D4_TO_C4"
    LED_CLOCK_D4_TO_C4 = "LED_CLOCK_D4_TO_C4"
    LED_DATA_C4_TO_B4 = "LED_DATA_C4_TO_B4"
    LED_CLOCK_C4_TO_B4 = "LED_CLOCK_C4_TO_B4"
    LED_DATA_B4_TO_A4 = "LED_DATA_B4_TO_A4"
    LED_CLOCK_B4_TO_A4 = "LED_CLOCK_B4_TO_A4"
    LED_DATA_A4_TO_A5 = "LED_DATA_A4_TO_A5"
    LED_CLOCK_A4_TO_A5 = "LED_CLOCK_A4_TO_A5"
    LED_DATA_A4_TO_A5_SRC = "LED_DATA_A4_TO_A5_SRC"
    LED_DATA_A5_TO_B5 = "LED_DATA_A5_TO_B5"
    LED_CLOCK_A5_TO_B5 = "LED_CLOCK_A5_TO_B5"
    LED_DATA_B5_TO_C5 = "LED_DATA_B5_TO_C5"
    LED_CLOCK_B5_TO_C5 = "LED_CLOCK_B5_TO_C5"
    LED_DATA_C5_TO_D5 = "LED_DATA_C5_TO_D5"
    LED_CLOCK_C5_TO_D5 = "LED_CLOCK_C5_TO_D5"
    LED_DATA_D5_TO_E5 = "LED_DATA_D5_TO_E5"
    LED_CLOCK_D5_TO_E5 = "LED_CLOCK_D5_TO_E5"
    LED_DATA_E5_TO_F5 = "LED_DATA_E5_TO_F5"
    LED_CLOCK_E5_TO_F5 = "LED_CLOCK_E5_TO_F5"
    LED_DATA_F5_TO_G5 = "LED_DATA_F5_TO_G5"
    LED_CLOCK_F5_TO_G5 = "LED_CLOCK_F5_TO_G5"
    LED_DATA_G5_TO_H5 = "LED_DATA_G5_TO_H5"
    LED_CLOCK_G5_TO_H5 = "LED_CLOCK_G5_TO_H5"
    LED_DATA_H5_TO_H6 = "LED_DATA_H5_TO_H6"
    LED_CLOCK_H5_TO_H6 = "LED_CLOCK_H5_TO_H6"
    LED_DATA_H6_TO_G6 = "LED_DATA_H6_TO_G6"
    LED_CLOCK_H6_TO_G6 = "LED_CLOCK_H6_TO_G6"
    LED_DATA_G6_TO_F6 = "LED_DATA_G6_TO_F6"
    LED_CLOCK_G6_TO_F6 = "LED_CLOCK_G6_TO_F6"
    LED_DATA_F6_TO_E6 = "LED_DATA_F6_TO_E6"
    LED_CLOCK_F6_TO_E6 = "LED_CLOCK_F6_TO_E6"
    LED_DATA_E6_TO_D6 = "LED_DATA_E6_TO_D6"
    LED_CLOCK_E6_TO_D6 = "LED_CLOCK_E6_TO_D6"
    LED_DATA_D6_TO_C6 = "LED_DATA_D6_TO_C6"
    LED_CLOCK_D6_TO_C6 = "LED_CLOCK_D6_TO_C6"
    LED_DATA_C6_TO_B6 = "LED_DATA_C6_TO_B6"
    LED_CLOCK_C6_TO_B6 = "LED_CLOCK_C6_TO_B6"
    LED_DATA_B6_TO_A6 = "LED_DATA_B6_TO_A6"
    LED_CLOCK_B6_TO_A6 = "LED_CLOCK_B6_TO_A6"
    LED_DATA_A6_TO_A7 = "LED_DATA_A6_TO_A7"
    LED_CLOCK_A6_TO_A7 = "LED_CLOCK_A6_TO_A7"
    LED_DATA_A6_TO_A7_SRC = "LED_DATA_A6_TO_A7_SRC"
    LED_DATA_A7_TO_B7 = "LED_DATA_A7_TO_B7"
    LED_CLOCK_A7_TO_B7 = "LED_CLOCK_A7_TO_B7"
    LED_DATA_B7_TO_C7 = "LED_DATA_B7_TO_C7"
    LED_CLOCK_B7_TO_C7 = "LED_CLOCK_B7_TO_C7"
    LED_DATA_C7_TO_D7 = "LED_DATA_C7_TO_D7"
    LED_CLOCK_C7_TO_D7 = "LED_CLOCK_C7_TO_D7"
    LED_DATA_D7_TO_E7 = "LED_DATA_D7_TO_E7"
    LED_CLOCK_D7_TO_E7 = "LED_CLOCK_D7_TO_E7"
    LED_DATA_E7_TO_F7 = "LED_DATA_E7_TO_F7"
    LED_CLOCK_E7_TO_F7 = "LED_CLOCK_E7_TO_F7"
    LED_DATA_F7_TO_G7 = "LED_DATA_F7_TO_G7"
    LED_CLOCK_F7_TO_G7 = "LED_CLOCK_F7_TO_G7"
    LED_DATA_G7_TO_H7 = "LED_DATA_G7_TO_H7"
    LED_CLOCK_G7_TO_H7 = "LED_CLOCK_G7_TO_H7"
    LED_DATA_H7_TO_H8 = "LED_DATA_H7_TO_H8"
    LED_CLOCK_H7_TO_H8 = "LED_CLOCK_H7_TO_H8"
    LED_DATA_H8_TO_G8 = "LED_DATA_H8_TO_G8"
    LED_CLOCK_H8_TO_G8 = "LED_CLOCK_H8_TO_G8"
    LED_DATA_G8_TO_F8 = "LED_DATA_G8_TO_F8"
    LED_CLOCK_G8_TO_F8 = "LED_CLOCK_G8_TO_F8"
    LED_DATA_F8_TO_E8 = "LED_DATA_F8_TO_E8"
    LED_CLOCK_F8_TO_E8 = "LED_CLOCK_F8_TO_E8"
    LED_DATA_E8_TO_D8 = "LED_DATA_E8_TO_D8"
    LED_CLOCK_E8_TO_D8 = "LED_CLOCK_E8_TO_D8"
    LED_DATA_D8_TO_C8 = "LED_DATA_D8_TO_C8"
    LED_CLOCK_D8_TO_C8 = "LED_CLOCK_D8_TO_C8"
    LED_DATA_C8_TO_B8 = "LED_DATA_C8_TO_B8"
    LED_CLOCK_C8_TO_B8 = "LED_CLOCK_C8_TO_B8"
    LED_DATA_B8_TO_A8 = "LED_DATA_B8_TO_A8"
    LED_CLOCK_B8_TO_A8 = "LED_CLOCK_B8_TO_A8"


# Endpoint-based data/clock networks, in serpentine chain order.
LED_LINKS = (
    (BoardNet.LED_DATA_A1_TO_B1, BoardNet.LED_CLOCK_A1_TO_B1),
    (BoardNet.LED_DATA_B1_TO_C1, BoardNet.LED_CLOCK_B1_TO_C1),
    (BoardNet.LED_DATA_C1_TO_D1, BoardNet.LED_CLOCK_C1_TO_D1),
    (BoardNet.LED_DATA_D1_TO_E1, BoardNet.LED_CLOCK_D1_TO_E1),
    (BoardNet.LED_DATA_E1_TO_F1, BoardNet.LED_CLOCK_E1_TO_F1),
    (BoardNet.LED_DATA_F1_TO_G1, BoardNet.LED_CLOCK_F1_TO_G1),
    (BoardNet.LED_DATA_G1_TO_H1, BoardNet.LED_CLOCK_G1_TO_H1),
    (BoardNet.LED_DATA_H1_TO_H2, BoardNet.LED_CLOCK_H1_TO_H2),
    (BoardNet.LED_DATA_H2_TO_G2, BoardNet.LED_CLOCK_H2_TO_G2),
    (BoardNet.LED_DATA_G2_TO_F2, BoardNet.LED_CLOCK_G2_TO_F2),
    (BoardNet.LED_DATA_F2_TO_E2, BoardNet.LED_CLOCK_F2_TO_E2),
    (BoardNet.LED_DATA_E2_TO_D2, BoardNet.LED_CLOCK_E2_TO_D2),
    (BoardNet.LED_DATA_D2_TO_C2, BoardNet.LED_CLOCK_D2_TO_C2),
    (BoardNet.LED_DATA_C2_TO_B2, BoardNet.LED_CLOCK_C2_TO_B2),
    (BoardNet.LED_DATA_B2_TO_A2, BoardNet.LED_CLOCK_B2_TO_A2),
    (BoardNet.LED_DATA_A2_TO_A3, BoardNet.LED_CLOCK_A2_TO_A3),
    (BoardNet.LED_DATA_A3_TO_B3, BoardNet.LED_CLOCK_A3_TO_B3),
    (BoardNet.LED_DATA_B3_TO_C3, BoardNet.LED_CLOCK_B3_TO_C3),
    (BoardNet.LED_DATA_C3_TO_D3, BoardNet.LED_CLOCK_C3_TO_D3),
    (BoardNet.LED_DATA_D3_TO_E3, BoardNet.LED_CLOCK_D3_TO_E3),
    (BoardNet.LED_DATA_E3_TO_F3, BoardNet.LED_CLOCK_E3_TO_F3),
    (BoardNet.LED_DATA_F3_TO_G3, BoardNet.LED_CLOCK_F3_TO_G3),
    (BoardNet.LED_DATA_G3_TO_H3, BoardNet.LED_CLOCK_G3_TO_H3),
    (BoardNet.LED_DATA_H3_TO_H4, BoardNet.LED_CLOCK_H3_TO_H4),
    (BoardNet.LED_DATA_H4_TO_G4, BoardNet.LED_CLOCK_H4_TO_G4),
    (BoardNet.LED_DATA_G4_TO_F4, BoardNet.LED_CLOCK_G4_TO_F4),
    (BoardNet.LED_DATA_F4_TO_E4, BoardNet.LED_CLOCK_F4_TO_E4),
    (BoardNet.LED_DATA_E4_TO_D4, BoardNet.LED_CLOCK_E4_TO_D4),
    (BoardNet.LED_DATA_D4_TO_C4, BoardNet.LED_CLOCK_D4_TO_C4),
    (BoardNet.LED_DATA_C4_TO_B4, BoardNet.LED_CLOCK_C4_TO_B4),
    (BoardNet.LED_DATA_B4_TO_A4, BoardNet.LED_CLOCK_B4_TO_A4),
    (BoardNet.LED_DATA_A4_TO_A5, BoardNet.LED_CLOCK_A4_TO_A5),
    (BoardNet.LED_DATA_A5_TO_B5, BoardNet.LED_CLOCK_A5_TO_B5),
    (BoardNet.LED_DATA_B5_TO_C5, BoardNet.LED_CLOCK_B5_TO_C5),
    (BoardNet.LED_DATA_C5_TO_D5, BoardNet.LED_CLOCK_C5_TO_D5),
    (BoardNet.LED_DATA_D5_TO_E5, BoardNet.LED_CLOCK_D5_TO_E5),
    (BoardNet.LED_DATA_E5_TO_F5, BoardNet.LED_CLOCK_E5_TO_F5),
    (BoardNet.LED_DATA_F5_TO_G5, BoardNet.LED_CLOCK_F5_TO_G5),
    (BoardNet.LED_DATA_G5_TO_H5, BoardNet.LED_CLOCK_G5_TO_H5),
    (BoardNet.LED_DATA_H5_TO_H6, BoardNet.LED_CLOCK_H5_TO_H6),
    (BoardNet.LED_DATA_H6_TO_G6, BoardNet.LED_CLOCK_H6_TO_G6),
    (BoardNet.LED_DATA_G6_TO_F6, BoardNet.LED_CLOCK_G6_TO_F6),
    (BoardNet.LED_DATA_F6_TO_E6, BoardNet.LED_CLOCK_F6_TO_E6),
    (BoardNet.LED_DATA_E6_TO_D6, BoardNet.LED_CLOCK_E6_TO_D6),
    (BoardNet.LED_DATA_D6_TO_C6, BoardNet.LED_CLOCK_D6_TO_C6),
    (BoardNet.LED_DATA_C6_TO_B6, BoardNet.LED_CLOCK_C6_TO_B6),
    (BoardNet.LED_DATA_B6_TO_A6, BoardNet.LED_CLOCK_B6_TO_A6),
    (BoardNet.LED_DATA_A6_TO_A7, BoardNet.LED_CLOCK_A6_TO_A7),
    (BoardNet.LED_DATA_A7_TO_B7, BoardNet.LED_CLOCK_A7_TO_B7),
    (BoardNet.LED_DATA_B7_TO_C7, BoardNet.LED_CLOCK_B7_TO_C7),
    (BoardNet.LED_DATA_C7_TO_D7, BoardNet.LED_CLOCK_C7_TO_D7),
    (BoardNet.LED_DATA_D7_TO_E7, BoardNet.LED_CLOCK_D7_TO_E7),
    (BoardNet.LED_DATA_E7_TO_F7, BoardNet.LED_CLOCK_E7_TO_F7),
    (BoardNet.LED_DATA_F7_TO_G7, BoardNet.LED_CLOCK_F7_TO_G7),
    (BoardNet.LED_DATA_G7_TO_H7, BoardNet.LED_CLOCK_G7_TO_H7),
    (BoardNet.LED_DATA_H7_TO_H8, BoardNet.LED_CLOCK_H7_TO_H8),
    (BoardNet.LED_DATA_H8_TO_G8, BoardNet.LED_CLOCK_H8_TO_G8),
    (BoardNet.LED_DATA_G8_TO_F8, BoardNet.LED_CLOCK_G8_TO_F8),
    (BoardNet.LED_DATA_F8_TO_E8, BoardNet.LED_CLOCK_F8_TO_E8),
    (BoardNet.LED_DATA_E8_TO_D8, BoardNet.LED_CLOCK_E8_TO_D8),
    (BoardNet.LED_DATA_D8_TO_C8, BoardNet.LED_CLOCK_D8_TO_C8),
    (BoardNet.LED_DATA_C8_TO_B8, BoardNet.LED_CLOCK_C8_TO_B8),
    (BoardNet.LED_DATA_B8_TO_A8, BoardNet.LED_CLOCK_B8_TO_A8),
)

LED_TURN_TERMINATIONS = {"A2": "R10", "A4": "R11", "A6": "R12"}

BANK_REFERENCES = (
    ("A1-D2", "U1", "C3"),
    ("E1-H2", "U2", "C4"),
    ("A3-D4", "U3", "C5"),
    ("E3-H4", "U4", "C6"),
    ("A5-D6", "U70", "C136"),
    ("E5-H6", "U71", "C137"),
    ("A7-D8", "U72", "C138"),
    ("E7-H8", "U73", "C139"),
)


def _placement(
    x_mm: float, y_mm: float, rotation: float = 0, side: Side = Side.TOP
) -> Placement:
    """Translate the shared playing-area origin into the PCB's centre origin."""
    height = dimensions.PCB_SIZE_MM[1]
    return Placement(
        x_mm, y_mm + (height - dimensions.PLAYING_SPAN_MM) / 2, rotation, side
    )


def _strip_placement(reference: str) -> Placement:
    placement = dimensions.PCB_STRIP_PLACEMENTS[reference]
    return _placement(
        *placement.centre_mm,
        placement.rotation_degrees,
        Side.BOTTOM if placement.bottom else Side.TOP,
    )


class Board(Circuit[BoardNet]):
    """The composed board: real component instances and their one pin map."""

    design_rules = DesignRules(
        RoutingSettings(
            track_width_mm=0.31,
            clearance_mm=0.30,
            via_diameter_mm=0.9,
            via_drill_mm=0.4,
            edge_clearance_mm=0.5,
        )
    )
    fabrication_pending = (
        "Declare symbol electrical pin roles for meaningful electrical ERC.",
        "Reassess manufacturing constraints and stackup for physical release.",
        "Extend electrical simulations beyond the modeled sensing and button paths.",
        "Review the engineering assumptions in docs/pcb-assumptions.md.",
    )

    input_bulk_capacitor: PolarizedCapacitor560Microfarad
    host_bulk_capacitor: PolarizedCapacitor560Microfarad
    input_fuse: Fuse2Ampere
    power_connector: PowerConnector4Pin
    host_header: HostGpioSocket40Pin
    input_bypass: Capacitor1Microfarad
    slew_capacitor: Capacitor10Nanofarad
    timer_capacitor: Capacitor1Nanofarad
    overvoltage_filter: Capacitor10Nanofarad
    input_tvs: BidirectionalTvs12Volt
    current_limit_resistor: Resistor1Point65Kilohm
    overvoltage_top: PrecisionResistor604Kilohm
    overvoltage_bottom: PrecisionResistor169Kilohm
    enable_top: PrecisionResistor604Kilohm
    enable_bottom: Resistor261Kilohm
    switch_wetting_load: Resistor1Kilohm
    electronic_fuse: ElectronicFuse
    led_data_termination: Resistor56Ohm
    led_buffer: LogicLevelShifter4Channel
    led_power_switch: LedPowerMosfet

    def __init__(self) -> None:
        width, height, _ = dimensions.PCB_SIZE_MM
        super().__init__(BoardNet, outline=BoardOutline(width, height))
        self.buttons: dict[str, TactileButton] = {}
        self.sensors: dict[str, HallSensor] = {}
        self.leds: dict[str, ClockedRgbLed] = {}
        self.led_turn_terminations: dict[str, Resistor56Ohm] = {}
        self.sensor_bypasses: dict[str, Capacitor100Nanofarad] = {}
        self.led_bypasses: dict[str, Capacitor100Nanofarad] = {}
        self.sensor_banks: dict[str, GpioExpander8Bit] = {}
        self.bank_bypasses: dict[str, Capacitor100Nanofarad] = {}
        _add_power(self)
        _add_controls(self)
        _add_led_switch(self)
        _add_squares(self)
        _add_sensor_banks(self)
        minimum_clearance, minimum_width = self.design_rules.minimums(self)
        self.layout = _layout(
            BoardNet.GROUND,
            BoardNet.FIVE_VOLTS,
            BoardNet.THREE_VOLTS_THREE,
            BoardNet.LED_5V,
            edge_clearance_mm=self.design_rules.routing.edge_clearance_mm,
            minimum_clearance_mm=minimum_clearance,
            minimum_track_width_mm=minimum_width,
        )
        self.validate()
        from pcb.board.wiring import wiring as define_wiring

        self.wiring: tuple[NetRoute, ...] = define_wiring(self)

    def route(self) -> None:
        """Lay out copper from the components' declared pin maps."""
        from pcb.board.wiring import routing_plan
        from pcb.harness.base.pcbnew.routing.run import route

        route(self, routing_plan(self), self.design_rules.routing)

    def sensor(self, square: str) -> HallSensor:
        """Return the individual Hall sensor placed on this square."""
        try:
            return self.sensors[square]
        except KeyError as error:
            raise ValueError(f"unknown square: {square}") from error

    def sense_input(self, square: str) -> tuple[GpioExpander8Bit, Tca9554Pin]:
        assignment = wiring.expander_of(wiring.parse_square(square))
        return self.sensor_banks[assignment.bank.label], Tca9554Pin[
            f"P{assignment.pin_index}"
        ]

    @property
    def sensing_components(
        self,
    ) -> tuple[HallSensor | GpioExpander8Bit | Capacitor100Nanofarad, ...]:
        """Actual Hall sensors, input banks and their supply bypass capacitors."""
        return (
            *self.sensors.values(),
            *self.sensor_bypasses.values(),
            *self.sensor_banks.values(),
            *self.bank_bypasses.values(),
        )


def _add_power(circuit: Board) -> None:
    """Each concrete constructor owns its mapping from these signals to pads."""
    circuit.input_bulk_capacitor = circuit.place(
        PolarizedCapacitor560Microfarad,
        reference="C1",
        placement=_strip_placement("C1"),
        purpose="LED rail bulk capacitor",
        positive=BoardNet.FIVE_VOLTS,
        negative=BoardNet.GROUND,
    )
    circuit.host_bulk_capacitor = circuit.place(
        PolarizedCapacitor560Microfarad,
        reference="C140",
        placement=_strip_placement("C140"),
        purpose="LED rail bulk capacitor",
        positive=BoardNet.FIVE_VOLTS,
        negative=BoardNet.GROUND,
    )
    circuit.input_bypass = circuit.place(
        Capacitor1Microfarad,
        reference="C141",
        placement=_strip_placement("C141"),
        purpose="eFuse input bypass",
        terminal_a=BoardNet.DC_FUSED,
        terminal_b=BoardNet.GROUND,
    )
    circuit.slew_capacitor = circuit.place(
        Capacitor10Nanofarad,
        reference="C142",
        placement=_strip_placement("C142"),
        purpose="eFuse dVdt",
        terminal_a=BoardNet.EFUSE_DVDT,
        terminal_b=BoardNet.GROUND,
    )
    circuit.timer_capacitor = circuit.place(
        Capacitor1Nanofarad,
        reference="C143",
        placement=_strip_placement("C143"),
        purpose="eFuse ITIMER",
        terminal_a=BoardNet.EFUSE_ITIMER,
        terminal_b=BoardNet.GROUND,
    )
    circuit.overvoltage_filter = circuit.place(
        Capacitor10Nanofarad,
        reference="C144",
        placement=_strip_placement("C144"),
        purpose="OVLO spike filter",
        terminal_a=BoardNet.EFUSE_OVLO,
        terminal_b=BoardNet.GROUND,
    )
    circuit.place(
        Capacitor10Microfarad,
        reference="C2",
        placement=_strip_placement("C2"),
        purpose="Rail decoupling capacitor",
        terminal_a=BoardNet.FIVE_VOLTS,
        terminal_b=BoardNet.GROUND,
    )
    circuit.input_tvs = circuit.place(
        BidirectionalTvs12Volt,
        reference="D1",
        placement=_strip_placement("D1"),
        purpose="Bidirectional transient suppressor on the eFuse input",
        protected_input=BoardNet.DC_FUSED,
        ground=BoardNet.GROUND,
    )
    circuit.input_fuse = circuit.place(
        Fuse2Ampere,
        reference="F1",
        placement=_strip_placement("F1"),
        purpose="Input over-current protection on the jack tip",
        unfused_input=BoardNet.DC_IN,
        fused_output=BoardNet.DC_FUSED,
    )
    circuit.power_connector = circuit.place(
        PowerConnector4Pin,
        reference="J4",
        placement=_strip_placement("J4"),
        purpose="Power entry: jack and rocker harness",
        dc_input=BoardNet.DC_IN,
        ground=BoardNet.GROUND,
        fused_to_switch=BoardNet.DC_FUSED,
        run=BoardNet.RUN,
    )
    circuit.current_limit_resistor = circuit.place(
        Resistor1Point65Kilohm,
        reference="R3",
        placement=_strip_placement("R3"),
        purpose="eFuse current limit (ILM)",
        terminal_a=BoardNet.EFUSE_ILM,
        terminal_b=BoardNet.GROUND,
    )
    circuit.overvoltage_top = circuit.place(
        PrecisionResistor604Kilohm,
        reference="R4",
        placement=_strip_placement("R4"),
        purpose="OVLO divider, top",
        terminal_a=BoardNet.EFUSE_OVLO,
        terminal_b=BoardNet.DC_FUSED,
    )
    circuit.overvoltage_bottom = circuit.place(
        PrecisionResistor169Kilohm,
        reference="R5",
        placement=_strip_placement("R5"),
        purpose="OVLO divider, bottom",
        terminal_a=BoardNet.EFUSE_OVLO,
        terminal_b=BoardNet.GROUND,
    )
    circuit.enable_top = circuit.place(
        PrecisionResistor604Kilohm,
        reference="R6",
        placement=_strip_placement("R6"),
        purpose="EN divider from RUN, top",
        terminal_a=BoardNet.RUN,
        terminal_b=BoardNet.EFUSE_EN,
    )
    circuit.enable_bottom = circuit.place(
        Resistor261Kilohm,
        reference="R7",
        placement=_strip_placement("R7"),
        purpose="EN divider, bottom",
        terminal_a=BoardNet.EFUSE_EN,
        terminal_b=BoardNet.GROUND,
    )
    circuit.switch_wetting_load = circuit.place(
        Resistor1Kilohm,
        reference="R8",
        placement=_strip_placement("R8"),
        purpose="Rocker contact wetting load",
        terminal_a=BoardNet.RUN,
        terminal_b=BoardNet.GROUND,
    )
    circuit.place(
        TestPoint,
        reference="TP1",
        placement=_strip_placement("TP1"),
        purpose="5 V test point",
        probe=BoardNet.FIVE_VOLTS,
    )
    circuit.place(
        TestPoint,
        reference="TP2",
        placement=_strip_placement("TP2"),
        purpose="Ground test point",
        probe=BoardNet.GROUND,
    )
    circuit.place(
        TestPoint,
        reference="TP5",
        placement=_strip_placement("TP5"),
        purpose="3.3 V test point",
        probe=BoardNet.THREE_VOLTS_THREE,
    )
    circuit.electronic_fuse = circuit.place(
        ElectronicFuse,
        reference="U74",
        placement=_strip_placement("U74"),
        purpose="Input eFuse: inrush, OVLO, reverse blocking, circuit breaker",
        enable_uvlo=BoardNet.EFUSE_EN,
        overvoltage_lockout=BoardNet.EFUSE_OVLO,
        power_good=NoConnect("Unused by the chessboard"),
        power_good_threshold=BoardNet.EFUSE_OVLO,
        input=BoardNet.DC_FUSED,
        output=BoardNet.FIVE_VOLTS,
        slew_rate=BoardNet.EFUSE_DVDT,
        ground=BoardNet.GROUND,
        current_limit=BoardNet.EFUSE_ILM,
        overcurrent_timer=BoardNet.EFUSE_ITIMER,
    )


def _add_controls(circuit: Board) -> None:
    """Each concrete constructor owns its mapping from these signals to pads."""
    circuit.place(
        Capacitor100Nanofarad,
        reference="C7",
        placement=_strip_placement("C7"),
        purpose="Buffer decoupling capacitor",
        terminal_a=BoardNet.FIVE_VOLTS,
        terminal_b=BoardNet.GROUND,
    )
    circuit.host_header = circuit.place(
        HostGpioSocket40Pin,
        reference="J1",
        placement=_placement(
            *dimensions.PI_HEADER_CENTER_MM,
            (dimensions.PI_ROTATION_DEG + 90) % 360,
            Side.BOTTOM,
        ),
        purpose="Raspberry Pi Zero 2 W GPIO socket",
        three_volts_three=BoardNet.THREE_VOLTS_THREE,
        five_volts=BoardNet.FIVE_VOLTS,
        i2c_sda=BoardNet.I2C_SDA,
        five_volts_alt=BoardNet.FIVE_VOLTS,
        i2c_scl=BoardNet.I2C_SCL,
        ground_6=BoardNet.GROUND,
        gpio4=NoConnect("Unused by the chessboard"),
        uart_tx_gpio14=NoConnect("Unused by the chessboard"),
        ground_9=BoardNet.GROUND,
        uart_rx_gpio15=NoConnect("Unused by the chessboard"),
        button_reset_gpio17=BoardNet.BTN_RESET,
        gpio18=NoConnect("Unused by the chessboard"),
        gpio27=NoConnect("Unused by the chessboard"),
        ground_14=BoardNet.GROUND,
        button_f3_gpio22=BoardNet.BTN_F3,
        button_f4_gpio23=BoardNet.BTN_F4,
        three_volts_three_alt=BoardNet.THREE_VOLTS_THREE,
        button_f5_gpio24=BoardNet.BTN_F5,
        spi_data_gpio10=BoardNet.SPI_DATA_3V3,
        ground_20=BoardNet.GROUND,
        spi_miso_gpio9=NoConnect("Unused by the chessboard"),
        gpio25=NoConnect("Unused by the chessboard"),
        spi_clock_gpio11=BoardNet.SPI_CLK_3V3,
        spi_ce0_gpio8=NoConnect("Unused by the chessboard"),
        ground_25=BoardNet.GROUND,
        spi_ce1_gpio7=NoConnect("Unused by the chessboard"),
        id_eeprom_data=NoConnect("Unused by the chessboard"),
        id_eeprom_clock=NoConnect("Unused by the chessboard"),
        button_up_gpio5=BoardNet.BTN_UP,
        ground_30=BoardNet.GROUND,
        button_down_gpio6=BoardNet.BTN_DOWN,
        button_left_gpio12=BoardNet.BTN_LEFT,
        button_right_gpio13=BoardNet.BTN_RIGHT,
        ground_34=BoardNet.GROUND,
        button_pass_gpio19=BoardNet.BTN_PASS,
        button_ok_gpio16=BoardNet.BTN_OK,
        led_en_gpio26=BoardNet.LED_EN,
        button_f1_gpio20=BoardNet.BTN_F1,
        ground_39=BoardNet.GROUND,
        button_f2_gpio21=BoardNet.BTN_F2,
    )
    circuit.place(
        OledConnector4Pin,
        reference="J2",
        placement=_strip_placement("J2"),
        purpose="OLED harness header (module wired by its pad labels)",
        ground=BoardNet.GROUND,
        three_volts_three=BoardNet.THREE_VOLTS_THREE,
        i2c_clock=BoardNet.I2C_SCL,
        i2c_data=BoardNet.I2C_SDA,
        mounting_tab_a=BoardNet.GROUND,
        mounting_tab_b=BoardNet.GROUND,
    )
    circuit.place(
        Resistor10Kilohm,
        reference="R17",
        placement=_strip_placement("R17"),
        purpose="LED_DATA_5V pull-down while the buffer is Hi-Z",
        terminal_a=BoardNet.LED_DATA_5V,
        terminal_b=BoardNet.GROUND,
    )
    circuit.place(
        Resistor10Kilohm,
        reference="R18",
        placement=_strip_placement("R18"),
        purpose="LED_CLK_5V pull-down while the buffer is Hi-Z",
        terminal_a=BoardNet.LED_CLK_5V,
        terminal_b=BoardNet.GROUND,
    )
    circuit.led_data_termination = circuit.place(
        Resistor56Ohm,
        reference="R9",
        placement=_strip_placement("R9"),
        purpose="LED data source termination",
        terminal_a=BoardNet.LED_DATA_5V,
        terminal_b=BoardNet.LED_DATA_BUF,
    )
    circuit.place(
        TestPoint,
        reference="TP3",
        placement=_strip_placement("TP3"),
        purpose="Buffered LED data test point",
        probe=BoardNet.LED_DATA_5V,
    )
    circuit.place(
        TestPoint,
        reference="TP4",
        placement=_strip_placement("TP4"),
        purpose="Buffered LED clock test point",
        probe=BoardNet.LED_CLK_5V,
    )
    circuit.place(
        TestPoint,
        reference="TP6",
        placement=_strip_placement("TP6"),
        purpose="I2C clock test point",
        probe=BoardNet.I2C_SCL,
    )
    circuit.place(
        TestPoint,
        reference="TP7",
        placement=_strip_placement("TP7"),
        purpose="I2C data test point",
        probe=BoardNet.I2C_SDA,
    )
    circuit.led_buffer = circuit.place(
        LogicLevelShifter4Channel,
        reference="U5",
        placement=_strip_placement("U5"),
        purpose="Quad 5 V buffer accepts 3.3 V SPI clock and data",
        buffer_1_output_enable=BoardNet.LED_OE_N,
        buffer_1_input=BoardNet.SPI_DATA_3V3,
        buffer_1_output=BoardNet.LED_DATA_BUF,
        buffer_2_output_enable=BoardNet.LED_OE_N,
        buffer_2_input=BoardNet.SPI_CLK_3V3,
        buffer_2_output=BoardNet.LED_CLK_5V,
        ground=BoardNet.GROUND,
        buffer_3_output=NoConnect("Unused by the chessboard"),
        buffer_3_input=BoardNet.GROUND,
        buffer_3_output_enable=BoardNet.FIVE_VOLTS,
        buffer_4_output=NoConnect("Unused by the chessboard"),
        buffer_4_input=BoardNet.GROUND,
        buffer_4_output_enable=BoardNet.FIVE_VOLTS,
        supply=BoardNet.FIVE_VOLTS,
    )
    for button in PANEL_BUTTONS:
        circuit.buttons[button.name] = circuit.place(
            TactileButton,
            reference=button.switch_reference,
            placement=_placement(*button.position_mm),
            purpose="Momentary panel button, 8.0 mm round stem",
            signal=BoardNet(button.net_name),
            ground=BoardNet.GROUND,
        )


def _add_led_switch(circuit: Board) -> None:
    """Each concrete constructor owns its mapping from these signals to pads."""
    circuit.place(
        Capacitor10Nanofarad,
        reference="C145",
        placement=_strip_placement("C145"),
        purpose="Q1 gate-to-drain ramp capacitor",
        terminal_a=BoardNet.LED_SW_GATE,
        terminal_b=BoardNet.LED_5V,
    )
    circuit.place(
        Capacitor100Nanofarad,
        reference="C146",
        placement=_strip_placement("C146"),
        purpose="U75 decoupling capacitor",
        terminal_a=BoardNet.FIVE_VOLTS,
        terminal_b=BoardNet.GROUND,
    )
    circuit.led_power_switch = circuit.place(
        LedPowerMosfet,
        reference="Q1",
        placement=_strip_placement("Q1"),
        purpose="LED rail switch, +5V to LED_5V",
        source=BoardNet.FIVE_VOLTS,
        gate=BoardNet.LED_SW_GATE,
        drain=BoardNet.LED_5V,
    )
    circuit.place(
        LedSwitchDriverMosfet,
        reference="Q2",
        placement=_strip_placement("Q2"),
        purpose="LED_EN inverter driving the LED switch gate and buffer enables",
        gate=BoardNet.LED_EN_GATE,
        source=BoardNet.GROUND,
        drain=BoardNet.LED_EN_N,
    )
    circuit.place(
        Resistor1Kilohm,
        reference="R13",
        placement=_strip_placement("R13"),
        purpose="LED_EN series to Q2 gate",
        terminal_a=BoardNet.LED_EN,
        terminal_b=BoardNet.LED_EN_GATE,
    )
    circuit.place(
        Resistor100Kilohm,
        reference="R14",
        placement=_strip_placement("R14"),
        purpose="Q2 gate pull-down (LED rail off)",
        terminal_a=BoardNet.LED_EN_GATE,
        terminal_b=BoardNet.GROUND,
    )
    circuit.place(
        Resistor10Kilohm,
        reference="R15",
        placement=_strip_placement("R15"),
        purpose="LED_EN_N pull-up",
        terminal_a=BoardNet.LED_EN_N,
        terminal_b=BoardNet.FIVE_VOLTS,
    )
    circuit.place(
        Resistor100Kilohm,
        reference="R16",
        placement=_strip_placement("R16"),
        purpose="Q1 gate drive (turn-on ramp)",
        terminal_a=BoardNet.LED_EN_N,
        terminal_b=BoardNet.LED_SW_GATE,
    )
    circuit.place(
        LedEnableLogicGate,
        reference="U75",
        placement=_strip_placement("U75"),
        purpose="LED_OE_N = Schmitt(Q1 gate) OR LED_EN_N: buffer on only once LED_5V is up",
        input_1=BoardNet.LED_EN_N,
        ground=BoardNet.GROUND,
        input_0=BoardNet.FIVE_VOLTS,
        output=BoardNet.LED_OE_N,
        supply=BoardNet.FIVE_VOLTS,
        input_2=BoardNet.LED_SW_GATE,
    )


def _add_squares(board: Board) -> None:
    for square in dimensions.BOARD_SQUARES.led_chain:
        index = square.led_chain_index
        rotation = 0 if square.position.rank % 2 else 180
        direction = 1 if rotation == 0 else -1
        lx, ly = square.led_position_mm
        hx, hy = square.hall_position_mm
        data_in, clock_in = (
            (BoardNet.LED_DATA_5V, BoardNet.LED_CLK_5V)
            if index == 0
            else LED_LINKS[index - 1]
        )
        data_out: Net | NoConnect
        clock_out: Net | NoConnect
        if index == len(LED_LINKS):
            data_out = NoConnect("Last LED has no downstream data receiver")
            clock_out = NoConnect("Last LED has no downstream clock receiver")
        else:
            data_out, clock_out = LED_LINKS[index]
            if square.name in LED_TURN_TERMINATIONS:
                data_out = BoardNet(data_out.label + "_SRC")
        board.leds[square.name] = board.place(
            ClockedRgbLed,
            reference=f"U{6 + index}",
            placement=_placement(lx, ly, rotation),
            purpose="Clocked 5050 RGB LED",
            data_in=data_in,
            clock_in=clock_in,
            ground=BoardNet.GROUND,
            five_volts=BoardNet.LED_5V,
            data_out=data_out,
            clock_out=clock_out,
        )
        board.sensors[square.name] = board.place(
            HallSensor,
            reference=f"HS{square.sensor_number}",
            placement=_placement(hx, hy),
            purpose="Omnipolar active-low Hall-effect square sensor",
            supply=BoardNet.THREE_VOLTS_THREE,
            active_low_output=BoardNet(wiring.sense_net(square.name)),
            ground=BoardNet.GROUND,
        )
        board.led_bypasses[square.name] = board.place(
            Capacitor100Nanofarad,
            reference=f"C{8 + index}",
            placement=_placement(lx, ly + direction * 4, rotation),
            purpose="Local LED decoupling capacitor",
            terminal_a=BoardNet.LED_5V,
            terminal_b=BoardNet.GROUND,
        )
        board.sensor_bypasses[square.name] = board.place(
            Capacitor100Nanofarad,
            reference=f"C{71 + square.sensor_number}",
            placement=_placement(hx, hy - 2.4),
            purpose="Local Hall-sensor decoupling capacitor",
            terminal_a=BoardNet.THREE_VOLTS_THREE,
            terminal_b=BoardNet.GROUND,
        )
        if square.name in LED_TURN_TERMINATIONS:
            board.led_turn_terminations[square.name] = board.place(
                Resistor56Ohm,
                reference=LED_TURN_TERMINATIONS[square.name],
                # The DATA_OUT land is 2.6 mm outward and 1.6 mm down;
                # the termination centre is another 3.05 mm outward.
                placement=_placement(lx - direction * 5.65, ly - direction * 1.6),
                purpose="LED rank-turn data source termination",
                terminal_a=LED_LINKS[index][0],
                terminal_b=BoardNet(LED_LINKS[index][0].label + "_SRC"),
            )


def _add_sensor_banks(board: Board) -> None:
    for label, reference, bypass_reference in BANK_REFERENCES:
        bank = next(bank for bank in dimensions.HALL_BANKS if bank.label == label)
        x, y = dimensions.EXPANDER_POSITIONS_BY_BANK_MM[label]
        channels = tuple(
            BoardNet(wiring.sense_net(member.name)) for member in bank.members
        )
        straps = tuple(
            BoardNet.THREE_VOLTS_THREE if high else BoardNet.GROUND
            for high in bank.straps
        )
        board.sensor_banks[label] = board.place(
            GpioExpander8Bit,
            reference=reference,
            placement=_placement(x, y),
            purpose="Polled 8-bit I2C GPIO expander",
            address_0=straps[0],
            address_1=straps[1],
            address_2=straps[2],
            p0=channels[0],
            p1=channels[1],
            p2=channels[2],
            p3=channels[3],
            p4=channels[4],
            p5=channels[5],
            p6=channels[6],
            p7=channels[7],
            ground=BoardNet.GROUND,
            supply=BoardNet.THREE_VOLTS_THREE,
            i2c_clock=BoardNet.I2C_SCL,
            i2c_data=BoardNet.I2C_SDA,
            interrupt=NoConnect("Hall banks are polled; interrupt is unused"),
        )
        board.bank_bypasses[label] = board.place(
            Capacitor100Nanofarad,
            reference=bypass_reference,
            placement=_placement(x + 3.5, y + 6.3, 180),
            purpose="Expander decoupling capacitor",
            terminal_a=BoardNet.THREE_VOLTS_THREE,
            terminal_b=BoardNet.GROUND,
        )


def _layout_point(x: float, y: float) -> Point:
    return Point(x, y + (dimensions.PCB_SIZE_MM[1] - dimensions.PLAYING_SPAN_MM) / 2)


def _layout[BoardNet: Net](
    ground: BoardNet,
    supply: BoardNet,
    logic_supply: BoardNet,
    led_supply: BoardNet,
    *,
    edge_clearance_mm: float,
    minimum_clearance_mm: float,
    minimum_track_width_mm: float,
) -> BoardLayout[BoardNet]:
    labels = [
        Label("CHESS BOARD", _layout_point(116, -165), 1.5),
        Label("J4: 1 DC-IN 2 GND 3 FUSED 4 RUN", _layout_point(-105, 125.9), 0.8),
        Label("U5 SPI 3V3 -> LED 5V", _layout_point(-60, -165), 0.8),
        Label("LED DATA + CLK IN", _layout_point(-127, -118), 0.8),
    ]
    for reference, text, dx, dy in (
        ("F1", "F1 2A FAST", 0, -3.4),
        ("D1", "D1 TVS", 0, 2.6),
        ("J2", "J2 OLED: 1 GND 2 3V3 3 SCL 4 SDA", 0, 4.1),
    ):
        x, y = dimensions.PCB_STRIP_PLACEMENTS[reference].centre_mm
        labels.append(Label(text, _layout_point(x + dx, y + dy), 0.8))
    for square in dimensions.BOARD_SQUARES:
        x, y = square.centre_mm
        labels.append(Label(square.name, _layout_point(x - 12, y)))
    for button in PANEL_BUTTONS:
        x, y = button.position_mm
        labels.append(
            Label(
                button.name,
                _layout_point(
                    x, y + (4.5 if y > dimensions.PANEL_ORIGIN_Y_MM else -4.5)
                ),
                0.9,
            )
        )
    half = dimensions.PLAYING_SPAN_MM / 2
    boundaries = tuple(
        -half + index * dimensions.SQUARE_SIZE_MM
        for index in range(1, dimensions.GRID_COUNT)
    )
    along = tuple(
        -half + index * 8 for index in range(1, round(dimensions.PLAYING_SPAN_MM / 8))
    )
    dots = {(boundary, offset) for boundary in boundaries for offset in along}
    dots.update((offset, boundary) for boundary in boundaries for offset in along)
    lines = tuple(
        Line(_layout_point(x - 0.01, y), _layout_point(x + 0.01, y), 0.6)
        for x, y in sorted(dots)
        if all(
            (x - hx) ** 2 + (y - hy) ** 2 >= 16
            for hx, hy in dimensions.PCB_SUPPORT_POSITIONS_MM
        )
    )
    return BoardLayout(
        copper_layers=8,
        thickness_mm=dimensions.PCB_THICKNESS_MM,
        edge_clearance_mm=edge_clearance_mm,
        minimum_clearance_mm=minimum_clearance_mm,
        minimum_track_width_mm=minimum_track_width_mm,
        planes=(
            Plane(ground, CopperLayer.INNER_1),
            Plane(supply, CopperLayer.INNER_2),
            Plane(logic_supply, CopperLayer.INNER_3),
            Plane(led_supply, CopperLayer.INNER_6),
        ),
        holes=tuple(
            MountingHole(
                f"H{index}",
                _layout_point(x, y),
                dimensions.PCB_MOUNTING_HOLE_DIAMETER_MM,
            )
            for index, (x, y) in enumerate(dimensions.PCB_SUPPORT_POSITIONS_MM, 1)
        ),
        labels=tuple(labels),
        lines=lines,
    )
