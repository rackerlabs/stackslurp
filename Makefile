init:
	pip install -r requirements.txt

test:
	py.test

coverage:
	py.test --verbose --cov-report term --cov=stackslurp tests/test_stackslurp.py
