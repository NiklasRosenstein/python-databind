
ARGS ?= --mypy

test:
	pytest $(ARGS) databind.binary/src
	pytest $(ARGS) databind.core/src
	pytest $(ARGS) databind.json/src
	pytest $(ARGS) databind.mypy/src
	pytest $(ARGS) databind.zaml/src
