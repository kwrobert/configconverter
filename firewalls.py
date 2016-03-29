#####################################################################################################
# Name: firewalls.py
# Author: Kyle Robertson
# Company: Worldcom Exchange Inc. 
# Description: This file contains the generic base class and vendor specific subclasses for all 
# supported firewalls.
#####################################################################################################

    
def CiscoASAParser(config_file):
    print "This is the cisco asa parser which will someday parser %s"%(config_file)

def FortinetParser(config_file):
    print "This is the fortinet parser which will someday parser %s"%(config_file)


# A dictionary of dictionaries. The first key is the vender, the second is the firmware/OS version.
# The value is the appropriate parser callable
parser_dict = {'cisco':
                   {'ciscoasa':CiscoASAParser},
               'fortinet':
                   {'testfortiOS':FortinetParser}
              }


class Firewall(object):
    
    physical_ports = {}
    address_objects = {}
    service_objects = {}
    routes = {}
    service_groups = {}
    address_groups = {}
    
    def __init__(self, vendor, OS):
        self.firmware = OS
        self.vendor = vendor
        print "Hello, I am a %s firewall running OS version %s"%(self.vendor, self.firmware)
        self._get_parser()

    def _get_parser(self):
        """ Based on the initialized values for vendor and OS, get the correct config file parser
        and set the same of the parser for this firewall"""
        self._parser_callable = parser_dict[self.vendor][self.firmware]
        self.parser = self._parser_callable.__name__

    def parse_config(self,config_file):
        """Externally exposed function that uses the chosen parser for some firewall instance to parse a config file"""
        self._parser_callable(config_file)

