import re
import firewall_addressobj as fwa
import firewall_serviceobj as fws

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
        self.protocol = ""
        self.description = ""
        self.ports = []
        self.member_objects = []

class ServiceGroup(ObjectGroup):
    """Child of ObjectGroup class for handling service object groups"""
    def __init__(self,firewall,chunk,start_num):
        ObjectGroup.__init__(self,firewall,chunk,start_num)
        print "Hello this is a service group of vendor %s with OS %s"%(self.vendor,self.firmware)
    def add_servobj(self,name):
        objs = filter(lambda obj: obj.name == name,self.firewall.service_objects)
        if len(objs) > 1:
            print "WOAH FOUND SOME DUPLICATE OBJECTS IN SERVICE OBJECTS CONTAINER"
        self.member_objects += objs
    def add_group(self,name):
        objs = filter(lambda obj: obj.name == name,self.firewall.service_groups)
        if len(objs) > 1:
            print "WOAH FOUND SOME DUPLICATE OBJECTS IN SERVICE OBJECTS CONTAINER"
        self.member_objects += objs

    def create_servobj(self,line,line_num,name):
        servobj = fws.ServiceObject(self.firewall,line,line_num)
        servobj.name = name
        data = line.split()
        servobj.protocol = data[1]
        print data
        try:
            srcind = data.index('source')
            servobj.srcop = data[srcind+1]
        except ValueError:
            pass
        try:
            destind = data.index('destination')
            servobj.destop = data[destind+1]
        except ValueError:
            pass

        if servobj.srcop == 'range':
            print "do src range stuff"
            try:
                servobj.strt_srcport = int(data[srcind+2])
            except ValueError:
                servobj.strt_srcport = fws.asa_port_names[data[srcind+2]]
            try:
                servobj.end_srcport = int(data[srcind+3])
            except ValueError:
                servobj.end_srcport = fws.asa_port_names[data[srcind+3]]
        elif servobj.srcop == 'eq':
            print "do src equal stuff"
            try:
                servobj.strt_srcport = int(data[srcind+2])
            except ValueError:
                servobj.strt_srcport = fws.asa_port_names[data[srcind+2]]
        elif servobj.srcop == 'gt':
            try:
                servobj.strt_srcport = int(data[srcind+2])
            except ValueError:
                servobj.strt_srcport = fws.asa_port_names[data[srcind+2]]
            servobj.end_srcport = 65535
        elif servobj.destop == 'lt':
            servobj.strt_srcport = 1
            try:
                servobj.end_srcport = int(data[srcind+2])
            except ValueError:
                servobj.end_srcport = fws.asa_port_names[data[srcind+2]]
             
        if servobj.destop == 'range':
            print "do dest range stuff"
            try:
                servobj.strt_destport = int(data[destind+2])
            except ValueError:
                servobj.strt_destport = fws.asa_port_names[data[destind+2]]
            try:
                servobj.end_destport = int(data[destind+3])
            except ValueError:
                servobj.end_destport = fws.asa_port_names[data[destind+3]]
        elif servobj.destop == 'eq':
            print "do dest equal stuff"
            try:
                servobj.strt_destport = int(data[destind+2])
            except ValueError:
                servobj.strt_destport = fws.asa_port_names[data[destind+2]]
        elif servobj.destop == 'gt':
            try:
                servobj.strt_destport = int(data[destind+2])
            except ValueError:
                servobj.strt_destport = fws.asa_port_names[data[destind+2]]
            servobj.end_destport = 65535
        elif servobj.destop == 'lt':
            servobj.strt_destport = 1
            try:
                servobj.end_destport = int(data[destind+2])
            except ValueError:
                servobj.end_destport = fws.asa_port_names[data[destind+2]]
        
        print servobj
        print vars(servobj)
        self.firewall.service_objects.append(servobj)
        self.member_objects.append(servobj)

class AddressGroup(ObjectGroup):
    """Child of ObjectGroup class for handling service object groups"""
    def __init__(self,firewall,chunk,start_num):
        ObjectGroup.__init__(self,firewall,chunk,start_num)
        print "Hello this is a address group of vendor %s with OS %s"%(self.vendor,self.firmware)
    
    def add_addrobj(self,name):
        objs = filter(lambda obj: obj.name == name,self.firewall.address_objects)
        if len(objs) > 1:
            print "WOAH FOUND SOME DUPLICATE OBJECTS IN ADDRESS OBJECTS CONTAINER"
        self.member_objects += objs
    def add_group(self,name):
        objs = filter(lambda obj: obj.name == name,self.firewall.address_groups)
        if len(objs) > 1:
            print "WOAH FOUND SOME DUPLICATE OBJECTS IN ADDRESS OBJECTS CONTAINER"
        self.member_objects += objs
    def create_addrobj(self,line,kind,line_num,match):
        if kind == 'host':
            addrobj = fwa.AddressObject(self.firewall,line,line_num)
            addrobj.kind = kind
            addrobj.network_address = match.group(1)
            if match.group(2):
                addrobj.mask = match.group(2)
            else:
                addrobj.mask = '255.255.255.255'
        elif kind == 'network':
            addrobj = fwa.AddressObject(self.firewall,line,line_num)
            addrobj.kind = 'subnet'
            addrobj.network_address = match.group(1)
            addrobj.mask = match.group(2)
        else:
            raise NotImplementedError("This inline address object kind is not supported")
        self.firewall.address_objects.append(addrobj)
        self.member_objects.append(addrobj)
