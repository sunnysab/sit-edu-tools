import base64
import re
from typing import Tuple

import requests
import rsa

from .base import BaseSession
from src.global_config import URL, REQUEST_OPTION


def encrypt_in_rsa(message: bytes, public_key: bytes, exponent: bytes) -> str:
    public_key: int = int.from_bytes(public_key, byteorder='big')
    exponent: int = int.from_bytes(exponent, byteorder='big')

    encrypted_passwd: bytes = rsa.encrypt(message, rsa.PublicKey(n=public_key, e=exponent))
    return base64.b64encode(encrypted_passwd).decode('utf-8')


class PasswordSession(BaseSession):

    def __init__(self, user: str = None, passwd: str = None):
        super().__init__(user, passwd)

    def __get_ras_public_key(self) -> Tuple[bytes, bytes]:
        """
        Request to the system with the cookie we got before, and get the RSA public key.
        :return: RSA public key for encrypting the user password.
        """
        resp_obj = self._session.get(URL.RSA_PUBLIC_KEY, headers=REQUEST_OPTION).json()
        return base64.b64decode(resp_obj['modulus']), base64.b64decode(resp_obj['exponent'])

    def __get_csrf_token(self, login_page: str) -> str:
        """
        Get csrftoken field from the login front page by regex expression, for re is much more faster than beautifulsoup
        :param login_page: the login page in text, where we input user and password
        :return: the value of 'csrftoken' field
        """
        token_tag = re.compile(r'<input type="hidden" id="csrftoken" name="csrftoken" value="(.*)"/>')
        return token_tag.search(login_page).group(1)

    def __get_err_message(self, content: str) -> str:
        """
        Parse the error page and get the error message prompt.
        :param content: login failed page in text
        :return: the error message we got.
        """
        from bs4 import BeautifulSoup

        page = BeautifulSoup(content, 'html5lib')
        err_node = page.select(r'div#home.tab-pane.in.active p#tips.bg_danger.sl_danger')[0]
        return err_node.text.strip()

    def login(self) -> str:
        """
        Login the system through simulating a browser
        :return: If the login succeeds, the function will return a User object with the requests session.
                Otherwise, it will return a string with the error message provided by the page.
        """
        self._session = requests.Session()

        # Get login page for the first cookie
        login_page = self._session.get(URL.HOME, headers=REQUEST_OPTION)

        # Get RAS public key to encode the raw password
        public_key, exponent = self.__get_ras_public_key()
        encrypted_passwd: str = encrypt_in_rsa(self._passwd.encode('utf-8'), public_key, exponent)

        form_to_post = {
            'csrftoken': self.__get_csrf_token(login_page.text),
            'language': 'zh_CN',
            'yhm': self._user,
            'mm': encrypted_passwd
        }
        # If the login process succeeds, turn to other page (It may be not sure.
        # But for the sake of simplicity, I decided to decide whether to fail
        r = self._session.post(URL.LOGIN, data=form_to_post, headers=REQUEST_OPTION)
        if r.url.startswith(URL.LOGIN):
            return self.__get_err_message(r.text)
        else:
            self._login_flag = True
            return 'success'
