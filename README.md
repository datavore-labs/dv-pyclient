
To Install

bumpversion patch

python setup.py sdist

python setup.py bdist_wheel

rm -rf dist/*

twine upload --repository-url https://upload.pypi.org/legacy/ dist/*

See: https://gist.github.com/audreyr/5990987 for pypi release checklist
