import sys
import json

############## FILE LISTS ################

no_interest_file = [
    '/var/log/messages',
    '/etc/init.d/rcS',
    '.php',
    '.html',
    '/www/locale/en/charset',
    '.pem',
    '/usr/sbin/',
    '.tar.gz',
    '.pid',
    '/etc/services/svchlper'
]

low_interest_file = [
    'stunnel',
    '/etc/passwd',
    '/etc/TZ',
    '/etc/config/',
    '.sh',
    'zoneinfo'
]

medium_interest_file = [
    '.conf',
    '.xml',
    '.cfg'
]

############### VIRTUAL FILE LISTS ##############

no_interest_virtual_file = [
    '/proc/0',
    '/proc/1',
    '/proc/2',
    '/proc/3',
    '/proc/4',
    '/proc/5',
    '/proc/6',
    '/proc/7',
    '/proc/8',
    '/proc/9',
    '/sys/class/mem/',           # devices which are not externally pluggable devices and do not get data from outside
    '/sys/class/tty/tty',        # devices which are not externally pluggable devices and do not get data from outside
    '/sys/class/tty/console',    # devices which are not externally pluggable devices and do not get data from outside
    '/sys/class/tty/ptmx',       # (pseudo) devices which are not externally pluggable devices and do not get data from outside
    '/sys/class/tty/ptyp',       # (pseudo) devices which are not externally pluggable devices and do not get data from outside
    '/sys/class/mtd/',           # devices which are not externally pluggable devices and do not get data from outside
    '/sys/class/block/mtdblock', # devices which are not externally pluggable devices and do not get data from outside
    '/sys/class/block/ram',      # devices which are not externally pluggable devices and do not get data from outside
    '/sys/class/block/loop',     # devices which are not externally pluggable devices and do not get data from outside
    '/sys/class/block/mem',      # devices which are not externally pluggable devices and do not get data from outside
    '/sys/class/vc',             # devices which are not externally pluggable devices and do not get data from outside
    '/sys/class/tty/tty0',       # devices which are not externally pluggable devices and do not get data from outside
    '/sys/class/tty/tty1',
    '/sys/class/tty/tty2',
    '/sys/class/tty/tty3',
    '/sys/class/tty/tty4',
    '/sys/class/tty/tty5',
    '/sys/class/tty/tty6',
    '/sys/class/tty/tty7',
    '/sys/class/tty/tty8',
    '/sys/class/tty/tty9',
    '/sys/class/tty/ttyS',
    '/sys/class/tty/ttyp',
    '/sys/class/bsg/',           # devices which are not externally pluggable devices and do not get data from outside
    '/sys/class/pib/',           # devices which are not externally pluggable devices and do not get data from outside
    '/sys/class/rtc/',           # devices which are not externally pluggable devices and do not get data from outside
    '/sys/class/misc/tun/',      # devices which are not externally pluggable devices and do not get data from outside
    '/sys/class/misc/cpu_dma_latency/',  # devices which are not externally pluggable devices and do not get data from outside
    '/sys/class/misc/psaux/',    # devices which are not externally pluggable devices and do not get data from outside
    '/sys/class/misc/memory_bandwidth/', # devices which are not externally pluggable devices and do not get data from outside
    '/sys/class/misc/loop-control/',     # devices which are not externally pluggable devices and do not get data from outside
    '/sys/class/misc/vga_arbiter/',      # devices which are not externally pluggable devices and do not get data from outside
    '/sys/class/brcmboard/',              # devices which are not externally pluggable devices and do not get data from outside
    '/sys/class/i2c-dev/',               # devices which are not externally pluggable devices and do not get data from outside
    '/sys/class/input/mice/',            # devices which are not externally pluggable devices and do not get data from outside
    '/sys/class/nvram/',                 # devices which are not externally pluggable devices and do not get data from outside
    '/sys/class/graphics/',              # devices which are not externally pluggable devices and do not get data from outside
    '/sys/class/dsl_cpe_api/',           # devices which are not externally pluggable devices and do not get data from outside
    '/sys/class/zybtnio/',               # devices which are not externally pluggable devices and do not get data from outside
    '/sys/class/acos_nat_cli/',          # devices which are not externally pluggable devices and do not get data from outside
    '/sys/class/sc_led/',                # devices which are not externally pluggable devices and do not get data from outside
    '/proc/filesystems',
    '/proc/stat',
    '/proc/meminfo',
]

