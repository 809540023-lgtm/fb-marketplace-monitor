PYTHON ?= python3

.PHONY: install run api compile

install:
	$(PYTHON) -m pip install -r requirements.txt

run:
	$(PYTHON) main.py --query "$(QUERY)"

api:
	uvicorn api:app --reload

compile:
	$(PYTHON) -m compileall .
