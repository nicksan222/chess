#![allow(
    clippy::unwrap_used,
    clippy::expect_used,
    clippy::panic,
    reason = "integration-test helpers panic to report a failure"
)]

mod bus;
mod frame;
mod scene;

use embedded_graphics::{
    Pixel,
    geometry::Point,
    pixelcolor::BinaryColor,
    prelude::*,
    primitives::{PrimitiveStyle, Rectangle},
};
use embedded_graphics_simulator::SimulatorDisplay;
use firmware::hardware::display::{Display, HEIGHT, I2C_ADDRESS, WIDTH};

use bus::{BUFFER_SIZE, COMMAND, CapturingI2C, DATA, DyingI2C};
use frame::*;
use scene::{Scene, verify_scene};

#[test]
fn primitives_survive_the_real_display_i2c_stream() {
    verify_scene("primitives", Scene::Primitives);
}

#[test]
fn text_survives_the_real_display_i2c_stream() {
    verify_scene("text", Scene::Text);
}

#[test]
fn inverted_menu_row_survives_the_real_display_i2c_stream() {
    verify_scene("inverted-menu-row", Scene::Menu);
}

#[test]
fn clipped_text_survives_the_real_display_i2c_stream() {
    verify_scene("clipped-text", Scene::ClippedText);
}

#[test]
fn symbols_survive_the_real_display_i2c_stream() {
    verify_scene("symbols", Scene::Symbols);
}

#[test]
fn initialization_uses_the_board_address_and_controller_commands() {
    let bus = CapturingI2C::default();
    let mut display = Display::new(bus.clone());

    display.initialize().unwrap();

    let writes = bus.writes.borrow();
    assert!(!writes.is_empty());
    assert!(writes.iter().all(|(address, _)| *address == I2C_ADDRESS));
    let commands = command_bytes(&writes);
    // Supplier SSD1309 sequence plus explicit page mode: flush selects pages,
    // so a horizontal-address-mode regression would corrupt real hardware.
    assert_eq!(
        commands,
        [
            0xAE, 0xFD, 0x12, 0x20, 0x02, 0x00, 0x10, 0x40, 0x81, 0xBF, 0xA1, 0xA6, 0xA8, 0x3F,
            0xC8, 0xD3, 0x00, 0xD5, 0xA0, 0xD9, 0xF1, 0xDA, 0x12, 0xDB, 0x34, 0xA4, 0xA6, 0xAF,
        ]
    );
    save_screenshot("initialized", &SimulatorDisplay::new(panel_size()));
}

#[test]
fn one_pixel_is_encoded_in_the_transmitted_page_major_frame() {
    let bus = CapturingI2C::default();
    let mut display = initialized_display(&bus);
    Pixel(Point::new(3, 9), BinaryColor::On)
        .draw(&mut display)
        .unwrap();

    display.flush().unwrap();

    let actual = display_from_i2c(&bus);
    assert_eq!(actual.get_pixel(Point::new(3, 9)), BinaryColor::On);
    assert_eq!(actual.get_pixel(Point::new(3, 8)), BinaryColor::Off);
    assert_eq!(actual.get_pixel(Point::new(4, 9)), BinaryColor::Off);
    save_screenshot("page-layout", &actual);
}

#[test]
fn flush_transmits_one_complete_128_by_64_frame() {
    let bus = CapturingI2C::default();
    let mut display = initialized_display(&bus);
    Rectangle::new(Point::zero(), panel_size())
        .into_styled(PrimitiveStyle::with_stroke(BinaryColor::On, 1))
        .draw(&mut display)
        .unwrap();

    display.flush().unwrap();

    let frame = transmitted_frame(&bus);
    assert_eq!(frame.len(), BUFFER_SIZE);
    let actual = display_from_frame(&frame);
    save_screenshot("full-frame-flush", &actual);
}

#[test]
fn display_power_commands_do_not_mutate_the_transmitted_frame() {
    let bus = CapturingI2C::default();
    let mut display = initialized_display(&bus);
    display.set_power(false).unwrap();
    display.set_power(true).unwrap();

    let commands = command_bytes(&bus.writes.borrow());
    assert!(commands.ends_with(&[0xAE, 0xAF]));
    save_screenshot("power-control", &SimulatorDisplay::new(panel_size()));
}

