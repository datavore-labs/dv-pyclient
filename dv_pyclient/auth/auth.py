'''login and session management'''

import requests
import jwt

class Session:
    '''A Datavore session object. Returned from login.'''
    user_name = None # String
    user = None # Dict
    token = None # String
    env_conf = None # { authDomain: String, execDomain: String }

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

    :param env_conf: { authDomain: String } - The environment to log in to
    :param user_name: String - User to log in as. If not provided, will be prompted.
    :param password: String? - Optional password. If not provided, will be prompted.
    :returns: Session object if successful.
    :raises Exception: On bad env_conf and bad response.
    '''

    if env_conf == None or not 'authDomain' in env_conf:
        raise Exception('Invalid env_conf. Requires { authDomain: String }')

    if user_name == None:
        raise Exception('Invalid User name. Requires')

    if password == None:
        raise Exception('Invalid env_conf. Requires')

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

