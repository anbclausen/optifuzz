inspect: clean-flagged
	@./assembly_inspection.py

latexgen:
	@./latex_generator.py

latexcompile:
	@cd latex; pdflatex master.tex 1>/dev/null 2>&1; true

clean-programs:
	@$(RM) programs/*

clean-flagged:
	@$(RM) flagged/*

clean-latex:
	@$(RM) latex/generated_latex/prog* 

.PHONY : clean
clean: clean-programs clean-flagged clean-latex
