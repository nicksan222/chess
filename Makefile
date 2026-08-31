.PHONY: all cad check gen pcb regen-all rust

all: check

check:
	./tools/check

cad:
	./tools/cad

pcb:
	./tools/pcb

rust:
	./tools/rust

gen: cad pcb

regen-all: gen
