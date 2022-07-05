# -*- coding: utf-8 -*-

import json
import requests as req
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Device:
    auth = ()
    headers = {}

    def __init__(self, name, dev_type):
        self.name = name
        self.type = dev_type

    def send_rest_post_request(self, data, timeout=0.0):
        try:
            response = req.post(
                self.url,
                auth=self.auth,
                data=json.dumps(data),
                headers=self.headers,
                verify=False,
                # timeout=(300.0,300.0)
                timeout=300
            )
            # else:
            #     response = req.post(
            #         self.url,
            #         auth=self.auth,
            #         data=json.dumps(data),
            #         headers=self.headers,
            #         verify=self.verify,
            #         # timeout = timeout
            #         timeout=None
            #     )
            return response
        except req.ConnectionError as error:  # noqa
            # print("Error message: {}".format(error))
            # return error
            return None

    def send_rest_get_request(self):
        try:
            response = req.get(
                self.base_url,
                auth=self.auth,
                verify=False
            )
            return response
        except req.ConnectionError as error:  # noqa
            # print("Error message: {}".format(error))
            # return error
            return None