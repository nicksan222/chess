.PHONY: all cad check gen pcb python regen-all rust

all: check

check:
	./tools/check

cad:
	./tools/cad

pcb:
	./tools/pcb

python:
	./tools/python

rust:
	./tools/rust

gen: cad pcb

regen-all: gen
