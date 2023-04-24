build-generator:
	@cd generator; \
	dune build

exec-generator:
	@cd generator; \
	mkdir -p generated; \
	dune exec generator
