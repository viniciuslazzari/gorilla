from google_auth_oauthlib.flow import InstalledAppFlow, _WSGIRequestHandler, _RedirectWSGIApp
from google.auth.transport.requests import Request
import os
from pathlib import Path
import pickle
import re
import requests
import ssl
import webbrowser
import wsgiref.simple_server
import wsgiref.util
from urllib.parse import quote, urlparse, parse_qs
from .consts import AUTH_URL, CERT_FILE_PATH, KEY_FILE_PATH

DROPBOX_FOLDER_PATH = os.path.join(os.path.dirname(Path(os.path.realpath(__file__)).parent.parent), 'exec_engine/credentials/dropbox')
TOKEN_FILE = os.path.join(DROPBOX_FOLDER_PATH, 'token.pickle')

def main():
    creds = run_dropbox_flow()
    # Save the credentials for the next run
    if not os.path.isdir(DROPBOX_FOLDER_PATH):
        os.mkdir(DROPBOX_FOLDER_PATH)
    with open(TOKEN_FILE, 'wb') as token:
        pickle.dump(creds, token)

def run_dropbox_flow():
        host="localhost"
        bind_addr=None
        port=8000
        authorization_prompt_message="Please visit the link below to authorize: \n{url}"
        success_message="authorization success, you may close the window"
        open_browser=True,
        redirect_uri_trailing_slash=True
        timeout_seconds=None
        browser=None
        gorilla_user_scopes = 'user-read-private,user-read-email,playlist-modify-private,playlist-modify-public,user-top-read,user-read-recently-played'
 
        wsgi_app = _RedirectWSGIApp(success_message)
        # Fail fast if the address is occupied
        wsgiref.simple_server.WSGIServer.allow_reuse_address = False
        local_server = wsgiref.simple_server.make_server(
            bind_addr or host, port, wsgi_app, handler_class=_WSGIRequestHandler
        )

        sslctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        sslctx.check_hostname = False # If set to True, only the hostname that matches the certificate will be accepted
        sslctx.load_cert_chain(certfile=CERT_FILE_PATH, keyfile=KEY_FILE_PATH)

        local_server.socket = ssl.wrap_socket (local_server.socket,
            keyfile=KEY_FILE_PATH,
            certfile=CERT_FILE_PATH, server_side=True)

        redirect_uri_format = (
            "https://{}:{}/" if redirect_uri_trailing_slash else "https://{}:{}"
        )
        redirect_uri = redirect_uri_format.format(host, local_server.server_port)
        client_id = "8yht0rtna5qkk7v"
        auth_url = f"https://www.dropbox.com/oauth2/authorize?client_id={client_id}&response_type=code&redirect_uri={quote(redirect_uri)}"

        if open_browser:
            # if browser is None it defaults to default browser
            webbrowser.get(browser).open(auth_url, new=1, autoraise=True)

        if authorization_prompt_message:
            print(authorization_prompt_message.format(url=auth_url))

        local_server.timeout = timeout_seconds
        local_server.handle_request()

        # Note: using https here because oauthlib is very picky that
        # OAuth 2.0 should only occur over https.
        authorization_response = wsgi_app.last_request_uri.replace("http", "https")
        code = parse_qs(urlparse(authorization_response).query)['code'][0]
        local_server.server_close()
        data = {
            "service": "dropbox",
            "code": code,
            "redirect_uri": redirect_uri
        }
        r = requests.post(AUTH_URL, headers={}, json=data)
        return r.json()['token']

main()