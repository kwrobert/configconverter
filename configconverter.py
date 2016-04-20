#####################################################################################################
# Name: configconverter.py
# Author: Kyle Robertson
# Company: Worldcom Exchange Inc. 
# Description: This script retrieves the input from the user and initializes all objects depending
# on that input. 
#####################################################################################################

import argparse
import os
import firewalls as fw
import firewall_ports as fwp 
import json

def check_args(args):
    # Use this function to prevent the user from attempting an unsupported conversions
    
    
    # Catch any unsupported vendors and OS/firmware for a specific hardware type
    if args.device_type == 'firewall':
        allowed_vendors = ['fortinet','cisco']
    elif args.device_type == 'switch':
        allowed_vendors = []
    elif args.device_type == 'router':
        allowed_vendors = []
    else:
        print "You somehow managed to pass in an unsupported device"
        exit(1)
    
    if args.src_vendor not in allowed_vendors:
        raise ValueError("Source vendor %s isn't supported for hardware type %s"%(args.src_vendor,args.device_type))
    if args.dest_vendor not in allowed_vendors:
        raise ValueError("Destination vendor %s isn't supported for hardware type %s"%(args.dest_vendor,args.device_type))
    
    # Catch any unsupported src/dest firmware/OS combos for a given src vendor and hardware type
    if args.src_vendor == 'cisco' and args.device_type == 'firewall':
        # This should contain all supported source OS for given vendor
        allowed_src_OS = ['ciscoasa']
        allowed_dest_OS = ['testfortiOS']
    elif args.src_vendor == 'cisco' and args.device_type == 'switch':
        allowed_src_OS = []
        allowed_dest_OS = []
    elif args.src_vendor == 'cisco' and args.device_type == 'router':
        allowed_src_OS = []
        allowed_dest_OS = []
    elif args.src_vendor == 'fortinet' and args.device_type == 'firewall':
        allowed_src_OS = ['testfortiOS']
        allowed_dest_OS = ['ciscoasa']
    elif args.src_vendor == 'fortinet' and args.device_type == 'switch':
        allowed_src_OS = []
        allowed_dest_OS = []
    elif args.src_vendor == 'fortinet' and args.device_type == 'router':
        allowed_src_OS = []
        allowed_dest_OS = []
    else:
        print "You somehow managed to pass in an unsupported vendor"
        exit(1)

    if args.src_OS not in allowed_src_OS:
        raise ValueError("Source OS/firmware version %s isn't supported for vendor %s and hardware type%s"%(args.src_OS,args.src_vendor,args.device_type))
   
    if args.dest_OS not in allowed_dest_OS:
        raise ValueError("""Destination OS/firmware version %s isn't supported for vendor %s hardware type %s
                         when converting from source OS/firmware version %s with vendor %s"""%(args.dest_OS,args.dest_vendor,args.device_type,args.src_OS,args.src_vendor))
    
    if not os.path.isfile(args.src_config):
        raise ValueError("The source config file %s doesn't exist"%args.src_config)

def main():
    parser = argparse.ArgumentParser(description="""This is the main driver for the configuration
    converter program. It consumes the input from the user (hardware type, vendor, OS, and config
    file), then hands off the info to the other parts of the program to parse the input config,
    initialize objects,  convert, and generate output""")
    # Add 'switch' and 'router' to choices as they become supported
    parser.add_argument("device_type",type=str,metavar='device_type',choices=['firewall'],help="The type of device")
    # Add vendors to choices as they become supported. Remove vendor choices based on hardware type
    parser.add_argument("src_vendor",type=str,metavar='src_vendor',choices=['fortinet','cisco'],help="The vendor of the source device")
    parser.add_argument("dest_vendor",type=str,metavar='dest_vendor',choices=['fortinet','cisco'],help="The vendor of the destination device")
    # Add OS versions as they become available. Exclude choices based on hardware type and vendor 
    parser.add_argument("src_OS",type=str,metavar='src_OS',choices=['testfortiOS','ciscoasa'],help="The OS or firmware version of the source device")
    parser.add_argument("dest_OS",type=str,metavar='dest_OS',choices=['testfortiOS','ciscoasa'],help="The OS or firmware version of the destination device")
    parser.add_argument("src_config",type=str,help="The absolute path to the source configuration file")
    parser.add_argument("dest_config",type=str,default='output.conf',help="The path to the destination config file")
    args = parser.parse_args()
    
    # Make sure the supplied args are valid
    check_args(args)
   
    firewall = fw.parse_config(args.src_vendor,args.src_OS,args.src_config)
            
    print firewall.vendor
    print firewall.firmware
    print "Here are the lines we parsed"
    print firewall.lines_parsed.keys()
    print "Here are the lines we missed"
    print firewall.lines_missed.keys()
    if set(firewall.lines_parsed.keys()).intersection(firewall.lines_missed.keys()):
        print "You messed up, here are the lines that are in both dicts"
        print set(firewall.lines_parsed.keys()).intersection(firewall.lines_missed.keys()) 
    for line_num in sorted(firewall.lines_missed.keys()):
        print "%d: %s"%(line_num,firewall.lines_missed[line_num])
    
    missfile = os.path.join(os.path.dirname(args.dest_config),"lines_missed.txt")
    with open(missfile,'w+') as afile:
        for num in sorted(firewall.lines_missed.keys()):
            afile.write("%d: %s\n"%(num,firewall.lines_missed[num]))
    fw.write_config(args.dest_vendor,args.dest_OS,args.dest_config,firewall)

if __name__ == '__main__':
    main()
