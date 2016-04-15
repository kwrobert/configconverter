import re

class ObjectGroup(object):
    """Abstract base class for object groups"""

    def __init__(self,firewall,chunk,start_num):
        self.firewall = firewall
        self.firmware = firewall.firmware
        self.vendor = firewall.vendor
        self.text = chunk
        self.start = start_num
        self.end = start_num + len(chunk)
        self.line_counter = 0
        self.name = ""
        self.member_objects = []
class ServiceGroup(ObjectGroup):
    """Child of ObjectGroup class for handling service object groups"""
    def __init__(self,firewall,chunk,start_num):
        ObjectGroup.__init__(self,firewall,chunk,start_num)
        print "Hello this is a service group of vendor %s with OS %s"%(self.vendor,self.firmware)

class AddressGroup(ObjectGroup):
    """Child of ObjectGroup class for handling service object groups"""
    def __init__(self,firewall,chunk,start_num):
        ObjectGroup.__init__(self,firewall,chunk,start_num)
        print "Hello this is a address group of vendor %s with OS %s"%(self.vendor,self.firmware)
    
    def add_addrobj(self,name):
        objs = filter(lambda obj: obj.name == name,firewall.address_objects)
        if len(objs) > 1:
            print "WOAH FOUND SOME DUPLICATE OBJECTS IN ADDRESS OBJECTS CONTAINER"
        self.member_objects += objs
    def add_group(self,name):
        objs = filter(lambda obj: obj.name == name,firewall.address_groups)
        if len(objs) > 1:
            print "WOAH FOUND SOME DUPLICATE OBJECTS IN ADDRESS OBJECTS CONTAINER"
        self.member_objects += objs
#####################################################################################################
def parse_addrgroup(firewall,chunk,start_num):
    """Call the correct parser function based on vendor and OS"""

    if firewall.vendor == 'cisco' and firewall.firmware == 'ciscoasa':
        return _parse_ciscoasa_addrgroup(firewall,chunk,start_num)
    else:
        raise NotImplementedError("Sorry, the vendor and firmware combination you specified \
        is not supported")
#-----------------------------------------------------------------------------------------------------#
def parse_servgroup(firewall,chunk,start_num):
    """Call the correct parser function based on vendor and OS"""

    if firewall.vendor == 'cisco' and firewall.firmware == 'ciscoasa':
        return _parse_ciscoasa_servgroup(firewall,chunk,start_num)
    else:
        raise NotImplementedError("Sorry, the vendor and firmware combination you specified \
        is not supported")
#####################################################################################################
def _parse_ciscoasa_servgroup(firewall,chunk,start_num):
    print "Parsing cisco asa service group"
    servgroup = ServiceGroup(firewall,chunk,start_num)
    servgroup.name = servgroup.text[servgroup.line_counter].split()[-1]
    firewall.lines_parsed[firewall.line_counter+servgroup.line_counter] = servgroup.text[servgroup.line_counter]
    servgroup.line_counter += 1  
    return servgroup
def _parse_ciscoasa_addrgroup(firewall,chunk,start_num):
    print "Parsing cisco asa address group"
    addrgroup = AddressGroup(firewall,chunk,start_num)
    addrgroup.name = addrgroup.text[addrgroup.line_counter].split()[-1]
    firewall.lines_parsed[firewall.line_counter+addrgroup.line_counter] = addrgroup.text[addrgroup.line_counter]
    addrgroup.line_counter += 1 
    re_dict = {'address-object':'network-object object ([.]+)', 'object-group':'group-object ([.]+)'}
            
    while addrgroup.line_counter < len(addrgroup.text):
        line = addrgroup.text[addrgroup.line_counter]
        for obj,regex in re_dict.iteritems():
            match = re.search(regex,line)
            if match:
                firewall.lines_parsed[firewall.line_counter+addrgroup.line_counter] = line
                if obj == 'address-object':
                    addrgroup.add_addrobj(match.group(1))
                elif obj == 'object-group':
                    addrgroup.add_group(match.group(1))
                break
            if not match:
                firewall.lines_missed[firewall.line_counter+addrgroup.line_counter] = line
                addrgroup.line_counter +=1

    return addrgroup
