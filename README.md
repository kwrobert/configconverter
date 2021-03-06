# Configuration Converter

This project will one day be a tool to convert configurations files for firewalls, switches, and
routers from one vendor format to another. The goal is to save network engineers a bunch of time
they would have spent manually going through configs line by line and transferring objects, groups,
ACLs, etc. The basic idea is as follows. There exists a single object to represent the physical
piece of hardware (firewall, switch, or router). The object is always instantiated with the vendor,
firmware/OS version, and config file path as parameters. The file is immediately opened, all the
blank lines are removed, all trailing newlines/whitespaces stripped, and each line is then placed in
an array. These basic hardware objects have a universal .parse() method that is exposed to the user. 
It utilizes the vendor and OS attributes to pick the appropriate parser methods to execute. Right 
now the parser methods just loop through each line of the file and compare it to a dictionary of 
regular expressions that represent specific configuration items (for example, a physical interface 
or an address object). A line counter attribute keeps track of the current location in the file. 
When a match is found, the "chunk" of the configuration file that contains all the important info 
about that configuration item is passed off to another "sub-object" that represents that configuration 
item. That sub-object parses the chunk, extracts all the useful info, and stores the info in attributes. 
As the generic hardware object loops through the file is collects lists of these sub-objects as an 
attributes. Two dictionaries exist as attributes of the generic hardware object to keep tabs on 
which lines were successfully parsed and which lines were missed. There is no "formal grammar" or
"tokenizer" that governs the parsing. Perhaps this is a bad idea/design, if anyone reading this has
a better design or any ideas please feel free to let me know!
