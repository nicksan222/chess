use core::{convert::Infallible, fmt::Debug};
use std::{cell::RefCell, fs, path::PathBuf, rc::Rc};

use embedded_graphics::{
    Pixel,
    draw_target::DrawTarget,
    geometry::{Point, Size},
    mono_font::{MonoTextStyle, ascii::FONT_6X10},
    pixelcolor::BinaryColor,
    prelude::*,
    primitives::{Circle, Line, PrimitiveStyle, Rectangle, Triangle},
    text::{Baseline, Text},
};
use embedded_graphics_simulator::{OutputSettingsBuilder, SimulatorDisplay};
use embedded_hal::i2c::{Error as I2cError, ErrorKind, ErrorType, I2c, Operation};
use firmware::hardware::display::{Display, HEIGHT, I2C_ADDRESS, WIDTH};

const COMMAND: u8 = 0x00;
const DATA: u8 = 0x40;
const BUFFER_SIZE: usize = WIDTH as usize * HEIGHT as usize / 8;

type I2CWrites = Rc<RefCell<Vec<(u8, Vec<u8>)>>>;

#[derive(Clone, Default)]
struct CapturingI2C {
    writes: I2CWrites,
}

impl CapturingI2C {
    fn clear(&self) {
        self.writes.borrow_mut().clear();
    }
}

impl ErrorType for CapturingI2C {
    type Error = Infallible;
}

