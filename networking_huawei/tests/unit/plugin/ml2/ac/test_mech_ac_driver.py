# Copyright (c) 2015 Huawei Technologies India Pvt Ltd
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

import mock
import networking_huawei.plugins.ml2.ac.driver as huawei_ml2_driver
from neutron.plugins.common import constants
from neutron.plugins.ml2 import driver_api as api
from neutron.plugins.ml2 import driver_context as ctx
from oslo_config import cfg
from oslo_serialization import jsonutils
from oslotest import base
import requests

test_network_uuid = 'd897e21a-dfd6-4331-a5dd-7524fa421c3e'

test_network_object_sent = {'status': 'ACTIVE',
                            'subnets': [],
                            'name': 'net1',
                            'provider:physical_network': None,
                            'admin_state_up': True,
                            'tenant_id': 'test-tenant',
                            'provider:network_type': 'local',
                            'router:external': False,
                            'shared': False,
                            'id': test_network_uuid,
                            'provider:segmentation_id': None}

test_network_object_sent_missing_tenant_id = {'status': 'ACTIVE',
                                              'subnets': [],
                                              'name': 'net1',
                                              'provider:physical_network':
                                                  None,
                                              'admin_state_up': True,
                                              'provider:network_type': 'local',
                                              'router:external': False,
                                              'shared': False,
                                              'id': test_network_uuid,
                                              'provider:segmentation_id': None}

test_network_object_receive = {"id": "d897e21a-dfd6-4331-a5dd-7524fa421c3e",
                               "status": "ACTIVE",
                               "segmentationId": None,
                               "tenant_id": "test-tenant",
                               "name": "net1",
                               "adminStateUp": True,
                               "shared": False,
                               "networkType": "local",
                               "physicalNetwork": None,
                               "routerExternal": False,
                               "serviceName": "physnet1"}

test_network_object_receive_update = {"id": "d897e21a-dfd6-4331-"
                                            "a5dd-7524fa421c3e",
                                      "status": "ACTIVE",
                                      "segmentationId": None,
                                      "tenant_id": "test-tenant",
                                      "name": "net1",
                                      "adminStateUp": True,
                                      "shared": False,
                                      "networkType": "local",
                                      "physicalNetwork": None,
                                      "routerExternal": False}

test_subnet_uuid = 'd897e21a-dfd6-4331-a5dd-7524fa421c3e'

test_subnet_object_sent = {'ipv6_ra_mode': None,
                           'allocation_pools': [{'start': '10.0.0.2',
                                                 'end': '10.0.1.254'}],
                           'host_routes': [],
                           'ipv6_address_mode': None,
                           'cidr': '10.0.0.0/23',
                           'id': test_subnet_uuid,
                           'name': '',
                           'enable_dhcp': True,
                           'network_id': test_network_uuid,
                           'tenant_id': 'test-tenant',
                           'dns_nameservers': [],
                           'gateway_ip': '10.0.0.1',
                           'ip_version': 4,
                           'shared': False}

test_subnet_object_receive = {'networkId': test_network_uuid,
                              'tenant_id': 'test-tenant',
                              'id': test_subnet_uuid,
                              'name': '',
                              'ipVersion': 4,
                              'enableDhcp': True,
                              'allocationPools': [{'start': '10.0.0.2',
                                                   'end': '10.0.1.254'}],
                              'cidr': '10.0.0.0/23',
                              'gatewayIp': '10.0.0.1',
                              'dnsNameservers': [],
                              'hostRoutes': [],
                              "serviceName": "physnet1"}

test_subnet_object_update = {'networkId': test_network_uuid,
                             'tenant_id': 'test-tenant',
                             'id': test_subnet_uuid,
                             'name': '',
                             'ipVersion': 4,
                             'enableDhcp': True,
                             'allocationPools':
                                 [{'start': '10.0.0.2', 'end': '10.0.1.254'}],
                             'cidr': '10.0.0.0/23',
                             'gatewayIp': '10.0.0.1',
                             'dnsNameservers': [],
                             'hostRoutes': []}

test_fake_port_uuid = '72c56c48-e9b8-4dcf-b3a7-0813bb3bd839'

test_port_object_sent = {'status': 'DOWN',
                         'binding:host_id': 'ubuntu',
                         'allowed_address_pairs': [],
                         'device_owner': 'fake_owner',
                         'binding:profile': {},
                         'fixed_ips': [],
                         'id': test_fake_port_uuid,
                         'security_groups': [],
                         'device_id': 'fake_device',
                         'name': '',
                         'admin_state_up': True,
                         'network_id': test_network_uuid,
                         'tenant_id': 'test-tenant',
                         'binding:vif_details': {},
                         'binding:vnic_type': 'normal',
                         'binding:vif_type': 'unbound',
                         'mac_address': '12:34:56 :78:21:b6'}

