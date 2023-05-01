build-generator:
	@cd generator; \
	dune build

exec-generator:
	@cd generator; \
	mkdir -p generated; \
	dune exec generator 50

clean-generated:
	@cd generator; \
	cd generated; \
	rm *

exec-assembly-inspection:
	@cd analysis; \
	python assembly_inspection.py

clean-inspected:
	@cd analysis; \
	cd programs; \
	rm *

move-generated:
	@cd generator; \
	cd generated; \
	mv * ../../analysis/programs

analyze: clean-inspected exec-generator move-generated exec-assembly-inspection
