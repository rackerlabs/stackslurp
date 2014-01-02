init:
	pip install -r requirements.txt

test:
	py.test

coverage:
	py.test --verbose --cov-report term --cov=stackslurp tests/test_stackslurp.py

coverage_html:
	py.test --verbose --cov-report=html --cov=stackslurp tests/test_stackslurp.py
