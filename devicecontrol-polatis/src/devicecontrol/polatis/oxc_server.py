from click import command, option
import json
import logging
import subprocess
from tornado.escape import json_decode
import tornado.ioloop
import tornado.web

from devicecontrol.polatis import Oxc


DEFAULT_LISTEN_PORT = 25025

SERVER_IP = subprocess.run(["hostname", "-I"], stdout=subprocess.PIPE).stdout.decode("utf-8").split(' ')[0]

console_formatter = logging.Formatter('%(asctime)s; %(message)s')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(console_formatter)

LOGGER = logging.getLogger()
LOGGER.addHandler(console_handler)
LOGGER.setLevel(logging.DEBUG)


class BaseHandler(tornado.web.RequestHandler):
    def initialize(self, polatis_dict):
        self.polatis_dict = polatis_dict

    def _decode_json(self):
        try:
            return json_decode(self.request.body)
        except:
            LOGGER.warning('Handler exception. No JSON data.')
            self.write('Handler exception. No JSON data.')

    def _map_oxc_ip(self, data_dict):
        '''
            # ip has priority over name
            data {
                'oxc_name': 'chavo'/'chapulin',
                'oxc_ip': 'ip',
                ...
            }
        '''
        if 'oxc_ip' in data_dict:
            oxc_ip = data_dict['oxc_ip']
        elif 'oxc_name' in data_dict:
            oxc_ip  = self.polatis_dict[data_dict['oxc_name']]['ip']
        return oxc_ip

    # Polatis OXC methods
    def _check_oxc_connectivity(self, oxc_ip):
        LOGGER.info('Checking connectivity to Oxc {}'.format(oxc_ip))
        try:
            response = Oxc(oxc_ip).idn
        except:
            response = 'Failed.'

        LOGGER.info(response)
        return response
    
    def _get_oxc_connections(self, oxc_ip):
        LOGGER.info('Getting Oxc {} connections.'.format(oxc_ip))
        try:
            response = Oxc(oxc_ip).connections
        except:
            response = 'Failed.'

        LOGGER.info(response)
        return response

    def _connect_OXC(self, oxc_ip, connection_dict):
        if not isinstance(connection_dict, dict):
            response = 'Failed. The connections must come in a dictionary.'
            LOGGER.error(response)
            return response

        LOGGER.info('Adding the following cross-connections on OXC {}'.format(oxc_ip))
        LOGGER.info('Cross-connections: {}'.format(connection_dict))
        try:
            Oxc(oxc_ip).connect(connection_dict)
            response = 'Ok.'
        except:
            response = 'Failed.'
        
        LOGGER.info(response)
        return response

    def _disconnect_OXC(self, oxc_ip, connection_dict):
        if not isinstance(connection_dict, dict):
            response = 'Failed. The connections must come in a dictionary.'
            LOGGER.error(response)
            return response

        LOGGER.info('Removing the following cross-connections on OXC {}'.format(oxc_ip))
        LOGGER.info('Cross-connections: {}'.format(connection_dict))
        try:
            Oxc(oxc_ip).disconnect(connection_dict)
            response = 'Ok.'
        except:
            response = 'Failed.'
        
        LOGGER.info(response)
        return response

    def _disconnect_all_OXC(self, oxc_ip):
        LOGGER.info('Disconnecting all Oxc {} connections.'.format(oxc_ip))
        try:
            Oxc(oxc_ip).disconnect_all()
            response = 'Ok.'
        except:
            response = 'Failed.'

        LOGGER.info(response)
        return response

    def _get_power_OXC(self, oxc_ip, port_list):
        if not isinstance(port_list, list):
            response = 'Failed. The ports must come in a list.'
            LOGGER.error(response)
            return response
        
        LOGGER.info('Getting Oxc {} power of the following ports: {}.'.format(oxc_ip, port_list))
        try:
            response = Oxc(oxc_ip).get_power(port_list)
        except:
            response = 'Failed.'

        LOGGER.info(response)
        return response


