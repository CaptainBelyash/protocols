
import argparse
import sys
import threading
import re
import socket
import struct
import time

WHOIS = re.compile(r'whois\.[\w]+\.net')
NETNAME = re.compile(r'netname:\s*(\S+)', re.IGNORECASE)
ORIGIN = re.compile(r'origina?s?:\s*(\S+)', re.IGNORECASE)
COUNTRY = re.compile(r'country:\s+(\S+)', re.IGNORECASE)


class PacketICMP:
    @staticmethod
    def build_packet():
        header = struct.pack("bbHHh", 8, 0, 0, 0, 1)
        data = struct.pack("d", time.time())
        checksum = socket.htons(PacketICMP.get_checksum(header + data))
        header = struct.pack("bbHHh", 8, 0, checksum, 0, 1)
        packet = header + data
        return packet

    @staticmethod
    def get_checksum(source_string):
        checksum = 0
        for i in range(0, len(source_string) - 1, 2):
            checksum += (source_string[i] << 8) + source_string[i + 1]
        checksum = (checksum >> 16) + (checksum & 0xffff)
        checksum += (checksum >> 16)
        return ~checksum & 0xffff


class WhoIS:
    @staticmethod
    def whois(ip, host='whois.iana.org'):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(5.0)
            sock.connect((host, 43))
            sock.sendall(socket.gethostbyname(ip).encode() + b'\n')
            data = WhoIS.get_data(sock)
            if not data:
                return 'local'
            try:
                info = WhoIS.get_info(data)
            except AttributeError:
                try:
                    host = WHOIS.search(data).group(0)
                except AttributeError:
                    return 'local'
                return WhoIS.whois(ip, host)
            return ", ".join(info)

    @staticmethod
    def get_data(sock):
        data = b''
        while True:
            try:
                raw_data = sock.recv(16)
                if not raw_data:
                    break
                data += raw_data
            except socket.timeout:
                return
        return data.decode(errors='replace')

    @staticmethod
    def get_info(data):
        info = []
        netname = NETNAME.search(data).group(1)
        system_number = ORIGIN.search(data).group(1)
        country = COUNTRY.search(data).group(1)
        info.append(netname)
        info.append(system_number)
        if country != "EU":
            info.append(country)
        return info


class TracertAS:
    def __init__(self, ip, ttl=100):
        self.destination = ip
        self.socket = None
        self.counter = 0
        self.max_ttl = ttl

    def ping(self):
        for ttl in range(1, self.max_ttl):
            self.send_packet(ttl)
            if self.receive_packet(ttl):
                self.socket.close()
                break

    def send_packet(self, ttl):
        self.socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_RAW,
            socket.IPPROTO_ICMP
        )
        self.socket.settimeout(0.2)
        self.socket.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_TTL,
            struct.pack('I', ttl)
        )
        self.socket.sendto(
            PacketICMP.build_packet(),
            (socket.gethostbyname(self.destination), 0)
        )

    def receive_packet(self, ttl):
        try:
            receive_packet, address = self.socket.recvfrom(1024)
            request_type, code, checksum, packet_ID, sequence = \
                struct.unpack("bbHHh", receive_packet[20:28])
            if request_type == 0 or request_type == 11:
                if self.counter == ttl - 1:
                    self.counter += 1
                    print(f'{self.counter}. {address[0]}\n'
                          f'{WhoIS.whois(address[0])}\n\n')
                if request_type == 0:
                    return True

        except socket.timeout:
            self.counter += 1
            print(f'{self.counter}. *\n\n\n')
            self.socket.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('ip', type=str, help='ip address or DNS name')
    args = parser.parse_args()
    ip = args.ip
    tracert = TracertAS(ip)
    thread = threading.Thread(target=tracert.ping, daemon=True)
    try:
        socket.gethostbyname(ip)
    except socket.gaierror:
        print(ip + ' is invalid', file=sys.stderr)
        sys.exit(1)
    thread.start()
    thread.join()


if __name__ == '__main__':
    main()
