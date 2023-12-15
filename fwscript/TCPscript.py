from scapy.all import *
import logging

from scapy.layers.inet import IP, TCP

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

# 目标IP地址和端口
target_ip = "192.168.52.130"
target_port = 80

# TCP标志列表
tcp_flags = [
    'F',  # FIN flag
    'S',  # SYN flag
    'R',  # RST flag
    'P',  # PSH flag
    'A',  # ACK flag
    'U',  # URG flag
    'E'   # ECE flag
]

# 发送TCP包并监听响应
def firewall(ip, port, flags):
    for flag in flags:
        packet = IP(dst=ip)/TCP(dport=port, flags=flag)
        resp = sr1(packet, timeout=1, verbose=0)
        if resp:
            # 如果收到响应 说明包通过了防火墙
            print(f"Packet with {flag} flag passed through the firewall.")
        else:
            # 如果没有响应 说明包可能被防火墙拦截
            print(f"Packet with {flag} flag did not pass through the firewall.")

# 运行测试
if __name__ == '__main__':
    firewall(target_ip, target_port, tcp_flags)

