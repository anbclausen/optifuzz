CONFIG_PATH="../config.json"
GENERATED_PATH = $(shell python3 -c "import json; print(json.load(open('$(CONFIG_PATH)'))['generated_programs_dir'])")

build:
	dune build

generate:
	dune exec generator $(GENERATED_PATH) $(pn) 0 $(md)

generate-seeded:
	dune exec generator $(GENERATED_PATH) 1 $(s) $(md)