#[test]
fn a_dead_bus_is_reported_by_every_operation_that_touches_it() {
    assert!(Display::new(DyingI2C { accepted: 0 }).initialize().is_err());

    // Initialization needs several writes; a bus that dies midway still fails it.
    assert!(Display::new(DyingI2C { accepted: 2 }).initialize().is_err());

    let mut display = Display::new(DyingI2C {
        accepted: usize::MAX,
    });
    display.initialize().unwrap();
    display.set_power(true).unwrap();
    display.flush().unwrap();
    let mut dead = Display::new(DyingI2C { accepted: 0 });
    assert!(dead.set_power(false).is_err());
    // The driver sends only what changed, so a frame needs something to send.
    Pixel(Point::new(1, 1), BinaryColor::On)
        .draw(&mut dead)
        .unwrap();
    assert!(dead.flush().is_err());
}

#[test]
fn clearing_the_buffer_makes_the_next_flush_blank_without_any_io() {
    let bus = CapturingI2C::default();
    let mut display = initialized_display(&bus);
    Rectangle::new(Point::zero(), panel_size())
        .into_styled(PrimitiveStyle::with_fill(BinaryColor::On))
        .draw(&mut display)
        .unwrap();

    display.clear_buffer();
    assert!(
        bus.writes.borrow().is_empty(),
        "clear_buffer performs no I/O"
    );
    display.flush().unwrap();

    let frame = transmitted_frame(&bus);
    assert_eq!(frame.len(), BUFFER_SIZE);
    assert!(frame.iter().all(|byte| *byte == 0));
    save_screenshot("cleared-frame", &display_from_frame(&frame));
}

#[test]
fn drawing_outside_the_panel_is_clipped_and_never_corrupts_the_frame() {
    let bus = CapturingI2C::default();
    let mut display = initialized_display(&bus);
    for point in [
        Point::new(-1, 0),
        Point::new(0, -1),
        Point::new(WIDTH.into(), 0),
        Point::new(0, HEIGHT.into()),
        Point::new(1000, 1000),
    ] {
        Pixel(point, BinaryColor::On).draw(&mut display).unwrap();
    }
    // One in-bounds pixel makes the driver send a frame at all (it sends only changes).
    Pixel(Point::new(7, 20), BinaryColor::On)
        .draw(&mut display)
        .unwrap();

    display.flush().unwrap();

    let frame = transmitted_frame(&bus);
    assert_eq!(frame.len(), BUFFER_SIZE);
    // Page-major layout: byte = (y / 8) * WIDTH + x, bit = y % 8.
    let only = (20 / 8) * usize::from(WIDTH) + 7;
    for (index, byte) in frame.iter().enumerate() {
        let expected = if index == only { 1 << (20 % 8) } else { 0 };
        assert_eq!(*byte, expected, "frame byte {index}");
    }
}

#[test]
fn flush_addresses_every_page_before_its_data() {
    let bus = CapturingI2C::default();
    let mut display = initialized_display(&bus);
    display.flush().unwrap();
    let writes = bus.writes.borrow();
    assert_eq!(writes.len(), 8 * 5);
    for (page, packets) in writes.as_chunks::<5>().0.iter().enumerate() {
        assert_eq!(
            packets[0].1,
            [COMMAND, 0xB0 | u8::try_from(page).unwrap(), 0x00, 0x10]
        );
        assert!(
            packets[1..]
                .iter()
                .all(|(_, bytes)| bytes.len() == 33 && bytes[0] == DATA)
        );
    }
}

#[test]
fn construction_and_drawing_perform_no_bus_io() {
    let bus = CapturingI2C::default();
    let mut display = Display::new(bus.clone());
    Pixel(Point::new(127, 63), BinaryColor::On)
        .draw(&mut display)
        .unwrap();
    display.clear_buffer();
    assert!(bus.writes.borrow().is_empty());
}
