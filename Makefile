init:
	pip install pipenv
	pipenv install
	pipenv install --dev

test:
	$(shell export PYTHONPATH=$PYTHONPATH:$(pwd))
	pipenv run py.test tests
	pipenv run py.test --cov=./
