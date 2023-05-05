build:
	dune build

generate:
	mkdir -p generated; \
	dune exec generator 200 0

generate-seeded:
	mkdir -p generated; \
	dune exec generator 1 $(seed)

.PHONY : clean
clean:
	@rm generated/* 1>/dev/null 2>&1; true