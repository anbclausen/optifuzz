inspect: clean-flagged
	@./assembly_inspection.py

latexgen:
	@./latex_generator.py

latexcompile:
	@cd latex && pdflatex -halt-on-error master.tex 1>/dev/null 2>&1

clean-programs:
	@rm programs/* 1>/dev/null 2>&1

clean-flagged:
	@rm flagged/* 1>/dev/null 2>&1

clean-latex:
	@rm latex/generated_latex/prog* 1>/dev/null 2>&1

.PHONY : clean
clean: clean-programs clean-flagged clean-latex
