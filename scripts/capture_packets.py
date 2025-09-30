from scapy.all import sniff, IP, TCP, Raw, wrpcap
import sys

sniffed_packets = []
blacklist_keywords = []
whitelist_keywords = []

def packet_callback(packet):
    global blacklist_keywords, whitelist_keywords

    if IP in packet and TCP in packet:
        ip_src = packet[IP].src
        ip_dst = packet[IP].dst
        tcp_dst = packet[TCP].dport

        if ip_dst == target and tcp_dst == 80:
            payload = packet[TCP].payload

            if isinstance(payload, Raw):
                payload_bytes = payload.load
                try:
                    payload_str = payload_bytes.decode('utf-8')

                    if any(w in payload_str for w in whitelist_keywords):
                        print(f"HTTP Request (whitelisted) from {ip_src} to {ip_dst} (Port {tcp_dst}):\n{payload_str}")
                        sniffed_packets.append(packet)
                        return

                    if any(b in payload_str for b in blacklist_keywords):
                        return

                    print(f"HTTP Request from {ip_src} to {ip_dst} (Port {tcp_dst}):\n{payload_str}")
                except UnicodeDecodeError:
                    print(f"HTTP Request from {ip_src} to {ip_dst} (Port {tcp_dst}):\n[Binary Data]")
                    sniffed_packets.append(packet)
                    return
                sniffed_packets.append(packet)
            else:
                sniffed_packets.append(packet)

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: python script.py <interface> <target> <outfile> <blacklist_keywords> <whitelist_keywords>")
        print("Example: python script.py eth0 192.168.1.1 out.pcap \".htm .jpg\" \"login password\"")
        sys.exit(1)

    interface = sys.argv[1] if sys.argv[2] != "127.0.0.1" else "lo"
    target = sys.argv[2]
    outfile = sys.argv[3]
    blacklist_keywords = sys.argv[4].split()
    whitelist_keywords = sys.argv[5].split()

    try:
        sniff(iface=interface, prn=packet_callback, store=0)
    except PermissionError:
        print("PermissionError: You may not have sufficient privileges to capture packets on this interface.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        try:
            wrpcap(outfile, sniffed_packets)
            print(f"Packets saved to {outfile}")
        except Exception as e:
            print(f"Error saving packets to {outfile}: {e}")