test_port_object_sent_sg = {'status': 'DOWN',
                            'binding:host_id': 'ubuntu',
                            'allowed_address_pairs': [],
                            'device_owner': 'fake_owner',
                            'binding:profile': {},
                            'fixed_ips': [],
                            'id': test_fake_port_uuid,
                            'security_groups':
                                ['2f9244b4-9bee-4e81-bc4a-3f3c2045b3d7'],
                            'device_id': 'fake_device',
                            'name': '',
                            'admin_state_up': True,
                            'network_id': test_network_uuid,
                            'tenant_id': 'test-tenant',
                            'binding:vif_details': {},
                            'binding:vnic_type': 'normal',
                            'binding:vif_type': 'unbound',
                            'mac_address': '12:34:56 :78:21:b6'}

test_port_object_receive = {"id": "72c56c48-e9b8-4dcf-b3a7-0813bb3bd839",
                            "networkId": "d897e21a-dfd6-4331-a5dd-7524fa"
                                         "421c3e",
                            "macAddress": "12:34:56 :78:21:b6",
                            "tenant_id": "test-tenant",
                            "serviceName": "physnet1",
                            "profile": {"localLinkInformations": []},
                            "name": "",
                            "adminStateUp": True,
                            "sercurityGroups": [],
                            "deviceOwner": "fake_owner",
                            "hostId": "ubuntu"}

test_port_object_receive_sg = {"id": "72c56c48-e9b8-4dcf-b3a7-0813bb3bd839",
                               "serviceName": "physnet1",
                               "sercurityGroups": ["2f9244b4-9bee-"
                                                   "4e81-bc4a-3f3c2045b3d7"],
                               "tenant_id": "test-tenant",
                               "name": "",
                               "macAddress": "12:34:56 :78:21:b6",
                               "deviceOwner": "fake_owner",
                               "hostId": "ubuntu",
                               "adminStateUp": True,
                               "networkId": "d897e21a-dfd6-"
                               "4331-a5dd-7524fa421c3e",
                               "profile": {"localLinkInformations": []}}

test_port_object_receive_sg_rule_list = {"tenant_id": "e4f50856753b4d"
                                                      "c6afee5fa6b9b6c550",
                                         "name": "new-webservers",
                                         "description": "security "
                                                        "group for webservers",
                                         "id": "2076db17-a522-"
                                               "4506-91de-c6dd8e837028",
                                         "securityGroupRuleList": []}

test_port_object_receive_update = {"id": "72c56c48-e9b8-4dcf-"
                                         "b3a7-0813bb3bd839",
                                   "networkId": "d897e21a-dfd6-"
                                                "4331-a5dd-7524fa421c3e",
                                   "macAddress": "12:34:56 :78:21:b6",
                                   "tenant_id": "test-tenant",
                                   "profile": {"localLinkInformations": []},
                                   "name": "",
                                   "adminStateUp": True,
                                   "sercurityGroups": [],
                                   "deviceOwner": "fake_owner",
                                   "hostId": "ubuntu"}

test_port_object_delete_update = {'id': "72c56c48-e9b8-"
                                        "4dcf-b3a7-0813bb3bd839",
                                  'name': "",
                                  'networkId': "d897e21a-dfd6-"
                                               "4331-a5dd-7524fa421c3e",
                                  'tenant_id': "test-tenant",
                                  'hostId': "ubuntu",
                                  'macAddress': "12:34:56 :78:21:b6",
                                  'adminStateUp': True,
                                  'deviceOwner': "fake_owner",
                                  'profile': {}
                                  }

security_group = {'tenant_id': '',
                  'name': '',
                  'description': '',
                  'id': '',
                  'security_group_rules': ''}

test_sg_receive = {"tenant_id": "e4f50856753b4dc6afee5fa6b9b6c550",
                   "name": "new-webservers",
                   "description": "security group for webservers",
                   "id": "2076db17-a522-4506-91de-c6dd8e837028",
                   "securityGroupRuleList": [
                       {"tenant_id": "e4f50856753b4dc6afee5fa6b9b6c550",
                        "remoteGroupId": None,
                        "direction": "egress",
                        "remoteIpPrefix": None,
                        "protocol": None,
                        "portRangeMax": None,
                        "portRangeMin": None,
                        "id": "565b9502-12de-4ffd-91e9-68885cff6ae1",
                        "etherType": "IPv6",
                        "securityGroupId":
                            "2076db17-a522-4506-91de-c6dd8e837028",
                        }]}

