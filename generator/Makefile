build:
	dune build

generate:
	mkdir -p generated; \
	dune exec generator $(pn) 0 $(md)

generate-seeded:
	mkdir -p generated; \
	dune exec generator 1 $(s) $(md)

.PHONY : clean
clean:
	@$(RM) -r generated 1>/dev/null 2>&1; true
	@mkdir generated