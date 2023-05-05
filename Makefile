build-gen:
	@cd generator; \
	dune build

generate:
	@cd generator; \
	mkdir -p generated; \
	dune exec generator 200 0

clean-gen:
	@rm generator/generated/* 1>/dev/null 2>&1; true

inspect:
	@cd analysis; \
	python3 assembly_inspection.py

clean-ins:
	@rm analysis/programs/* 1>/dev/null 2>&1; true

clean-flagged:
	@rm analysis/flagged/* 1>/dev/null 2>&1; true

move-gen:
	@mkdir -p analysis/programs
	@mv generator/generated/* analysis/programs

analyze: clean-ins clean-flagged generate move-gen inspect

.PHONY : clean
clean: clean-ins clean-gen clean-flagged
	$(MAKE) -C fuzzer clean

fuzz:
	$(MAKE) -C fuzzer fuzz

generate-seeded:
	@cd generator; \
	mkdir -p generated; \
	dune exec generator 1 $(seed)

visualize: 
	@cd fuzzer; \
	./data_analysis.py

all: analyze fuzz visualize