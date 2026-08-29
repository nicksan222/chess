.PHONY: all cad check electronics gen regen-all

all: check

check:
	./tools/check

cad:
	./tools/cad

electronics:
	./tools/electronics

gen: cad electronics

regen-all: gen
