run:
	python main.py

output.xml:
	python main.py

verif: output.xml
	/home/gabriel/uppaal64-4.1.20-stratego-7/bin-Linux/verifyta output.xml

tag:
	ctags -R .

black:
	black .

.PHONY: tag black run verif
