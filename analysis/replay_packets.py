import socket
from scapy.all import *
import sys
from time import sleep

input_pcap = sys.argv[1]
dst_ip = sys.argv[2]
work_dir = sys.argv[3]

packets = rdpcap(input_pcap)

prev_timestamp = 0
i = 0
for pkt in packets:
    if prev_timestamp:
        sleep_time = pkt.time - prev_timestamp
        f = open("%s/debug/replay_packets.log"%work_dir, "a+")
        f.write("SLEEP %f\n"%sleep_time)
        f.close()
        time.sleep(sleep_time)
    else:
        sleep_time = 0

    prev_timestamp = pkt.time

    if pkt.haslayer(IP) and pkt[IP].payload:
        family = socket.AF_INET
        network_pkt = pkt[IP]
        if pkt[IP].haslayer(TCP) and pkt[TCP].payload:
            socket_type = socket.SOCK_STREAM
            transport_pkt = pkt[TCP]
        elif pkt[IP].haslayer(UDP) and pkt[UDP].payload:
            socket_type = socket.SOCK_DGRAM
            transport_pkt = pkt[UDP]
        elif pkt[IP].haslayer(SCTP) and pkt[SCTP].payload:
            socket_type = socket.SOCK_STREAM
            transport_pkt = pkt[SCTP]
        else:
            continue
    elif pkt.haslayer(IPv6) and pkt[IPv6].payload:
        family = socket.AF_INET6
        network_pkt = pkt[IPv6]
        if pkt[IPv6].haslayer(TCP) and pkt[TCP].payload:
            socket_type = socket.SOCK_STREAM
            transport_pkt = pkt[TCP]
        elif pkt[IPv6].haslayer(UDP) and pkt[UDP].payload:
            socket_type = socket.SOCK_DGRAM
            transport_pkt = pkt[UDP]
        elif pkt[IPv6].haslayer(SCTP) and pkt[SCTP].payload:
            socket_type = socket.SOCK_STREAM
            transport_pkt = pkt[SCTP]
        else:
            continue
    else:
        continue
    
    if network_pkt.dst == dst_ip:
        # print(pkt.time, sleep_time, pkt.show())
        sock = socket.socket(family, socket_type)
        sock.connect((network_pkt.dst, transport_pkt.dport))
        payload = bytes(transport_pkt.payload)
        sock.sendall(payload)
        sock.close()
    
        f = open("%s/debug/replay_packets.log"%work_dir, "a+")
        f.write("SENT PACKET %d\n"%i)
        f.close()
        i+=1

f = open("%s/debug/replay_packets.log"%work_dir, "a+")
f.write("FINISH!\n")
f.close()
