//! Reference scenes drawn both to the driver and to a simulator display.

use core::fmt::Debug;

use embedded_graphics::{
    geometry::{Point, Size},
    mono_font::{MonoTextStyle, ascii::FONT_6X10},
    pixelcolor::BinaryColor,
    prelude::*,
    primitives::{Circle, Line, PrimitiveStyle, Rectangle, Triangle},
    text::{Baseline, Text},
};
use embedded_graphics_simulator::SimulatorDisplay;
use firmware::hardware::display::WIDTH;

use crate::{
    bus::CapturingI2C,
    frame::{display_from_i2c, initialized_display, panel_size, save_screenshot},
};

#[derive(Clone, Copy)]
pub(crate) enum Scene {
    Primitives,
    Text,
    Menu,
    ClippedText,
    Symbols,
}

pub(crate) fn verify_scene(name: &str, scene: Scene) {
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

pub(crate) fn draw_scene<D>(scene: Scene, target: &mut D)
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

pub(crate) fn draw_primitives<D>(target: &mut D)
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

pub(crate) fn draw_text<D>(target: &mut D)
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

pub(crate) fn draw_menu<D>(target: &mut D)
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

pub(crate) fn draw_clipped_text<D>(target: &mut D)
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

pub(crate) fn draw_symbols<D>(target: &mut D)
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
