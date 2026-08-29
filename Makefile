.PHONY: all cad cad-regenerate check electronics electronics-check gen regen-all

all: check

check:
	./tools/check

cad cad-regenerate:
	./tools/generate-cad

electronics:
	./tools/electronics generate

electronics-check:
	./tools/electronics check

gen: cad electronics

regen-all: gen
