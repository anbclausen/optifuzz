build-generator:
	@cd generator; \
	dune build

exec-generator:
	@cd generator; \
	dune exec generator
