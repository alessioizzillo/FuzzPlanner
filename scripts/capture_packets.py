from scapy.all import sniff, IP, TCP, Raw, wrpcap
import signal
import sys
import os

sniffed_packets = []
outfile = None
target = None

def dump_intermediate_pcap():
    global outfile, sniffed_packets
    if not sniffed_packets:
        print("[+] No packets captured yet.")
        return
    try:
        wrpcap(outfile, sniffed_packets)
        print(f"[+] Intermediate packet dump saved to {outfile}")
    except Exception as e:
        print(f"[!] Error saving intermediate pcap: {e}")

def handle_dump_signal(signum, frame):
    sig_name = signal.Signals(signum).name
    print(f"\n[!] {sig_name} received: dumping intermediate pcap…")
    dump_intermediate_pcap()

    if signum == signal.SIGTSTP:
        os.kill(os.getpid(), signal.SIGCONT)

def handle_exit_signal(signum, frame):
    sig_name = signal.Signals(signum).name
    print(f"\n[!] {sig_name} received: dumping final pcap before exit…")
    dump_intermediate_pcap()
    sys.exit(0)

def packet_callback(packet):
    global sniffed_packets, target

    if IP in packet and TCP in packet:
        ip_dst = packet[IP].dst
        tcp_dport = packet[TCP].dport

        if ip_dst == target and tcp_dport == 80:
            payload = packet[TCP].payload
            if isinstance(payload, Raw):
                try:
                    data = payload.load.decode('utf-8')
                    print(f"HTTP Request → {ip_dst}:{tcp_dport}:\n{data}")
                except UnicodeDecodeError:
                    print(f"HTTP Request → {ip_dst}:{tcp_dport}: [binary]")
                sniffed_packets.append(packet)
            else:
                sniffed_packets.append(packet)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python capture_packets.py <interface> <target> <outfile>")
        print("Example: python capture_packets.py eth0 192.168.1.1 capture.pcap")
        sys.exit(1)

    interface = sys.argv[1] if sys.argv[1] != "127.0.0.1" else "lo"
    target    = sys.argv[2]
    outfile   = sys.argv[3]

    signal.signal(signal.SIGUSR1, handle_dump_signal)
    signal.signal(signal.SIGTSTP, handle_dump_signal)

    signal.signal(signal.SIGTERM, handle_exit_signal)
    signal.signal(signal.SIGINT, handle_exit_signal)

    print(f"[+] Sniffing on {interface}, targeting {target}, will write to {outfile}")
    print("[+] Send SIGUSR1 to dump on demand, Ctrl+Z to dump+resume, or SIGTERM/Ctrl+C to dump & exit.")

    try:
        sniff(iface=interface, prn=packet_callback, store=0)
    except PermissionError:
        print("[!] PermissionError: need root or sudo to sniff on this interface.")
    except Exception as e:
        print(f"[!] An error occurred: {e}")
    finally:
        if sniffed_packets:
            try:
                wrpcap(outfile, sniffed_packets)
                print(f"[+] Final dump saved to {outfile}")
            except Exception as e:
                print(f"[!] Error saving final pcap: {e}")
