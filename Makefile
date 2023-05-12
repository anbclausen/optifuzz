generate: 
	$(MAKE) -C generator clean
	$(MAKE) -C generator generate

generate-seeded:
	$(MAKE) -C generator clean
	$(MAKE) -C generator generate-seeded

inspect: 
	$(MAKE) -C analysis inspect

fuzz:
	$(MAKE) -C fuzzer fuzz

latexgen: 
	$(MAKE) -C analysis latexgen

latexcompile:
	$(MAKE) -C analysis latexcompile

generate-inspect: generate inspect

all: clean generate inspect fuzz latexgen latexcompile

.PHONY : clean
clean:
	$(MAKE) -C generator clean
	$(MAKE) -C analysis clean
	$(MAKE) -C fuzzer clean