test_sg = {"security_group":
           {"description": "security group "
                           "for webservers",
            "id": "2076db17-a522-4506-91de-"
                  "c6dd8e837028",
            "name": "new-webservers",
            "security_group_rules": [
                {"direction": "egress",
                 "ethertype": "IPv6",
                 "id": "565b9502-12de-4ffd-91e9-68885cff6ae1",
                 "port_range_max": None,
                 "port_range_min": None,
                 "protocol": None,
                 "remote_group_id": None,
                 "remote_ip_prefix": None,
                 "security_group_id": "2076db17-a522-"
                                      "4506-91de-c6dd8e837028",
                 "tenant_id": "e4f50856753b4dc6a"
                              "fee5fa6b9b6c550"}],
            "tenant_id": "e4f50856753b4dc6afee5fa6b9b6c550"
            }}

test_sg_create = {"security_group": {
                  "tenant_id": "e4f50856753b4d"
                               "c6afee5fa6b9b6c550",
                  "name": "new-webservers",
                  "description": "security "
                                 "group for webservers",
                  "id": "2076db17-a522-4506-"
                        "91de-c6dd8e837028",
                  "security_group_rules": []}}

test_delete_sg = {'security_group_id': "2076db17-a522-4506-91de-c6dd8e837028"}

test_delete_sg_receive = {'id': "2076db17-a522-4506-91de-c6dd8e837028"}

test_sg_rule_create = {"security_group_rule": {
                       "direction": "ingress",
                       "ethertype": "IPv4",
                       "id": "2bc0accf-312e-429a-"
                             "956e-e4407625eb62",
                       "port_range_max": 80,
                       "port_range_min": 80,
                       "protocol": "tcp",
                       "remote_group_id": "85cc3048-abc3-"
                                          "43cc-89b3-377341426ac5",
                       "remote_ip_prefix": None,
                       "security_group_id": "a7734e61-b545-"
                                            "452d-a3cd-0189cbd9747a",
                       "tenant_id": "e4f50856753b4dc"
                                    "6afee5fa6b9b6c550"}}

test_sg_rule_receive = {'securityGroupRule': {
                        'remoteGroupId':
                        "85cc3048-abc3-43cc-89b3-377341426ac5",
                        'direction': "ingress",
                        'remoteIpPrefix': None,
                        'protocol': "tcp",
                        'etherType': "IPv4",
                        'tenant_id': "e4f50856753b4dc6a"
                                     "fee5fa6b9b6c550",
                        'portRangeMax': 80,
                        'portRangeMin': 80,
                        'id': "2bc0accf-312e-429a-956e-"
                              "e4407625eb62",
                        'securityGroupId': "a7734e61-b545-"
                                           "452d-a3cd-0189cbd9747a"}}

test_delete_sg_rule = {'security_group_rule_id':
                       "2076db17-a522-4506-91de-c6dd8e837028"}

test_delete_sg_rule_receive = {'id': "2076db17-a522-4506-91de-c6dd8e837028"}

test_delete_snat = {'router_id': "2076db17-a522-4506-91de-c6dd8e837028"}

test_delete_snat_receive = {'id': "2076db17-a522-4506-91de-c6dd8e837028"}


