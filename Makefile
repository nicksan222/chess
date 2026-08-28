.PHONY: all cad cad-regenerate check regen-all

all: check

check:
	./tools/check

cad cad-regenerate:
	./tools/generate-cad

regen-all: cad
