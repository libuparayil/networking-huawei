# Copyright (c) 2016 OpenStack Foundation.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from networking_huawei._i18n import _LE
from oslo_config import cfg
from oslo_log import log as logging
from oslo_serialization import jsonutils
import requests
import traceback

LOG = logging.getLogger(__name__)


class RestClient(object):
    # Initialized and reads the configuration file base parameters
    def __init__(self):
        self.username = cfg.CONF.ml2_huawei_ac.username
        self.password = cfg.CONF.ml2_huawei_ac.password
        self.timeout = float(cfg.CONF.ml2_huawei_ac.request_timeout)
        self.timeout_retry = int(cfg.CONF.ml2_huawei_ac.timeout_retry)
        self.token_retry = int(cfg.CONF.ml2_huawei_ac.token_retry)
        self.ac_simulate = cfg.CONF.ml2_huawei_ac.simulator

    # Send the JSON message to the controller
    def send(self, host, port, method, url,
             resrc_id, body, callback=None):

        result = {}

        if method.upper() == 'GET' or method.upper() == 'DELETE' \
                or method.upper() == 'PUT':
            url = url + "/" + resrc_id
        else:
            pass

        params = jsonutils.dumps(body)
        headers = {"Content-type": "application/json",
                   "Accept": "application/json"}

        LOG.debug('Send the request information, method: %s, url: %s, '
                  'headers: %s, data:%s', method, url, headers, params)

        if self.ac_simulate:
            result['response'] = 'OK'
            result['status'] = requests.codes.ok
            result['errorCode'] = '0'
            result['reason'] = 'Good'
            return result

        ret = self.process_request(method, url, headers, params)

        if ("Timeout Exceptions" == ret) or ("Exceptions" == ret):
            LOG.error(_LE("Request to AC failed, ret: %s"), ret)
            result['response'] = None
            result['status'] = -1
            result['errorCode'] = None
            result['reason'] = None
            return result

        LOG.debug("AC request result, status_code: %s, content: %s, "
                  "headers: %s", ret.status_code,
                  ret.content.decode('utf-8'), ret.headers)

        res_code = int(ret.status_code)
        res_content = ret.content.decode('utf-8')
        try:
            if requests.codes.ok <= res_code < requests.codes.multiple_choices:
                LOG.debug('AC process request successfully.')
                res = self.fix_json(res_content)
                LOG.debug("send: response body is %s", res)
                if not res_content.strip():
                    result['response'] = None
                    result['status'] = ret.status_code
                    result['errorCode'] = None
                    result['reason'] = None
                else:
                    res1 = jsonutils.loads(res)
                    result['response'] = res1['result']
                    result['status'] = ret.status_code
                    result['errorCode'] = res1['errorCode']
                    result['reason'] = res1['errorMsg']
            else:
                LOG.error(_LE('AC process request failed.'))
                if self.token_retry > 0 and \
                   requests.codes.unauthorized == res_code:
                    LOG.debug('AC:TokenId expired, get again')
                    self.token_retry -= 1
                    (res_code, res_content) = self.send(host, port, method,
                                                        url,
                                                        resrc_id, body,
                                                        callback)
                else:
                    result['response'] = None
                    result['status'] = ret.status_code
                    result['errorCode'] = None
                    result['reason'] = None
        except Exception:
            result['response'] = ''
            result['status'] = ret.status_code
            result['reason'] = -1
            result['errorCode'] = -1
            raise Exception

        if callback is not None:
            callback(result['errorCode'], result['reason'], result['status'],
                     result['response'])
        else:
            LOG.debug("call back is null")

        return result

    def process_request(self, method, url, headers, data):
        timeout_retry = self.timeout_retry
        ret = None
        temp_ret = None
        while True:
            try:
                if (method == 'get') or (method == 'GET'):
                    ret = requests.request(method, url=url, headers=headers,
                                           verify=False, timeout=self.timeout)
                else:
                    ret = requests.request(method, url=url, headers=headers,
                                           data=data, verify=False,
                                           timeout=self.timeout)
                break

            except requests.exceptions.Timeout:
                temp_ret = "Timeout Exceptions"
                LOG.error(_LE("Exception: AC time out, "
                              "traceback:%s"), traceback.format_exc())
                timeout_retry -= 1
                if timeout_retry < 0:
                    ret = "Timeout Exceptions"
                    break

            except Exception:
                LOG.error(_LE("Exception: AC exception, traceback:%s"),
                          traceback.format_exc())
                timeout_retry -= 1
                if timeout_retry < 0:
                    if temp_ret == "Timeout Exceptions":
                        ret = "Timeout Exceptions"
                    else:
                        ret = "Exceptions"
                    break

        if ("Timeout Exceptions" == ret) or ("Exceptions" == ret):
            LOG.error(_LE('AC: request failed, return code:%s') % ret)
            return ret

        return ret

    # Internal function to fix the JSON parameters
    def fix_json(self, str):
        return str.replace(r'"result":null', r'"result":"null"')

    # Check whether the http response is success ir not
    def http_success(self, http):
        LOG.debug(http)
        status = int(http['status'])
        if (status == requests.codes.ok or
                status == requests.codes.not_modified) \
            and http['response'] is not None:
            return True
        else:
            return False

    # Check whether the http response is failure ir not
    def httpError(self):
        pass

    # http Operationtimeout
    def httpTimeout(self):
        pass

    # Post the message
    def post(self):
        pass
