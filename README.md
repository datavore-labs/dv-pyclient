
To Install

bumpversion patch

python setup.py sdist upload

python setup.py bdist_wheel upload

twine upload --repository-url https://upload.pypi.org/legacy/ dist/*
