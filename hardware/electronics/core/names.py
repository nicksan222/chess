"""Board coordinates, net names, and Pico GPIO assignment."""

from __future__ import annotations

FILES = "ABCDEFGH"
GRID = 2.54

ROW_PINS = ("2", "4", "5", "6", "7", "9", "10", "11")
COL_PINS = ("12", "14", "15", "16", "17", "19", "20", "21")
LED_DATA_PIN = "1"
BAT_ADC_PIN = "31"
PICO_3V3_PIN = "36"
PICO_5V_PIN = "39"
PICO_GND_PINS = ("3", "8", "13", "18", "23", "28", "33", "38")
PICO_UNUSED_PINS = ("22", "24", "25", "26", "27", "29", "30", "32", "34", "35", "37", "40")


def square(file_index: int, rank: int) -> str:
    return f"{FILES[file_index]}{rank + 1}"


def parse_square(name: str) -> tuple[int, int]:
    text = name.strip().upper()
    if len(text) < 2 or text[0] not in FILES:
        raise ValueError(f"invalid square {name!r}")
    rank = int(text[1:]) - 1
    if rank not in range(8):
        raise ValueError(f"invalid square {name!r}")
    return FILES.index(text[0]), rank


def led_chain_order() -> list[tuple[str, int, int]]:
    chain: list[tuple[str, int, int]] = []
    for index in range(64):
        rank = index // 8
        file_index = index % 8 if rank % 2 == 0 else 7 - (index % 8)
        chain.append((square(file_index, rank), file_index, rank))
    return chain
