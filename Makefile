.PHONY: all cad cad-check check electronics electronics-check gen regen-all setup

all: check

check:
	./tools/check

setup:
	./tools/cad setup
	./tools/electronics setup

cad:
	./tools/cad build

cad-check:
	./tools/cad check

electronics:
	./tools/electronics build

electronics-check:
	./tools/electronics check

gen: cad electronics

regen-all: gen
