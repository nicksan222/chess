"""Explicit coverage of every approved PCB and off-board assembly component.

This is a list of concrete declarations, not a factory or discovery mechanism.
Import the class directly from its component file when placing a part.
"""

from pcb.components.capacitors.capacitor_1_microfarad import CAP_1U_DEFINITION
from pcb.components.capacitors.capacitor_1_nanofarad import CAP_1N_DEFINITION
from pcb.components.capacitors.capacitor_10_microfarad import CAP_10U_DEFINITION
from pcb.components.capacitors.capacitor_10_nanofarad import CAP_10N_DEFINITION
from pcb.components.capacitors.capacitor_100_nanofarad import CAP_100N_DEFINITION
from pcb.components.capacitors.polarized_capacitor_560_microfarad import (
    CAP_560U_DEFINITION,
)
from pcb.components.connectors.host_gpio_male_header_40_pin import (
    HostGpioMaleHeader40Pin,
)
from pcb.components.connectors.host_gpio_socket_40_pin import PI_ZERO_HEADER_DEFINITION
from pcb.components.connectors.oled_connector_4_pin import OLED_HEADER_DEFINITION
from pcb.components.connectors.oled_harness_crimp_contact import OledHarnessCrimpContact
from pcb.components.connectors.oled_harness_housing_4_pin import OledHarnessHousing4Pin
from pcb.components.connectors.panel_dc_barrel_jack import PanelDcBarrelJack
from pcb.components.connectors.power_connector_4_pin import POWER_HEADER_DEFINITION
from pcb.components.connectors.power_harness_crimp_contact import (
    PowerHarnessCrimpContact,
)
from pcb.components.connectors.power_harness_housing_4_pin import (
    PowerHarnessHousing4Pin,
)
from pcb.components.connectors.rocker_switch_receptacle import RockerSwitchReceptacle
from pcb.components.connectors.test_point import TEST_POINT_DEFINITION
from pcb.components.gpio_expanders.gpio_expander_8_bit import TCA9554_DEFINITION
from pcb.components.hall_sensors.hall_sensor import HALL_SENSOR_DEFINITION
from pcb.components.leds.clocked_rgb_led import SK9822_DEFINITION
from pcb.components.level_shifters.logic_level_shifter_4_channel import (
    AHCT125_DEFINITION,
)
from pcb.components.logic_gates.led_enable_logic_gate import (
    LED_ENABLE_GATE_DEFINITION,
)
from pcb.components.modules.microsd_card_32_gigabyte import MicroSdCard32Gigabyte
from pcb.components.modules.oled_display_module import OledDisplayModule
from pcb.components.modules.raspberry_pi_zero_2_w import RaspberryPiZero2W
from pcb.components.mosfets.led_power_mosfet import LED_SWITCH_DEFINITION
from pcb.components.mosfets.led_switch_driver_mosfet import (
    LED_SWITCH_DRIVER_DEFINITION,
)
from pcb.components.power.electronic_fuse import EFUSE_DEFINITION
from pcb.components.power.fuse_2_ampere import FUSE_2A_DEFINITION
from pcb.components.power.power_supply_5_volt_3_ampere import PowerSupply5Volt3Ampere
from pcb.components.resistors.precision_resistor_169_kilohm import (
    RES_169K_PRECISION_DEFINITION,
)
from pcb.components.resistors.precision_resistor_604_kilohm import (
    RES_604K_PRECISION_DEFINITION,
)
from pcb.components.resistors.resistor_1_65_kilohm import RES_1K65_DEFINITION
from pcb.components.resistors.resistor_1_kilohm import RES_1K_DEFINITION
from pcb.components.resistors.resistor_10_kilohm import RES_10K_DEFINITION
from pcb.components.resistors.resistor_56_ohm import RES_56_DEFINITION
from pcb.components.resistors.resistor_100_kilohm import RES_100K_DEFINITION
from pcb.components.resistors.resistor_261_kilohm import RES_261K_DEFINITION
from pcb.components.switches.panel_power_rocker_switch import PanelPowerRockerSwitch
from pcb.components.switches.tactile_button import BUTTON_DEFINITION
from pcb.components.tvs_diodes.bidirectional_tvs_12_volt import TVS_12V0_DEFINITION

PCB_DEFINITIONS = (
    AHCT125_DEFINITION,
    BUTTON_DEFINITION,
    CAP_100N_DEFINITION,
    CAP_10U_DEFINITION,
    CAP_560U_DEFINITION,
    FUSE_2A_DEFINITION,
    HALL_SENSOR_DEFINITION,
    TCA9554_DEFINITION,
    OLED_HEADER_DEFINITION,
    PI_ZERO_HEADER_DEFINITION,
    POWER_HEADER_DEFINITION,
    RES_1K_DEFINITION,
    RES_10K_DEFINITION,
    RES_100K_DEFINITION,
    LED_SWITCH_DEFINITION,
    LED_SWITCH_DRIVER_DEFINITION,
    LED_ENABLE_GATE_DEFINITION,
    SK9822_DEFINITION,
    TEST_POINT_DEFINITION,
    TVS_12V0_DEFINITION,
    EFUSE_DEFINITION,
    RES_1K65_DEFINITION,
    RES_56_DEFINITION,
    RES_261K_DEFINITION,
    RES_604K_PRECISION_DEFINITION,
    RES_169K_PRECISION_DEFINITION,
    CAP_10N_DEFINITION,
    CAP_1N_DEFINITION,
    CAP_1U_DEFINITION,
)

ASSEMBLY_PRODUCTS = (
    RaspberryPiZero2W.product,
    OledDisplayModule.product,
    PowerSupply5Volt3Ampere.product,
    MicroSdCard32Gigabyte.product,
    PanelDcBarrelJack.product,
    PanelPowerRockerSwitch.product,
    HostGpioMaleHeader40Pin.product,
    PowerHarnessHousing4Pin.product,
    PowerHarnessCrimpContact.product,
    RockerSwitchReceptacle.product,
    OledHarnessHousing4Pin.product,
    OledHarnessCrimpContact.product,
)
