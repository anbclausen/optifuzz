move-generated:
	@mkdir -p analysis/programs
	@mv generator/generated/* analysis/programs

generate: 
	$(MAKE) -C analysis clean
	$(MAKE) -C generator generate

inspect: move-generated
	$(MAKE) -C analysis inspect

fuzz:
	$(MAKE) -C fuzzer fuzz

visualize: 
	@cd fuzzer; \
	./data_analysis.py

generate-inspect: generate inspect

all: generate inspect fuzz visualize

.PHONY : clean
clean:
	$(MAKE) -C generator clean
	$(MAKE) -C analysis clean
	$(MAKE) -C fuzzer clean