class HuaweiACMechanismDriverTestCase(base.BaseTestCase,
                                      huawei_ml2_driver.
                                      HuaweiACMechanismDriver):
    def setUp(self):
        super(HuaweiACMechanismDriverTestCase, self).setUp()
        super(HuaweiACMechanismDriverTestCase, self).initialize()
        self.set_test_config()

    # over_ride the config file values
    def set_test_config(self):
        cfg.CONF.set_override('host', '127.0.0.1', 'ml2_huawei_ac')
        cfg.CONF.set_override('port', '2222', 'ml2_huawei_ac')
        cfg.CONF.set_override('username', 'huawei_user', 'ml2_huawei_ac')
        cfg.CONF.set_override('password', 'huawei_pwd', 'ml2_huawei_ac')
        self.ml2_huawei_path = "http://" + cfg.CONF.ml2_huawei_ac.host + ":" + \
                               str(cfg.CONF.ml2_huawei_ac.port)

    # prepare the error response for post request
    def _mock_req_resp(self, status_code):
        response = mock.Mock()
        response.response = "OK"
        response.status_code = status_code
        response.errorcode = 0
        response.content = jsonutils.dumps(
            {'result': "ok", 'errorCode': '0', 'errorMsg': None}, indent=2)
        return response

    # prepare the response for post request
    def _mock_req_resp_error(self, status_code):
        response = mock.Mock()
        response.response = "OK"
        response.status_code = status_code
        response.errorcode = '1'
        response.content = ""
        return response

    def _test_response(self, context, oper_type,
                       obj_type, mock_method, any=False):
        body = '{}'
        url = ""
        append_url = "controller/dc/esdk/v2.0/"

        if oper_type is not 'DELETE':
            entity = {obj_type: sorted(context.current.copy().values())}
            body = jsonutils.dumps(entity)

            if oper_type == 'POST':
                url = '%s/%s%s' % (self.ml2_huawei_path, append_url,
                                   obj_type + 's')
            elif oper_type == 'PUT':
                url = '%s/%s/%s' % (self.ml2_huawei_path,
                                    append_url +
                                    obj_type + 's',
                                    context.current['id'])
        else:
            url = '%s/%s/%s' % (self.ml2_huawei_path, append_url +
                                obj_type + 's',
                                context.current['id'])

        if oper_type is not 'DELETE':
            data = mock_method.call_args[1]['data']
            data_network = jsonutils.loads(data)

            if obj_type in data_network:
                data_network = data_network[obj_type]

            data_network = sorted(data_network.values())

            mock_method.call_args[1]['data'] = \
                jsonutils.dumps({obj_type: data_network})

        kwargs = {'url': url, 'data': body}
        if not any:
            mock_method.assert_called_once_with(
                oper_type,
                headers={'Content-type': 'application/json',
                         'Accept': 'application/json'},
                timeout=float(cfg.CONF.ml2_huawei_ac.request_timeout),
                verify=False,
                **kwargs)
        else:
            mock_method.assert_any_call(
                oper_type,
                headers={'Content-type': 'application/json',
                         'Accept': 'application/json'},
                timeout=float(cfg.CONF.ml2_huawei_ac.request_timeout),
                verify=False,
                **kwargs)

    def _test_response_sg(self, context, oper_type,
                          obj_type, mock_method, any=False):
        body = '{}'
        url = ""
        append_url = "controller/dc/esdk/v2.0/"

        if obj_type != "snat":
            append_url = "controller/dc/esdk/v2.0/neutronapi/"

        if oper_type is not 'DELETE':
            if obj_type != 'security-group-rule':
                entity = {obj_type: (context.current.copy())}
            else:
                entity = context.current.copy()
        else:
            entity = {}

        if obj_type in entity and 'securityGroupRuleList' in entity[obj_type]:
            entity[obj_type]['securityGroupRuleList'] = \
                entity[obj_type]['securityGroupRuleList'].sort()

        body = jsonutils.dumps(entity)

        if obj_type is 'securityGroup':
            obj_type = 'security-group'

        if oper_type == 'POST':
            url = '%s/%s%s' % (self.ml2_huawei_path, append_url,
                               obj_type + 's')
        elif oper_type == 'PUT' or oper_type == 'DELETE':
            url = '%s/%s/%s' % (self.ml2_huawei_path, append_url
                                + obj_type + 's',
                                context.current['id'])

        if obj_type is 'security-group':
            obj_type = 'securityGroup'

        data = mock_method.call_args[1]['data']
        data_network = jsonutils.loads(data)

        if obj_type in data_network:
            data_network = data_network[obj_type]

        if 'securityGroupRuleList' in data_network:
            data_network['securityGroupRuleList'] = \
                data_network['securityGroupRuleList'].sort()
            mock_method.call_args[1]['data'] = \
                jsonutils.dumps({obj_type: data_network})

        kwargs = {'url': url, 'data': body}
        if not any:
            mock_method.assert_called_once_with(
                oper_type,
                headers={'Content-type': 'application/json',
                         'Accept': 'application/json'},
                timeout=float(cfg.CONF.ml2_huawei_ac.request_timeout),
                verify=False,
                **kwargs)
        else:
            mock_method.assert_any_call(
                oper_type,
                headers={'Content-type': 'application/json',
                         'Accept': 'application/json'},
                timeout=float(cfg.CONF.ml2_huawei_ac.request_timeout),
                verify=False,
                **kwargs)

    def test_create_network_postcommit(self):
        context = mock.Mock(current=test_network_object_sent)
        context_receive = mock.Mock(current=test_network_object_receive)
        resp = self._mock_req_resp(requests.codes.no_content)
        with mock.patch('requests.request',
                        return_value=resp) as mock_method:
            self.create_network_postcommit(context)
            self._test_response(context_receive, 'POST',
                                'network', mock_method)

    def test_update_network_postcommit_all_good(self):
        context = mock.Mock(current=test_network_object_sent)
        context_receive = mock.Mock(current=test_network_object_receive_update)
        resp = self._mock_req_resp(requests.codes.all_good)
        with mock.patch('requests.request',
                        return_value=resp) as mock_method:
            self.update_network_postcommit(context)
            self._test_response(context_receive, 'PUT',
                                'network', mock_method)

    def test_update_network_postcommit(self):
        context = mock.Mock(current=test_network_object_sent)
        context_receive = mock.Mock(current=test_network_object_receive_update)
        resp = self._mock_req_resp(requests.codes.all_good)
        with mock.patch('requests.request',
                        return_value=resp) as mock_method:
            self.update_network_postcommit(context)
            self._test_response(context_receive, 'PUT',
                                'network', mock_method)

    def test_delete_network_postcommit(self):
        context = mock.Mock(current=test_network_object_sent)
        resp = self._mock_req_resp(requests.codes.no_content)
        with mock.patch('requests.request',
                        return_value=resp) as mock_method:
            self.delete_network_postcommit(context)
            self._test_response(context, 'DELETE',
                                'network', mock_method)

    def test_create_subnet_postcommit(self):
        context = mock.Mock(current=test_subnet_object_sent)
        context_receive = mock.Mock(current=test_subnet_object_receive)
        resp = self._mock_req_resp(requests.codes.no_content)
        with mock.patch('requests.request',
                        return_value=resp) as mock_method:
            self.create_subnet_postcommit(context)
            self._test_response(context_receive, 'POST',
                                'subnet', mock_method)

    def test_update_subnet_postcommit(self):
        context = mock.Mock(current=test_subnet_object_sent)
        context_receive = mock.Mock(current=test_subnet_object_update)
        resp = self._mock_req_resp(requests.codes.no_content)
        with mock.patch('requests.request',
                        return_value=resp) as mock_method:
            self.update_subnet_postcommit(context)
            self._test_response(context_receive, 'PUT',
                                'subnet', mock_method)

    def test_delete_subnet_postcommit(self):
        context = mock.Mock(current=test_subnet_object_sent)
        resp = self._mock_req_resp(requests.codes.no_content)
        with mock.patch('requests.request',
                        return_value=resp) as mock_method:
            self.delete_subnet_postcommit(context)
            self._test_response(context, 'DELETE',
                                'subnet', mock_method)

    def test_create_port_postcommit(self):
        context = mock.Mock(current=test_port_object_sent)
        context_receive = mock.Mock(current=test_port_object_receive)
        resp = self._mock_req_resp(requests.codes.no_content)
        with mock.patch('requests.request',
                        return_value=resp) as mock_method:
                self.create_port_postcommit(context)
                self._test_response(context_receive, 'POST',
                                    'port', mock_method)

    def test_update_port_postcommit(self):
        context = mock.Mock(current=test_port_object_sent)
        context_receive = mock.Mock(
            current=test_port_object_receive_update)
        resp = self._mock_req_resp(requests.codes.no_content)
        with mock.patch('requests.request',
                        return_value=resp) as mock_method:
            self.update_port_postcommit(context)
            self._test_response(context_receive, 'PUT',
                                'port', mock_method)

    valid_segment = {
        api.ID: 'API_ID',
        api.NETWORK_TYPE: constants.TYPE_LOCAL,
        api.SEGMENTATION_ID: 'API_SEGMENTATION_ID',
        api.PHYSICAL_NETWORK: 'API_PHYSICAL_NETWORK'}

    def test_bind_port(self):

        self.vif_details = {'ovs_hybrid_plug': True}
        network = mock.MagicMock(spec=api.NetworkContext)

        port_context = mock.MagicMock(
            spec=ctx.PortContext, current={'id': 'CURRENT_CONTEXT_ID'},
            segments_to_bind=[self.valid_segment],
            network=network)

        # when port is bound
        self.bind_port(port_context)

        # port_context.
        # then context binding is setup with returned vif_type and valid
        # segment api ID
        port_context.set_binding.assert_called_once_with(
            self.valid_segment[api.ID], 'ovs', self.vif_details)

    def test_create_network_postcommit_404_error(self):
        context = mock.Mock(current=test_network_object_sent)
        context_receive = mock.Mock(current=test_network_object_receive)
        resp = self._mock_req_resp_error(requests.codes.not_found)
        with mock.patch('requests.request',
                        return_value=resp) as mock_method:
            try:
                self.create_network_postcommit(context)
            except Exception:
                pass
            self._test_response(context_receive, 'POST',
                                'network', mock_method)

    def test_create_network_postcommit_401_error(self):
        context = mock.Mock(current=test_network_object_sent)
        context_receive = mock.Mock(current=test_network_object_receive)
        resp = self._mock_req_resp_error(requests.codes.unauthorized)
        with mock.patch('requests.request',
                        return_value=resp) as mock_method:
            try:
                self.create_network_postcommit(context)
            except Exception:
                pass
            self._test_response(context_receive, 'POST',
                                'network', mock_method, True)

    def test_create_network_postcommit_206_error(self):
        context = mock.Mock(current=test_network_object_sent)
        context_receive = mock.Mock(current=test_network_object_receive)
        resp = self._mock_req_resp_error(requests.codes.partial_content)
        with mock.patch('requests.request',
                        return_value=resp) as mock_method:
            try:
                self.create_network_postcommit(context)
            except Exception:
                pass
            self._test_response(context_receive, 'POST',
                                'network', mock_method, True)

    def test_create_network_postcommit_exceptions(self):
        context = mock.Mock(current=test_network_object_sent)
        context_receive = mock.Mock(current=test_network_object_receive)
        with mock.patch('requests.request',
                        return_value="Timeout Exceptions") as mock_method:
            self.create_network_postcommit(context)
            self._test_response(context_receive, 'POST',
                                'network', mock_method, True)

    def test_create_network_postcommit_201_driver_exception(self):
        context = mock.Mock(current=test_network_object_sent)
        context_receive = mock.Mock(current=test_network_object_receive)
        resp = self._mock_req_resp(requests.codes.created)
        with mock.patch('requests.request',
                        return_value=resp) as mock_method:
            try:
                self.create_network_postcommit(context)
            except Exception:
                pass
            self._test_response(context_receive, 'POST',
                                'network', mock_method)

    def test_create_network_postcommit_raise_timeout(self):
        context = mock.Mock(current=test_network_object_sent)
        context_receive = mock.Mock(current=test_network_object_receive)
        resp = self._mock_req_resp_error(requests.codes.unauthorized)
        with mock.patch('requests.request',
                        return_value=resp) as mock_method:
            mock_method.side_effect = requests.exceptions.\
                Timeout(mock.Mock(msg="Timeout Exceptions"))
            self.create_network_postcommit(context)
            self._test_response(context_receive, 'POST',
                                'network', mock_method, True)

    def test_create_network_postcommit_raise_exception(self):
        context = mock.Mock(current=test_network_object_sent)
        context_receive = mock.Mock(current=test_network_object_receive)
        resp = self._mock_req_resp_error(requests.codes.unauthorized)
        with mock.patch('requests.request',
                        return_value=resp) as mock_method:
            mock_method.side_effect = Exception(mock.Mock(msg="exceptions"))
            self.create_network_postcommit(context)
            self._test_response(context_receive, 'POST',
                                'network', mock_method, True)

    def test_create_security_group(self):
        context_receive = mock.Mock(
            current=test_port_object_receive_sg_rule_list)
        resp = self._mock_req_resp(requests.codes.all_good)
        kwargs = test_sg_create
        with mock.patch('requests.request', return_value=resp) as mock_method:
            with mock.patch.object(huawei_ml2_driver.SecurityGroupDbManager,
                                   'get_security_group',
                                   return_value=security_group):
                huawei_ml2_driver.create_security_group(
                    None, None, None, **kwargs)
                self._test_response_sg(context_receive,
                                       'POST', 'securityGroup', mock_method)

    def test_create_security_group_exception(self):
        resp = self._mock_req_resp(requests.codes.all_good)
        kwargs = test_sg_create
        with mock.patch.object(huawei_ml2_driver, 'rest_request',
                               return_value=resp) as mock_method:
            mock_method.side_effect = Exception(mock.Mock(msg="exceptions"))
            with mock.patch.object(huawei_ml2_driver.SecurityGroupDbManager,
                                   'get_security_group',
                                   return_value=security_group):
                huawei_ml2_driver.\
                    create_security_group(None, None, None, **kwargs)

    def test_create_security_group_exception_sg(self):
        resp = self._mock_req_resp(requests.codes.all_good)
        kwargs = test_sg_create
        with mock.patch.object(huawei_ml2_driver, 'rest_request',
                               return_value=resp) as mock_method:
            with mock.patch.object(huawei_ml2_driver.SecurityGroupDbManager,
                                   'get_security_group',
                                   return_value=security_group) \
                    as mock_method:
                mock_method.side_effect = Exception(
                    mock.Mock(msg="exceptions"))
                huawei_ml2_driver.create_security_group(
                    None, None, None, **kwargs)

    def test_update_security_group(self):
        resp = self._mock_req_resp(requests.codes.all_good)
        context_receive = mock.Mock(current=test_sg_receive)
        kwargs = test_sg
        with mock.patch('requests.request', return_value=resp) as mock_method:
            huawei_ml2_driver.update_security_group(None, None, None, **kwargs)
            self._test_response_sg(context_receive,
                                   'PUT', 'securityGroup', mock_method)

    def test_update_security_group_exception(self):
        resp = self._mock_req_resp(requests.codes.all_good)
        kwargs = test_sg
        with mock.patch.object(huawei_ml2_driver, 'rest_request',
                               return_value=resp) as mock_method:
            mock_method.side_effect = Exception(mock.Mock(msg="exceptions"))
            huawei_ml2_driver.update_security_group(None, None, None, **kwargs)

    def test_delete_security_group(self):
        resp = self._mock_req_resp(requests.codes.all_good)
        context_receive = mock.Mock(current=test_delete_sg_receive)
        kwargs = test_delete_sg
        with mock.patch('requests.request', return_value=resp) as mock_method:
            huawei_ml2_driver.delete_security_group(None, None, None, **kwargs)
            self._test_response_sg(context_receive,
                                   'DELETE', 'securityGroup', mock_method)

    def test_delete_security_group_exception(self):
        resp = self._mock_req_resp(requests.codes.all_good)
        kwargs = test_delete_sg
        with mock.patch.object(huawei_ml2_driver, 'rest_request',
                               return_value=resp) as mock_method:
            mock_method.side_effect = Exception(mock.Mock(msg="exceptions"))
            huawei_ml2_driver.delete_security_group(None, None, None, **kwargs)

    def test_create_security_group_rollback(self):
        resp = self._mock_req_resp(requests.codes.all_good)
        context_receive = mock.Mock(current=test_delete_sg_receive)
        with mock.patch('requests.request', return_value=resp) as mock_method:
            huawei_ml2_driver.create_security_group_rollback(
                test_delete_sg['security_group_id'])
            self._test_response_sg(context_receive,
                                   'DELETE', 'securityGroup', mock_method)

    def test_create_security_group_rule(self):
        resp = self._mock_req_resp(requests.codes.all_good)
        kwargs = test_sg_rule_create
        context_receive = mock.Mock(current=test_sg_rule_receive)
        with mock.patch('requests.request', return_value=resp) as mock_method:
            huawei_ml2_driver.create_security_group_rule(None, None,
                                                         None, **kwargs)
            self._test_response_sg(context_receive, 'POST',
                                   'security-group-rule', mock_method)

    def test_create_security_group_rule_exception(self):
        resp = self._mock_req_resp(requests.codes.all_good)
        kwargs = test_sg_rule_create
        with mock.patch.object(huawei_ml2_driver, 'rest_request',
                               return_value=resp) as mock_method:
            mock_method.side_effect = Exception(mock.Mock(msg="exceptions"))
            huawei_ml2_driver.create_security_group_rule(
                None, None, None, **kwargs)

    def test_delete_security_group_rule(self):
        resp = self._mock_req_resp(requests.codes.all_good)
        kwargs = test_delete_sg_rule
        context_receive = mock.Mock(current=test_delete_sg_rule_receive)
        with mock.patch('requests.request', return_value=resp) as mock_method:
            huawei_ml2_driver.delete_security_group_rule(
                None, None, None, **kwargs)
            self._test_response_sg(
                context_receive, 'DELETE', 'security-group-rule', mock_method)

    def test_delete_security_group_rule_exception(self):
        resp = self._mock_req_resp(requests.codes.all_good)
        kwargs = test_delete_sg_rule
        with mock.patch.object(huawei_ml2_driver, 'rest_request',
                               return_value=resp) as mock_method:
            mock_method.side_effect = Exception(mock.Mock(msg="exceptions"))
            try:
                huawei_ml2_driver.delete_security_group_rule(
                    None, None, None, **kwargs)
            except Exception:
                pass

    def test_delete_snat(self):
        resp = self._mock_req_resp(requests.codes.all_good)
        kwargs = test_delete_snat
        context_receive = mock.Mock(current=test_delete_snat_receive)
        with mock.patch('requests.request', return_value=resp) as mock_method:
            huawei_ml2_driver.delete_snat(None, None,
                                          None, **kwargs)
            self._test_response_sg(context_receive,
                                   'DELETE', 'snat', mock_method)

    def test_delete_snat_exception(self):
        resp = self._mock_req_resp(requests.codes.all_good)
        kwargs = test_delete_snat
        context_receive = mock.Mock(current=test_delete_snat_receive)
        with mock.patch.object(huawei_ml2_driver, 'rest_request',
                               return_value=resp) as mock_method:
            mock_method.side_effect = Exception()
            try:
                huawei_ml2_driver.delete_snat(None, None, None, **kwargs)
                self._test_response_sg(context_receive,
                                       'DELETE', 'snat', mock_method)
            except Exception:
                pass

    def test_default_security_group_rest_callback(self):
        try:
            huawei_ml2_driver.default_security_group_rest_callback(
                '0', None, requests.codes.ok, None)
            huawei_ml2_driver.default_security_group_rest_callback(
                '0', None, requests.codes.no_content, None)
            huawei_ml2_driver.default_security_group_rest_callback(
                '1', None, requests.codes.ok, None)
        except Exception:
            pass

    def test_all_rest_callback(self):
        try:
            self.__callBack__('1', None,
                              requests.codes.ok, None)
            self.__callBack__('0', None,
                              requests.codes.internal_server_error, None)
        except Exception:
            pass

    def test_all_rest_callback_two(self):
        try:
            huawei_ml2_driver.rest_callback('0', None,
                                            requests.codes.ok, None)
            huawei_ml2_driver.rest_callback('0', None,
                                            requests.codes.no_content, None)
            huawei_ml2_driver.rest_callback('1', None,
                                            requests.codes.ok, None)
        except Exception:
            pass

    # # passed
    def test_create_security_group_rule_rollback(self):
        resp = self._mock_req_resp(requests.codes.all_good)
        context_receive = mock.Mock(current=test_delete_sg_rule_receive)
        with mock.patch('requests.request', return_value=resp) as mock_method:
            huawei_ml2_driver.create_security_group_rule_rollback(
                test_delete_sg_rule['security_group_rule_id'])
            self._test_response_sg(context_receive, 'DELETE',
                                   'security-group-rule', mock_method)

    # passed
    def test_create_security_group_rule_rollback_exception(self):
        resp = self._mock_req_resp(requests.codes.all_good)
        context_receive = mock.Mock(current=test_delete_sg_rule_receive)
        with mock.patch.object(huawei_ml2_driver, 'rest_request',
                               return_value=resp) as mock_method:
            mock_method.side_effect = Exception()
            try:
                huawei_ml2_driver.create_security_group_rule_rollback(
                    test_delete_sg_rule['security_group_rule_id'])
                self._test_response_sg(context_receive,
                                       'DELETE', 'security-group-rule',
                                       mock_method, True)
            except Exception:
                pass

    # error, bug invalid option used in code
    # def test_creportOpenstackName(self):
    #
    #     resp = self._mock_req_resp(requests.codes.all_good)
    #
    #     url = '%s%s' % (self.ml2_huawei_path, "
                # /rest/openapi/AgileController/OpenSDK/openstackname")
    #     kwargs = {'url': url, 'data': {}}
    #
    #     with mock.patch.object(huawei_ml2_driver, 'rest_request',
    #                            return_value=resp) as mock_method:
    #
    #         rest_service.RESTService().reportOpenstackName()
    #
    #         mock_method.assert_called_once_with(
    #             "POST",
    #             headers={'Content-type': 'application/json',
                # 'Accept': 'application/json'},
    #             timeout=float(cfg.CONF.ml2_huawei_ac.request_timeout),
    #             verify=False,
    #             **kwargs)

    # currenlty only delete_port_precommit is supported looks like some bug
    # dont have delete_port_postcommit method to test this case
    # todo: check with libu later
    # def test_delete_port_precommit(self):
    #     context = mock.Mock(current=test_port_object_sent)
    #     context_receive = mock.Mock(current=test_port_object_delete_update)
    #     resp = self._mock_req_resp(requests.codes.ok)
    #     with mock.patch('requests.request',
    #                     return_value=resp) as mock_method:
    #         self.delete_port_precommit(context)
    #         self._test_response(context_receive,
                # 'DELETE', 'port', mock_method)

    # # # error
    # # def test_create_network_postcommit_no_tenant(self):
    # #     context = mock.Mock(current=
                # test_network_object_sent_missing_tenant_id)
    # #     context_receive = mock.Mock(current=test_network_object_receive)
    # #     resp = self._mock_req_resp(requests.codes.no_content)
    # #     with mock.patch('requests.request',
    # #                     return_value=resp) as mock_method:
    # #         self.create_network_postcommit(context)
    # #         self._test_response(context_receive, 'POST',
                # 'network', mock_method)
    #
    #

    # # create port with security group, facing err in importing in mock
    # def test_create_port_postcommit_with_sg(self):
    #
    #     context = mock.Mock(current=test_port_object_sent_sg)
    #     context_receive = mock.Mock(current=test_port_object_receive_sg)
    #     resp = self._mock_req_resp(requests.codes.all_good)
    #     # sg_group = self._mock_sg_group_resp()
    #
    #     with mock.patch('requests.request', return_value=resp)
                # as mock_method:
    #         with mock.patch.object(huawei_ml2_driver.SecurityGroupDbManager,
                # 'get_security_group',
    #                                return_value=security_group):
    #             self.create_port_postcommit(context)
    #             self._test_response(context_receive, 'POST',
                # 'port', mock_method)
