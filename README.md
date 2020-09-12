# dv-py_client
Provides a lightweight client to communicate with Datavore server.  The client support download to pandas Dataframe, and a grpc endpoint to publish Datasource to Datavore Server.

## Design
### Code Organization

**_dv_pyclient.auth_** : Handle authenticating to the Datavore server.  Authentication is via username and password.  The client creates a session object that is used by other packages to fetch  or publish data

**_dv_pyclient.client** : Handle the fetch data from server and transform to Dataframe function. It also the user libs to publish data to Datavore Server

**_dv_pyclinet.<other_packages>_** :  Supporting code that implements the grpc protocol to move data into and out of Datavore Server.

### Coding Style
Ugh!. Python best practices we know.  We are not expert python developers!!!

## Development
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

### Prerequisites
* Install Git
* Install your favorite Python virtual env or Conda to avoid dependency hell

### Getting Started
* Clone this repo
* Make a virtual env in a directory outside the project dir
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
* Develop locally
`python setup.py develop`

### Deployment
* Install [bumpversion](https://pypi.org/project/bumpversion/)
* Bump version if your are getting read to release a version. Note:  For development, just delete the `dist/*` 
```
bumpversion patch 
```
See bumpversion options

* To install a release into your local environment use pip and point it to the build you want to install 
```python
make dist
pip install dist/dv_pyclient-XXX.tar.gz
```
* Upload to PyPi
```
twine upload --repository-url https://upload.pypi.org/legacy/ dist/*
user: sanjayvenkat2000
pass: asksanjay
```

# Onboarding project
