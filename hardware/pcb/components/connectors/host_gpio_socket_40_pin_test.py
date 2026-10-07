"""Native pad and logical-pin regression checks for PPPC202LFBN-RC."""

import unittest

import pcbnew

from pcb.components.connectors.host_gpio_socket_40_pin import HostGpioSocket40Pin
from pcb.harness import BoardOutline, Circuit, Net, Placement, Side
from pcb.harness.base.pcbnew.render.board import render_board


class Nets(Net):
    A = "A"
    B = "B"


class HostGpioSocket40PinTest(unittest.TestCase):
    def test_product_pin_mapping_and_native_lands(self) -> None:
        circuit = Circuit(Nets, outline=BoardOutline(160, 160))
        component = circuit.place(
            HostGpioSocket40Pin,
            reference="U1",
            placement=Placement(0, 0),
            purpose="component contract check",
            three_volts_three=Nets.A,
            five_volts=Nets.B,
            i2c_sda=Nets.A,
            five_volts_alt=Nets.B,
            i2c_scl=Nets.A,
            ground_6=Nets.B,
            gpio4=Nets.A,
            uart_tx_gpio14=Nets.B,
            ground_9=Nets.A,
            uart_rx_gpio15=Nets.B,
            button_reset_gpio17=Nets.A,
            gpio18=Nets.B,
            gpio27=Nets.A,
            ground_14=Nets.B,
            button_f3_gpio22=Nets.A,
            button_f4_gpio23=Nets.B,
            three_volts_three_alt=Nets.A,
            button_f5_gpio24=Nets.B,
            spi_data_gpio10=Nets.A,
            ground_20=Nets.B,
            spi_miso_gpio9=Nets.A,
            gpio25=Nets.B,
            spi_clock_gpio11=Nets.A,
            spi_ce0_gpio8=Nets.B,
            ground_25=Nets.A,
            spi_ce1_gpio7=Nets.B,
            id_eeprom_data=Nets.A,
            id_eeprom_clock=Nets.B,
            button_up_gpio5=Nets.A,
            ground_30=Nets.B,
            button_down_gpio6=Nets.A,
            button_left_gpio12=Nets.B,
            button_right_gpio13=Nets.A,
            ground_34=Nets.B,
            button_pass_gpio19=Nets.A,
            button_ok_gpio16=Nets.B,
            led_en_gpio26=Nets.A,
            button_f1_gpio20=Nets.B,
            ground_39=Nets.A,
            button_f2_gpio21=Nets.B,
        )
        self.assertEqual(component.definition.product.part_number, "PPPC202LFBN-RC")
        native = render_board(circuit)
        footprint = next(iter(native.GetFootprints()))
        pads = {pad.GetNumber(): pad for pad in footprint.Pads()}
        expected = (
            ("40", 1.27, -24.13, 1.82, 1.82, 1.02, 0, "B"),
            ("39", -1.27, -24.13, 1.82, 1.82, 1.02, 0, "A"),
            ("38", 1.27, -21.59, 1.82, 1.82, 1.02, 0, "B"),
            ("37", -1.27, -21.59, 1.82, 1.82, 1.02, 0, "A"),
            ("36", 1.27, -19.05, 1.82, 1.82, 1.02, 0, "B"),
            ("35", -1.27, -19.05, 1.82, 1.82, 1.02, 0, "A"),
            ("34", 1.27, -16.51, 1.82, 1.82, 1.02, 0, "B"),
            ("33", -1.27, -16.51, 1.82, 1.82, 1.02, 0, "A"),
            ("32", 1.27, -13.97, 1.82, 1.82, 1.02, 0, "B"),
            ("31", -1.27, -13.97, 1.82, 1.82, 1.02, 0, "A"),
            ("30", 1.27, -11.43, 1.82, 1.82, 1.02, 0, "B"),
            ("29", -1.27, -11.43, 1.82, 1.82, 1.02, 0, "A"),
            ("28", 1.27, -8.89, 1.82, 1.82, 1.02, 0, "B"),
            ("27", -1.27, -8.89, 1.82, 1.82, 1.02, 0, "A"),
            ("26", 1.27, -6.35, 1.82, 1.82, 1.02, 0, "B"),
            ("25", -1.27, -6.35, 1.82, 1.82, 1.02, 0, "A"),
            ("24", 1.27, -3.81, 1.82, 1.82, 1.02, 0, "B"),
            ("23", -1.27, -3.81, 1.82, 1.82, 1.02, 0, "A"),
            ("22", 1.27, -1.269999, 1.82, 1.82, 1.02, 0, "B"),
            ("21", -1.27, -1.269999, 1.82, 1.82, 1.02, 0, "A"),
            ("20", 1.27, 1.269999, 1.82, 1.82, 1.02, 0, "B"),
            ("19", -1.27, 1.269999, 1.82, 1.82, 1.02, 0, "A"),
            ("18", 1.27, 3.809999, 1.82, 1.82, 1.02, 0, "B"),
            ("17", -1.27, 3.809999, 1.82, 1.82, 1.02, 0, "A"),
            ("16", 1.27, 6.349999, 1.82, 1.82, 1.02, 0, "B"),
            ("15", -1.27, 6.349999, 1.82, 1.82, 1.02, 0, "A"),
            ("14", 1.27, 8.889999, 1.82, 1.82, 1.02, 0, "B"),
            ("13", -1.27, 8.889999, 1.82, 1.82, 1.02, 0, "A"),
            ("12", 1.27, 11.43, 1.82, 1.82, 1.02, 0, "B"),
            ("11", -1.27, 11.43, 1.82, 1.82, 1.02, 0, "A"),
            ("10", 1.27, 13.969999, 1.82, 1.82, 1.02, 0, "B"),
            ("9", -1.27, 13.969999, 1.82, 1.82, 1.02, 0, "A"),
            ("8", 1.27, 16.509999, 1.82, 1.82, 1.02, 0, "B"),
            ("7", -1.27, 16.509999, 1.82, 1.82, 1.02, 0, "A"),
            ("6", 1.27, 19.049999, 1.82, 1.82, 1.02, 0, "B"),
            ("5", -1.27, 19.049999, 1.82, 1.82, 1.02, 0, "A"),
            ("4", 1.27, 21.59, 1.82, 1.82, 1.02, 0, "B"),
            ("3", -1.27, 21.59, 1.82, 1.82, 1.02, 0, "A"),
            ("2", 1.27, 24.13, 1.82, 1.82, 1.02, 0, "B"),
            ("1", -1.27, 24.13, 1.82, 1.82, 1.02, 1, "A"),
        )
        self.assertEqual(set(pads), {row[0] for row in expected})
        for number, x, y, width, height, drill, shape, net in expected:
            with self.subTest(pad=number):
                pad = pads[number]
                self.assertAlmostEqual(
                    pcbnew.ToMM(pad.GetPosition().x), 80 + x, places=5
                )
                self.assertAlmostEqual(
                    pcbnew.ToMM(pad.GetPosition().y), 80 - y, places=5
                )
                self.assertAlmostEqual(pcbnew.ToMM(pad.GetSize().x), width, places=5)
                self.assertAlmostEqual(pcbnew.ToMM(pad.GetSize().y), height, places=5)
                self.assertAlmostEqual(
                    pcbnew.ToMM(pad.GetDrillSize().x), drill, places=5
                )
                self.assertEqual(pad.GetShape(), shape)
                self.assertEqual(pad.GetNetname(), net)
        bottom = Circuit(Nets, outline=BoardOutline(160, 160))
        bottom.place(
            HostGpioSocket40Pin,
            reference="J1",
            placement=Placement(0, 0, side=Side.BOTTOM),
            purpose="bottom socket fixed by host pins",
            three_volts_three=Nets.A,
            five_volts=Nets.B,
            i2c_sda=Nets.A,
            five_volts_alt=Nets.B,
            i2c_scl=Nets.A,
            ground_6=Nets.B,
            gpio4=Nets.A,
            uart_tx_gpio14=Nets.B,
            ground_9=Nets.A,
            uart_rx_gpio15=Nets.B,
            button_reset_gpio17=Nets.A,
            gpio18=Nets.B,
            gpio27=Nets.A,
            ground_14=Nets.B,
            button_f3_gpio22=Nets.A,
            button_f4_gpio23=Nets.B,
            three_volts_three_alt=Nets.A,
            button_f5_gpio24=Nets.B,
            spi_data_gpio10=Nets.A,
            ground_20=Nets.B,
            spi_miso_gpio9=Nets.A,
            gpio25=Nets.B,
            spi_clock_gpio11=Nets.A,
            spi_ce0_gpio8=Nets.B,
            ground_25=Nets.A,
            spi_ce1_gpio7=Nets.B,
            id_eeprom_data=Nets.A,
            id_eeprom_clock=Nets.B,
            button_up_gpio5=Nets.A,
            ground_30=Nets.B,
            button_down_gpio6=Nets.A,
            button_left_gpio12=Nets.B,
            button_right_gpio13=Nets.A,
            ground_34=Nets.B,
            button_pass_gpio19=Nets.A,
            button_ok_gpio16=Nets.B,
            led_en_gpio26=Nets.A,
            button_f1_gpio20=Nets.B,
            ground_39=Nets.A,
            button_f2_gpio21=Nets.B,
        )
        native_bottom = render_board(bottom)
        socket = next(iter(native_bottom.GetFootprints()))
        self.assertEqual(socket.GetLayer(), pcbnew.B_Cu)
        positions = {
            pad.GetNumber(): (pad.GetPosition().x, pad.GetPosition().y)
            for pad in socket.Pads()
        }
        self.assertEqual(
            positions,
            {
                pad.GetNumber(): (pad.GetPosition().x, pad.GetPosition().y)
                for pad in footprint.Pads()
            },
        )
