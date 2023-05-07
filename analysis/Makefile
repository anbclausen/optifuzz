inspect:
	@./assembly_inspection.py $(c)

visualize:
	@./visualize.py

latexgen:
	@./latex_generator.py

clean-programs:
	@rm programs/* 1>/dev/null 2>&1; true

clean-flagged:
	@rm flagged/* 1>/dev/null 2>&1; true

clean-latex:
	@rm latex/generated_latex/prog* 1>/dev/null 2>&1; true

.PHONY : clean
clean: clean-programs clean-flagged clean-latex