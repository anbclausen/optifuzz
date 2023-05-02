build-gen:
	@cd generator; \
	dune build

generate:
	@cd generator; \
	mkdir -p generated; \
	dune exec generator 200 0

clean-gen:
	@cd generator; \
	cd generated; \
	rm *

inspect:
	@cd analysis; \
	python assembly_inspection.py

clean-ins:
	@cd analysis; \
	cd programs; \
	rm *

move-gen:
	@cd generator; \
	cd generated; \
	mv * ../../analysis/programs

analyze: clean-ins generate move-gen inspect

generate-seeded:
	@cd generator; \
	mkdir -p generated; \
	dune exec generator 1 $(seed)