low_interest_virtual_file = [
    '/sys/class/block/sda',   # it may be related to an usb stick (hackable and externally pluggable)
    '/sys/class/ppp/',   # related to Ethernet or DSL (Digital Subscriber Line) or Cable Internet providers
    '/sys/class/misc/network_latency',    # Maybe settable
    '/sys/class/misc/network_throughput',
    '/sys/class/misc/tca',  # Network-related (TCA subsystem provides traffic control capabilities for managing network traffic)
    '/sys/class/tca', # Network-related
    'proc/sys/net/ipv6/conf/br0/disable_ipv6',     # Maybe settable
    'var/proc/web',     # related to web sessions
    '/proc/net/',
]

medium_interest_virtual_file = [
    '/proc/net/arp', # it contains a table that shows the mapping between IP addresses and corresponding MAC addresses
    '/proc/net/dev', # it contains a table with detailed statistics for each network interface on the system.
                     # It provides information such as the number of bytes and packets transmitted and received
]


############### DEVICE LISTS ##############

no_interest_device = [
    '/dev/pts/',    # pseudo terminal devices
    '/dev/urandom',

]

low_interest_device = [
    '/dev/mtdblock/',    # Writed by /usr/sbin/devconf
]

medium_interest_device = [

]



def assign_score(data_channels_dict):
    global no_interest_file
    global low_interest_file
    global medium_interest_file
    global no_interest_virtual_file
    global low_interest_virtual_file
    global medium_interest_virtual_file
    global no_interest_device
    global low_interest_device
    global medium_interest_device

    no_interest = no_interest_file+no_interest_device+no_interest_virtual_file
    low_interest = low_interest_file+low_interest_device+low_interest_virtual_file
    medium_interest = medium_interest_file+medium_interest_device+medium_interest_virtual_file

    for id in data_channels_dict:
        data_channels_dict[id]['score'] = 0.0
        # if data_channels_dict[id]["used"] == False:
        #     data_channels_dict[id]['score'] = 0.0
        if data_channels_dict[id]["kind"] == "inet_socket" or data_channels_dict[id]["kind"] == "inet6_socket":
            data_channels_dict[id]['score'] = 1.0
        elif data_channels_dict[id]["kind"] == "pipe" or data_channels_dict[id]["kind"] == "unix_socket":
            data_channels_dict[id]['score'] = 0.0
        elif id == 'file{path:}':
            data_channels_dict[id]['score'] = 0.0
        else:
            for token in no_interest:
                if token in id:
                    data_channels_dict[id]['score'] = 0.0

            for token in low_interest:
                if token in id:
                    data_channels_dict[id]['score'] = 0.15

            for token in medium_interest:
                if token in id:
                    data_channels_dict[id]['score'] = 0.5

    return data_channels_dict


if __name__ == '__main__':
    kind = sys.argv[1]
    json_file = sys.argv[2]

    data_channels = None
    with open(json_file) as file:
        data_channels = json.load(file)
    data_channels = {item['id']: {key: item[key] for key in item if key != 'id'} for item in data_channels}

    data_channels = assign_score(data_channels)

    data_channels_list = []
    for channel in data_channels:
        data_channels_list.append({"id" : channel, "kind" : data_channels[channel]["kind"], "used" : data_channels[channel]["used"], "listening_pids" : data_channels[channel]["listening_pids"], "score": data_channels[channel]["score"]})

    with open(json_file, "w") as f:
        f.write(json.dumps(data_channels_list, indent=4))

    for id in data_channels:
        print(data_channels[id])