## dv_pyclient setup

### To create a new project
`cookiecutter https://github.com/audreyr/cookiecutter-pypackage.git`

After you create your project, change directory to the project and 
install dependencies. You should be in the folder that contains
requirements_dev.txt

### Setup
Make a virtual env in a directory outside the project dir
```
python -m venv /path-to-create-environment-in
source /path-to-create-environment-in/bin/activate
```
OR



Install deps
```
pip install -r requirements_dev.txt
make install
```

### Run locally
`make test`

### Build a release
Bump version if your are getting read to release a version. Note:  For development, just delete the `dist/*` 
```
bumpversion patch 
```
See bumpversion options

### Develop locally
`python setup.py develop`
Will install the package for development.  Open a python shell, import dv_pyclient and use


### Install a release locally
To install a release into your local environment use pip and point it to the build you want to install 
```python
make dist
pip install dist/dv_pyclient-XXX.tar.gz
```


### Upload to PyPi
twine upload --repository-url https://upload.pypi.org/legacy/ dist/*
user: sanjayvenkat2000
pass: askme



