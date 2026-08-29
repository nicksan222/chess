.PHONY: all cad check electronics gen regen-all rust

all: check

check:
	./tools/check

cad:
	./tools/cad

electronics:
	./tools/electronics

rust:
	./tools/rust

gen: cad electronics

regen-all: gen
