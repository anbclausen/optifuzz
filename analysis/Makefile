CONFIG_PATH='../config.json'
REPORT_DIR_KEY='report_dir'
LATEX_REPORT_OUTPUT_DIR = $(shell python3 -c "import os; import json; print(f'..{os.sep}..{os.sep}', end=''); print(json.load(open($(CONFIG_PATH)))[$(REPORT_DIR_KEY)], end=''); print(f'${os.sep}report.pdf')")

inspect:
	@./assembly_inspection.py

latexgen: clean
	@./latex_generator.py

latexcompile:
	@cd latex \
	&& pdflatex -halt-on-error master.tex 1>/dev/null 2>&1 \
	&& cp master.pdf $(LATEX_REPORT_OUTPUT_DIR)

clean-latex:
	@$(RM) latex/generated_latex/prog*

.PHONY : clean
clean: clean-latex