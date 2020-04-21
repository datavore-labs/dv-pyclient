'''login and session management'''

import getpass
import requests
import jwt

class Session:
    '''A Datavore session object. Returned from login.'''
    user_name = None # String
    user = None # Dict
    token = None # String
    env_conf = None # { authDomain: String }

    def __init__(self, user_name, env_conf):
        self.user_name = user_name
        self.env_conf = env_conf

    def set_user(self, user):
        self.user = user

    def set_token(self, token):
        self.token = token

def login(env_conf=None, user_name=None, password=None):
    '''
    Log in to Datavore. Returns a Session object.

    Arguments:
    env_conf: { authDomain: String } - The environment to log in to
    user_name: String - User to log in as. If not provided, will be prompted.
    password: String? - Optional password. If not provided, will be prompted.
    '''

    if env_conf == None or not 'authDomain' in env_conf:
        raise Exception('Invalid env_conf. Requires { authDomain: String }')

    if user_name == None:
        user_name = input('Login user name: ')

    if password == None:
        password = getpass.getpass(prompt=f'Enter password for user {user_name} :')

    if user_name != None and password != None and env_conf != None and 'authDomain' in env_conf:
        res = requests.get(
            f'{env_conf["authDomain"]}/login', auth=(user_name, password)
        )
        if res.status_code == 200:
            result_json = res.json()
            token = result_json['nextToken']
            user = jwt.decode(token, verify=False)
            print(f'Login success for {user["fullName"]}\n')
            result = Session(user_name, env_conf)
            result.set_user(user)
            result.set_token(token)
            return result
        else:
            raise Exception(res.status_code, res.content.decode('ascii'))
    else:
        print('Requires username, password and data_config from Datavore UI')
