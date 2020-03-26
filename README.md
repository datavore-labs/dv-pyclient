## dv_pyclient setup

### To create a new project
`cookiecutter https://github.com/audreyr/cookiecutter-pypackage.git`

After you create your project, change directory to the project and 
install dependencies. You should be in the folder that contains
requirements_dev.txt

`pip install -r requirements_dev.txt`

### Run test locally
`make test`

Run make to see options

### Build a release
Bump version if your are getting read to release a version. Note:  For development, just delete the `dist/*` 
```
rm -rf dist/*
bumpversion patch
python setup.py sdist
python setup.py bdist_wheel
```

### Test release
`tok`


### Install a release locally
To install a release into your local environment use pip and point it to the build you want to install 
```python
pip install dist/dv_pyclient-XXX.tar.gz
```


### Upload to PyPi
twine upload --repository-url https://upload.pypi.org/legacy/ dist/*
user: sanjayvenkat2000
pass: askme



