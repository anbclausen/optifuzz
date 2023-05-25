generate: 
	./util/clean_results.py generated_programs_dir \
	&& ./util/prepare_results.py generated_programs_dir
	$(MAKE) -C generator generate

generate-seeded:
	./util/clean_results.py generated_programs_dir \
	&& ./util/prepare_results.py generated_programs_dir
	$(MAKE) -C generator generate-seeded

inspect: 
	./util/prepare_results.py generated_programs_dir \
	&& ./util/clean_results.py flagged_programs_dir \
	&& ./util/prepare_results.py flagged_programs_dir
	$(MAKE) -C analysis inspect

fuzz:
	./util/prepare_results.py flagged_programs_dir \
	&& ./util/clean_results.py fuzzer_results_dir \
	&& ./util/prepare_results.py fuzzer_results_dir
	$(MAKE) -C fuzzer fuzz

latexgen: 
	./util/prepare_results.py fuzzer_results_dir
	$(MAKE) -C analysis latexgen

latexcompile:
	./util/clean_results.py report_dir \
	&& ./util/prepare_results.py report_dir
	$(MAKE) -C analysis latexcompile

generate-inspect: generate inspect

all: clean generate inspect fuzz latexgen latexcompile

run-experiments:
	@python experiments.py

.PHONY : clean
clean:
	$(MAKE) -C fuzzer clean
	$(MAKE) -C analysis clean