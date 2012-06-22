import requests
import urllib
import urlparse

try:
  import json
except ImportError:
  import simplejson as json


class FBClient(object):

  auth_uri = 'https://www.facebook.com/dialog/oauth'
  access_token_uri = 'https://graph.facebook.com/oauth/access_token'
  graph_api_uri = 'https://graph.facebook.com'
  # Pre-set client_id and client_secret so we can
  # instantiate FBClient without them and have them loaded later
  client_id = None
  client_secret = None
  # Pre-set the other attributes as well
  redirect_uri = ''
  scope = ''
  access_token = ''

  # We won't be needing the __init__ method as we have
  # set the default attributes in class already. Object
  # constructor still works by passing in an expanded dict.

  def _check_required_attributes(self, *args):
    """Check required attributes in a function call

    * args: string list of attributes
    """
    required_attrs = list(args)
    # Always check for client_id and client_secret
    required_attrs.append('client_id')
    required_attrs.append('client_secret')
    for attr in required_attrs:
      if not getattr(self, attr):
        raise Exception("%s attribute is required." % (attr))

  def get_auth_url(self, scope='', redirect_uri='', state=''):
    """Step 1: Redirect user to page for your application authorization
    """
    # Check required attributes (client_id, and client_secret)
    self._check_required_attributes()

    params = {
        'client_id': self.client_id,
        'redirect_uri': redirect_uri or self.redirect_uri,
        'scope': scope or self.scope,
      }
    if state:
      params['state'] = state
    return self.auth_uri + '?' + urllib.urlencode(params)

  def get_access_token(self, code):
    """Step 2: Get the access token

    * code (string): This will be passed in to the controller/view where the
        redirect_uri resolves to.
    """
    # Check required attributes (client_id, and client_secret)
    self._check_required_attributes()

    params = {
        'client_id': self.client_id,
        'redirect_uri': self.redirect_uri,
        'client_secret': self.client_secret,
        'code': code,
      }

    response = requests.get(self.access_token_uri, params=params)

    if response.ok:
      parsed_response = dict(urlparse.parse_qsl(response.content))
      access_token = self.access_token = parsed_response['access_token']
      return access_token

    else:
      try:
        error = json.loads(response.content).get('error')
        if error:
          error_type = error.get('type')
          error_message = error.get('message')
          if error_type and error_message:
            raise Exception('%s: %s' % (error_type, error_message))
      except ValueError: # Invalid JSON
        pass
      except AttributeError: # Not a dict
        pass
      raise Exception("An unknown error has occurred: %s" % response.content)

  def request(self, uri, method='get', **req_kwargs):

    if self.access_token:
      method = method.lower()

      if method in ('get', 'options'):
        req_kwargs['allow_redirects'] = True
      elif method == 'head':
        req_kwargs['allow_redirects'] = False

      params = req_kwargs.setdefault('params', {})
      params['access_token'] = self.access_token

      # TODO: Handle HTTP errors
      response = requests.request(method, uri, **req_kwargs)

      return json.loads(response.content)

    else:
      raise Exception('Not yet authorized.')

  def graph_request(self, path, *args, **kwargs):
    """Step 3: We can now make the facebook api requests. :)
    """

    path = path.lstrip('/')
    uri = '%s/%s' % (self.graph_api_uri, path)
    return self.request(uri, *args, **kwargs)