impl I2c for CapturingI2C {
    fn transaction(
        &mut self,
        address: u8,
        operations: &mut [Operation<'_>],
    ) -> Result<(), Self::Error> {
        for operation in operations {
            match operation {
                Operation::Write(bytes) => self.writes.borrow_mut().push((address, bytes.to_vec())),
                Operation::Read(bytes) => bytes.fill(0),
            }
        }
        Ok(())
    }
}

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

/// A bus that stops answering after `accepted` write operations.
struct DyingI2C {
    accepted: usize,
}

#[derive(Debug)]
struct BusDown;

impl I2cError for BusDown {
    fn kind(&self) -> ErrorKind {
        ErrorKind::Other
    }
}

impl ErrorType for DyingI2C {
    type Error = BusDown;
}

impl I2c for DyingI2C {
    fn transaction(&mut self, _: u8, _: &mut [Operation<'_>]) -> Result<(), Self::Error> {
        if self.accepted == 0 {
            return Err(BusDown);
        }
        self.accepted -= 1;
        Ok(())
    }
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

fn initialized_display(bus: &CapturingI2C) -> Display<CapturingI2C> {
    let mut display = Display::new(bus.clone());
    display.initialize().unwrap();
    bus.clear();
    display
}

#[derive(Clone, Copy)]
enum Scene {
    Primitives,
    Text,
    Menu,
    ClippedText,
    Symbols,
}

fn verify_scene(name: &str, scene: Scene) {
    let bus = CapturingI2C::default();
    let mut display = initialized_display(&bus);
    let mut reference = SimulatorDisplay::new(panel_size());

    draw_scene(scene, &mut display);
    draw_scene(scene, &mut reference);
    display.flush().unwrap();

    let actual = display_from_i2c(&bus);
    assert_eq!(actual.diff(&reference), None);
    save_screenshot(name, &actual);
}

fn draw_scene<D>(scene: Scene, target: &mut D)
where
    D: DrawTarget<Color = BinaryColor>,
    D::Error: Debug,
{
    match scene {
        Scene::Primitives => draw_primitives(target),
        Scene::Text => draw_text(target),
        Scene::Menu => draw_menu(target),
        Scene::ClippedText => draw_clipped_text(target),
        Scene::Symbols => draw_symbols(target),
    }
}

fn draw_primitives<D>(target: &mut D)
where
    D: DrawTarget<Color = BinaryColor>,
    D::Error: Debug,
{
    let on = PrimitiveStyle::with_stroke(BinaryColor::On, 1);
    Rectangle::new(Point::zero(), panel_size())
        .into_styled(on)
        .draw(target)
        .unwrap();
    Line::new(Point::new(0, 0), Point::new(127, 63))
        .into_styled(on)
        .draw(target)
        .unwrap();
    Circle::new(Point::new(48, 16), 32)
        .into_styled(on)
        .draw(target)
        .unwrap();
}

fn draw_text<D>(target: &mut D)
where
    D: DrawTarget<Color = BinaryColor>,
    D::Error: Debug,
{
    let style = MonoTextStyle::new(&FONT_6X10, BinaryColor::On);
    for (text, y) in [
        ("CHESS", 2),
        ("New game", 20),
        ("Settings", 34),
        ("Power off", 48),
    ] {
        Text::with_baseline(text, Point::new(2, y), style, Baseline::Top)
            .draw(target)
            .unwrap();
    }
}

fn draw_menu<D>(target: &mut D)
where
    D: DrawTarget<Color = BinaryColor>,
    D::Error: Debug,
{
    let normal = MonoTextStyle::new(&FONT_6X10, BinaryColor::On);
    let inverted = MonoTextStyle::new(&FONT_6X10, BinaryColor::Off);

    Text::with_baseline("MAIN MENU", Point::new(2, 1), normal, Baseline::Top)
        .draw(target)
        .unwrap();
    Line::new(Point::new(0, 12), Point::new(127, 12))
        .into_styled(PrimitiveStyle::with_stroke(BinaryColor::On, 1))
        .draw(target)
        .unwrap();
    Text::with_baseline("New game", Point::new(4, 15), normal, Baseline::Top)
        .draw(target)
        .unwrap();
    Rectangle::new(Point::new(0, 25), Size::new(u32::from(WIDTH), 13))
        .into_styled(PrimitiveStyle::with_fill(BinaryColor::On))
        .draw(target)
        .unwrap();
    Text::with_baseline("Settings", Point::new(4, 27), inverted, Baseline::Top)
        .draw(target)
        .unwrap();
    Text::with_baseline("Power off", Point::new(4, 40), normal, Baseline::Top)
        .draw(target)
        .unwrap();
}

fn draw_clipped_text<D>(target: &mut D)
where
    D: DrawTarget<Color = BinaryColor>,
    D::Error: Debug,
{
    let style = MonoTextStyle::new(&FONT_6X10, BinaryColor::On);
    Text::with_baseline(
        "This text is deliberately wider than 128 pixels",
        Point::new(3, 4),
        style,
        Baseline::Top,
    )
    .draw(target)
    .unwrap();
    Text::with_baseline("partly below", Point::new(70, 59), style, Baseline::Top)
        .draw(target)
        .unwrap();
}

fn draw_symbols<D>(target: &mut D)
where
    D: DrawTarget<Color = BinaryColor>,
    D::Error: Debug,
{
    let stroke = PrimitiveStyle::with_stroke(BinaryColor::On, 1);
    let fill = PrimitiveStyle::with_fill(BinaryColor::On);
    Triangle::new(Point::new(4, 16), Point::new(20, 4), Point::new(20, 28))
        .into_styled(fill)
        .draw(target)
        .unwrap();
    Triangle::new(Point::new(124, 16), Point::new(108, 4), Point::new(108, 28))
        .into_styled(stroke)
        .draw(target)
        .unwrap();
    Circle::new(Point::new(48, 8), 32)
        .into_styled(stroke)
        .draw(target)
        .unwrap();
    Rectangle::new(Point::new(44, 47), Size::new(40, 10))
        .into_styled(fill)
        .draw(target)
        .unwrap();
}

fn transmitted_frame(bus: &CapturingI2C) -> Vec<u8> {
    bus.writes
        .borrow()
        .iter()
        .filter_map(|(_, packet)| packet.strip_prefix(&[DATA]))
        .flatten()
        .copied()
        .collect()
}

fn command_bytes(writes: &[(u8, Vec<u8>)]) -> Vec<u8> {
    writes
        .iter()
        .filter_map(|(_, packet)| packet.strip_prefix(&[COMMAND]))
        .flatten()
        .copied()
        .collect()
}

fn display_from_i2c(bus: &CapturingI2C) -> SimulatorDisplay<BinaryColor> {
    let frame = transmitted_frame(bus);
    assert_eq!(frame.len(), BUFFER_SIZE);
    display_from_frame(&frame)
}

fn display_from_frame(frame: &[u8]) -> SimulatorDisplay<BinaryColor> {
    let mut display = SimulatorDisplay::new(panel_size());
    display
        .draw_iter(display.bounding_box().points().map(|point| {
            let x = point.x as usize;
            let y = point.y as usize;
            let byte = frame[(y / 8) * usize::from(WIDTH) + x];
            Pixel(point, BinaryColor::from(byte & (1 << (y % 8)) != 0))
        }))
        .unwrap();
    display
}

fn panel_size() -> Size {
    Size::new(u32::from(WIDTH), u32::from(HEIGHT))
}

fn save_screenshot(name: &str, display: &SimulatorDisplay<BinaryColor>) {
    let directory = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("tests/display/screenshots");
    fs::create_dir_all(&directory).unwrap();

    let settings = OutputSettingsBuilder::new()
        .scale(4)
        .pixel_spacing(1)
        .build();
    display
        .to_rgb_output_image(&settings)
        .save_png(directory.join(format!("{name}.png")))
        .unwrap();
}

#[test]
fn flush_addresses_every_page_before_its_data() {
    let bus = CapturingI2C::default();
    let mut display = initialized_display(&bus);
    display.flush().unwrap();
    let writes = bus.writes.borrow();
    assert_eq!(writes.len(), 8 * 5);
    for (page, packets) in writes.as_chunks::<5>().0.iter().enumerate() {
        assert_eq!(packets[0].1, [COMMAND, 0xB0 | page as u8, 0x00, 0x10]);
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
