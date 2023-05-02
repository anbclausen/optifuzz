build-gen:
	@cd generator; \
	dune build

generate:
	@cd generator; \
	mkdir -p generated; \
	dune exec generator 200 0

clean-gen:
	@rm generator/generated/*

inspect:
	@python3 analysis/assembly_inspection.py

clean-ins:
	@rm analysis/programs/*

move-gen:
	@mkdir -p analysis/programs
	@mv generator/generated/* analysis/programs

analyze: clean-ins generate move-gen inspect

generate-seeded:
	@cd generator; \
	mkdir -p generated; \
	dune exec generator 1 $(seed)