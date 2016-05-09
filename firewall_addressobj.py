import re

class AddressObject(object):
    """The abstract base class for all port objects"""

    def __init__(self,firewall,chunk,start_num):
        self.firewall = firewall
        self.firmware = firewall.firmware
        self.vendor = firewall.vendor
        self.text = chunk
        self.start = start_num
        self.end = start_num + len(chunk)
        self.line_counter = 0
        self.name = ""
        self.kind = ""
        self.network_address = ""
        self.mask = ""
        print "Hello this is an address object of vendor %s with OS %s"%(self.vendor,self.firmware)
#####################################################################################################
def parse_addrobj(firewall,chunk,start_num):
    """Call the correct parser function based on vendor and OS"""

    if firewall.vendor == 'cisco' and firewall.firmware == 'asa-9.0':
        return _parse_ciscoasa_9dot0(firewall,chunk,start_num)
    else:
        raise NotImplementedError("Sorry, the vendor and firmware combination you specified \
        is not supported")
#####################################################################################################
def _parse_ciscoasa_9dot0(firewall,chunk,start_num):
    # Initialize port
    addrobj = AddressObject(firewall,chunk,start_num)
    addrobj.name = addrobj.text[addrobj.line_counter].split()[-1]
    firewall.lines_parsed[firewall.line_counter+addrobj.line_counter] = addrobj.text[addrobj.line_counter]
    addrobj.line_counter += 1
    # The dictionary of config items the parser understands, and their regex's 
    re_dict = {'host':'host ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)',
               'subnet':'subnet ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+) ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)',
               'description':'description ([A-z0-9-_ ]+)',
               'range':'range ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+) ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)'}
    # Compare the line to all the available regex's. Execute the appropiate parser for the sub
    # object 
    while addrobj.line_counter < len(addrobj.text):
        line = addrobj.text[addrobj.line_counter]
        #print "LINE: ",line
        for obj,regex in re_dict.iteritems():
            match = re.search(regex,line)
            #print "OBJECT: ",obj
            #print "REGEX: ",regex
            #print "MATCH: ",match
            if match:
                firewall.lines_parsed[firewall.line_counter+addrobj.line_counter] = line
                if obj == 'host':
                    addrobj.kind = 'host'
                    addrobj.network_address = match.group(1)
                    addrobj.mask = '255.255.255.255'
                elif obj == 'subnet':
                    addrobj.kind = 'subnet'
                    addrobj.network_address = match.group(1)
                    addrobj.mask = match.group(2)
                elif obj == 'description':
                    addrobj.description = match.group(1)
                elif obj == 'range':
                    addrobj.kind = 'range'
                    addrobj.start_ip = match.group(1)
                    addrobj.end_ip = match.group(2)
                addrobj.line_counter += 1
                break    
        if not match:
            firewall.lines_missed[firewall.line_counter+addrobj.line_counter] = line
            addrobj.line_counter +=1
    return addrobj
