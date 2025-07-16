import socket
from scapy.all import *
import sys
from time import sleep
import errno

input_pcap = sys.argv[1]
dst_ip = sys.argv[2]
work_dir = sys.argv[3]

with open(f"{work_dir}/debug/replay_packets.log", "a+") as f:
    f.write(f"input_pcap {input_pcap}\n")

packets = rdpcap(input_pcap)

prev_timestamp = 0
i = 0
first_tcp_connection_successful = False

for pkt in packets:
    if prev_timestamp:
        sleep_time = pkt.time - prev_timestamp
        with open(f"{work_dir}/debug/replay_packets.log", "a+") as f:
            f.write(f"SLEEP {sleep_time:.6f}\n")
        sleep(float(sleep_time))
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
        payload = bytes(transport_pkt.payload)

        if socket_type == socket.SOCK_STREAM:
            connected = False

            if not first_tcp_connection_successful:
                while not connected:
                    sock = socket.socket(family, socket_type)
                    sock.settimeout(1.0)
                    try:
                        sock.connect((network_pkt.dst, transport_pkt.dport))
                        connected = True
                        first_tcp_connection_successful = True
                    except (socket.timeout, socket.error) as e:
                        with open(f"{work_dir}/debug/replay_packets.log", "a+") as f:
                            f.write(f"[INIT] Retry TCP to {network_pkt.dst}:{transport_pkt.dport} — {str(e)}\n")
                        sleep(0.1)
                        sock.close()
                        continue
            else:
                max_retries = 10
                retry_count = 0

                while retry_count < max_retries and not connected:
                    sock = socket.socket(family, socket_type)
                    sock.settimeout(1.0)
                    try:
                        sock.connect((network_pkt.dst, transport_pkt.dport))
                        connected = True
                    except (socket.timeout, socket.error) as e:
                        retry_count += 1
                        with open(f"{work_dir}/debug/replay_packets.log", "a+") as f:
                            f.write(f"Retry {retry_count}/{max_retries} TCP to {network_pkt.dst}:{transport_pkt.dport} — {str(e)}\n")
                        sleep(0.1)
                        sock.close()
                        continue

                if not connected:
                    with open(f"{work_dir}/debug/replay_packets.log", "a+") as f:
                        f.write(f"Failed to connect to {network_pkt.dst}:{transport_pkt.dport} after {max_retries} retries\n")
                    continue

            try:
                sock.sendall(payload)
            finally:
                sock.close()

        else:
            sock = socket.socket(family, socket_type)
            sock.settimeout(1.0)
            sock.sendto(payload, (network_pkt.dst, transport_pkt.dport))
            sock.close()

        with open(f"{work_dir}/debug/replay_packets.log", "a+") as f:
            f.write(f"SENT PACKET {i}\n")
        i += 1

with open(f"{work_dir}/debug/replay_packets.log", "a+") as f:
    f.write("FINISH!\n")