class MainHandler(BaseHandler):
    def get(self):
        self.write("<h2>Welcome to Polatis OXC Agent.</h2>")
        self.write("<p style=\"font-size: 1.5em;\">The Agent is up and running. These are the currently know Polatis devices:</p>")
        self.write("<pre style=\"font-size: 1.5em;\">")
        self.write(json.dumps(self.polatis_dict, indent=2))
        self.write("</pre>")
        self.write("<p>&nbsp;</p>")


class IdnHandler(BaseHandler):
    def post(self):
        data_dict = self._decode_json()
        oxc_ip = self._map_oxc_ip(data_dict)
        resp = self._check_oxc_connectivity(oxc_ip)
        response_dict = {
            'response': resp
        }
        self.write(response_dict)


class ConnectionsHandler(BaseHandler):
    def post(self):
        data_dict = self._decode_json()
        oxc_ip = self._map_oxc_ip(data_dict)
        resp = self._get_oxc_connections(oxc_ip)
        response_dict = {
            'response': resp
        }
        self.write(response_dict)


class ConnectHandler(BaseHandler):
    def post(self):
        data_dict = self._decode_json()

        if 'connection_dict' in data_dict:
            oxc_ip = self._map_oxc_ip(data_dict)
            resp = self._connect_OXC(oxc_ip, data_dict['connection_dict'])
        else:
            resp = 'Failed. You must send a dictionary containing the connections.'
            LOGGER.warning(resp)
        
        response_dict = {
            'response': resp
        }
        self.write(response_dict)


class DisconnectHandler(BaseHandler):
    def post(self):
        data_dict = self._decode_json()

        if 'connection_dict' in data_dict:
            oxc_ip = self._map_oxc_ip(data_dict)
            resp = self._disconnect_OXC(oxc_ip, data_dict['connection_dict'])
        
        else:
            resp = 'Failed. You must send a dictionary containing the connections.'
            LOGGER.warning(resp)
        
        response_dict = {
            'response': resp
        }
        self.write(response_dict)


class DisconnectAllHandler(BaseHandler):
    def post(self):
        data_dict = self._decode_json()
        oxc_ip = self._map_oxc_ip(data_dict)
        resp = self._disconnect_all_OXC(oxc_ip)
        response_dict = {
            'response': resp
        }
        self.write(response_dict)


class PowerHandler(BaseHandler):
    def post(self):
        data_dict = self._decode_json()

        if 'port_list' in data_dict:
            oxc_ip = self._map_oxc_ip(data_dict)
            resp = self._get_power_OXC(oxc_ip, data_dict['port_list'])
        else:
            resp = 'Failed. You must send a list containing the ports.'
            LOGGER.warning(resp)
        
        response_dict = {
            'response': resp
        }
        self.write(response_dict)

def setup_server():
    # if you have any configuration to be done, use the polatis_dict to send the values.
    polatis_dict = {
        'Chavo': {
            'ip': '10.68.100.3',
            'port': '5025'
        },
        'Chapulin': {
            'ip': '137.222.204.36',
            'port': '5025'
        }
    }
    return polatis_dict


def make_app():
    polatis_dict = setup_server()
    urls = [
        (r"/", MainHandler, dict(polatis_dict=polatis_dict)),
        (r"/idn", IdnHandler, dict(polatis_dict=polatis_dict)),
        (r"/connections", ConnectionsHandler, dict(polatis_dict=polatis_dict)),
        (r"/connect", ConnectHandler, dict(polatis_dict=polatis_dict)),
        (r"/disconnect", DisconnectHandler, dict(polatis_dict=polatis_dict)),
        (r"/disconnectall", DisconnectAllHandler, dict(polatis_dict=polatis_dict)),
        (r"/power", PowerHandler, dict(polatis_dict=polatis_dict)),
    ]
    return tornado.web.Application(urls)


@command()
@option(
    "-p",
    "--port",
    default=DEFAULT_LISTEN_PORT,
    help="Listen port. Default port is {}.".format(DEFAULT_LISTEN_PORT)
)
def main(
    port=DEFAULT_LISTEN_PORT
):
    """
    Polatis OXC REST server.
    Offers an interface to control the Polatis OXCs using requests.
    """
    app = make_app()
    app.listen(port)
    LOGGER.info("Server ready, listening on {}:{}".format(SERVER_IP, port))
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()
