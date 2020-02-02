
To Install

bumpversion patch

python setup.py sdist

python setup.py bdist_wheel

twine upload --repository-url https://upload.pypi.org/legacy/ dist/*
