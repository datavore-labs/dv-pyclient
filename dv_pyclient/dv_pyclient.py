"""Main module."""
import ndjson
import requests
import jwt


class Session:
    password = None
    username = None
    auth_domain = None
    api_domain = None
    user = None
    token = None

    def __init__(self, user_name, password, auth_domain, api_domain):
        self.username = user_name
        self.password = password
        self.auth_domain = auth_domain
        self.api_domain = api_domain

    def set_user(self, user):
        self.user = user

    def set_token(self, token):
        self.token = token


def _login(user_name=None, password=None, env_conf=None):
    if user_name is not None and password is not None and env_conf is not None:
        res = requests.get(env_conf['authDomain'], auth=(user_name, password))
        if res.status_code == 200:
            result_json = res.json()
            token = result_json['nextToken']
            user = jwt.decode(token, verify=False)
            print(f'Login success for {user}')
            result = Session(user_name, password, env_conf['authDomain'], env_conf['apiDomain'])
            result.set_user(user)
            result.set_token(token)
            return result
        else:
            raise Exception(res.status_code, res.content.decode('ascii'))
    else:
        print("Requires username, password and data_config from Datavore UI")


def _get_data(session: Session, step_info=None):
    """
    1. Make request using token.
    1a. if response is 200OK, return data as pandas frame
    1b. if response 401Unauthorized try login and return data frame
    1c. if response is any other
            throw exception
    Session that contains information to re-authenticate if required.
    :param session:
    :param step_info: Some JSON to post
    :return:
    """
    auth_header = {
        'Authorization': 'Bearer %s' % session.token,
        'Content-type': 'application/json',
    }

    res = requests.post(session.api_domain, json=step_info, headers=auth_header)
    if res.status_code == 200:
        payload = res.json(cls=ndjson.Decoder)
        return payload
    elif res.status_code == 401:
        session = _login(session)
        return _get_data(session, step_info)
    else:
        raise Exception(res.status_code, res.content.decode('ascii'))

