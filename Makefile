.PHONY: all cad check electronics gen pcb regen-all rust

all: check

check:
	./tools/check

cad:
	./tools/cad

electronics:
	./tools/electronics

pcb:
	./tools/pcb

rust:
	./tools/rust

# Electronics first: the schematic publishes the netlist the board layout reads.
gen: cad electronics pcb

regen-all: gen