#####################################################################################################
def parse_addrgroup(firewall,chunk,start_num):
    """Call the correct parser function based on vendor and OS"""

    if firewall.vendor == 'cisco' and firewall.firmware == 'asa-9.0':
        return _parse_ciscoasa_9dot0_addrgroup(firewall,chunk,start_num)
    else:
        raise NotImplementedError("Sorry, the vendor and firmware combination you specified \
        is not supported")
#-----------------------------------------------------------------------------------------------------#
def parse_servgroup(firewall,chunk,start_num):
    """Call the correct parser function based on vendor and OS"""

    if firewall.vendor == 'cisco' and firewall.firmware == 'asa-9.0':
        return _parse_ciscoasa_9dot0_servgroup(firewall,chunk,start_num)
    else:
        raise NotImplementedError("Sorry, the vendor and firmware combination you specified \
        is not supported")
#####################################################################################################
def _parse_ciscoasa_9dot0_servgroup(firewall,chunk,start_num):
    print "Parsing cisco asa service group"
    servgroup = ServiceGroup(firewall,chunk,start_num)
    data = servgroup.text[servgroup.line_counter].split()
    if len(data) == 3:
        servgroup.name = data[-1]
    else:
        # Sometimes ASA's have these bullshit service group configs that are basically a way of
        # creating service objects in a big chunk. The protocol of all the inline service objects
        # will be the last string in the group definition
        servgroup.name = data[-2]
        servgroup.protocol = data[-1]

    firewall.lines_parsed[firewall.line_counter+servgroup.line_counter] = servgroup.text[servgroup.line_counter]
    servgroup.line_counter += 1  
    re_dict = {'inline-servobj':'^ service-object',
             'port-object':'port-object (eq|range) ([0-9]+$|([0-9]+) ([0-9]+)$|[A-z\._-]+|([A-z\._-]+) ([A-z\._-]+))'}
             # When specifying ports this way the port listed is the destination port
    while servgroup.line_counter < len(servgroup.text):
        line = servgroup.text[servgroup.line_counter]
        for obj,regex in re_dict.iteritems():
            match = re.search(regex,line)
            if match:
                firewall.lines_parsed[firewall.line_counter+servgroup.line_counter] = line
                if obj == 'inline-servobj':
                    name = servgroup.name + "_inline-servobj%d"%servgroup.line_counter
                    servgroup.create_servobj(line,servgroup.line_counter,name)
                elif obj == 'port-object':
                    print "Do port-object stuff"
                    op = match.group(1)
                    if op == 'eq':
                        try:
                            port = int(match.group(2))
                        except ValueError:
                            port = fws.asa_port_names[match.group(2)]
                    elif op == 'range':
                        try:
                            start_port = int(match.group(3))
                        except ValueError:
                            start_port = fws.asa_port_names[match.group(5)]

                        try:
                            end_port = int(match.group(4))
                        except ValueError:
                            end_port = fws.asa_port_names[match.group(6)]
                        servgroup.ports += range(start_port,end_port+1)
                    else: 
                        print "FOUND MYSTERY OPERATOR IN SERVICE GROUP INLINE PORT-OBJECT"
                        quit()
                    # This is kinda hacky, but just build a service object line to pass into the
                    # create_servobj function
                    line = 'service %s source range 1 65535 destination'%servgroup.protocol
                    if op == 'eq':
                        line += ' eq %d'%port
                    elif op == 'range':
                        line += ' range %d %d'%(start_port, end_port)
                    name = servgroup.name + "_inline-portobj%d"%servgroup.line_counter
                    servgroup.create_servobj(line,servgroup.line_counter,name)
                servgroup.line_counter += 1
                break
        if not match:
            firewall.lines_missed[firewall.line_counter+servgroup.line_counter] = line
            servgroup.line_counter += 1
    return servgroup

def _parse_ciscoasa_9dot0_addrgroup(firewall,chunk,start_num):
    print "Parsing cisco asa address group"
    addrgroup = AddressGroup(firewall,chunk,start_num)
    addrgroup.name = addrgroup.text[addrgroup.line_counter].split()[-1]
    firewall.lines_parsed[firewall.line_counter+addrgroup.line_counter] = addrgroup.text[addrgroup.line_counter]
    addrgroup.line_counter += 1 
    re_dict = {'address-object':'network-object object ([0-9A-z\._-]+)',
            'object-group':'group-object ([0-9A-z\._-]+)',
            'inline-host':'network-object host ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)[ ]*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)*',
            'inline-network':'network-object ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+) ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)',
            'description':'description ([.]+)'}
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
                elif obj == 'description':
                    addrgroup.description = match.group(1)
                elif obj == 'inline-host':
                    addrgroup.create_addrobj(line,'host',firewall.line_counter+addrgroup.line_counter,match)
                elif obj == 'inline-network':
                    addrgroup.create_addrobj(line,'network',firewall.line_counter+addrgroup.line_counter,match)
                addrgroup.line_counter += 1
                break
        if not match:
            firewall.lines_missed[firewall.line_counter+addrgroup.line_counter] = line
            addrgroup.line_counter +=1

    return addrgroup
