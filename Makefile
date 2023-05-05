move-generated:
	@mkdir -p analysis/programs
	@mv generator/generated/* analysis/programs

generate: 
	$(MAKE) -C analysis clean
	$(MAKE) -C generator generate

generate-seeded:
	$(MAKE) -C analysis clean
	$(MAKE) -C generator generate-seeded

inspect: 
	$(MAKE) -C analysis inspect

fuzz:
	$(MAKE) -C fuzzer fuzz

visualize: 
	$(MAKE) -C analysis visualize

generate-inspect: generate move-generated inspect

all: generate move-generated inspect fuzz visualize

.PHONY : clean
clean:
	$(MAKE) -C generator clean
	$(MAKE) -C analysis clean
	$(MAKE) -C fuzzer clean