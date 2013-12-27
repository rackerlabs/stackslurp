init:
	pip install -r requirements.txt

test:
	py.test

coverage:
	py.test --verbose --cov-report term --cov=stackslurp test_stackslurp.py
