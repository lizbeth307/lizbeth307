"""Active protocol probing — працює без root і без pcap."""

from __future__ import annotations

import random
import socket
import struct
import time
from dataclasses import dataclass


@dataclass
class ProbeMessage:
    proto: str
    label: str
    direction: str  # request | response
    raw: bytes


def _dns_encode_name(domain: str) -> bytes:
    out = bytearray()
    for label in domain.strip(".").split("."):
        out.append(len(label))
        out.extend(label.encode("ascii"))
    out.append(0)
    return bytes(out)


def _dns_build_query(qid: int, domain: str) -> bytes:
    header = struct.pack(">HHHHHH", qid, 0x0100, 1, 0, 0, 0)
    return header + _dns_encode_name(domain) + struct.pack(">HH", 1, 1)


def probe_dns(
    domains: list[str] | None = None,
    servers: list[str] | None = None,
    timeout: float = 2.0,
) -> list[ProbeMessage]:
    domains = domains or [
        "google.com", "github.com", "cloudflare.com", "cursor.com", "example.com",
    ]
    servers = servers or ["1.1.1.1", "8.8.8.8", "9.9.9.9"]
    out: list[ProbeMessage] = []

    for server in servers:
        for domain in domains:
            qid = random.randint(0, 0xFFFF)
            query = _dns_build_query(qid, domain)
            out.append(ProbeMessage("udp", f"DNS:{server}", "request", query))
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(timeout)
                sock.sendto(query, (server, 53))
                resp, _ = sock.recvfrom(4096)
                out.append(ProbeMessage("udp", f"DNS:{server}", "response", resp))
            except OSError:
                pass
            finally:
                try:
                    sock.close()
                except Exception:
                    pass
    return out


def probe_ntp(servers: list[str] | None = None, timeout: float = 2.0) -> list[ProbeMessage]:
    servers = servers or ["pool.ntp.org", "time.google.com", "1.1.1.1"]
    out: list[ProbeMessage] = []
    req = bytes([0x23] + [0] * 47)
    for host in servers:
        out.append(ProbeMessage("udp", f"NTP:{host}", "request", req))
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            sock.sendto(req, (host, 123))
            resp, _ = sock.recvfrom(256)
            if len(resp) >= 48:
                out.append(ProbeMessage("udp", f"NTP:{host}", "response", resp[:48]))
        except OSError:
            pass
        finally:
            try:
                sock.close()
            except Exception:
                pass
    return out


def _minimal_tls_client_hello() -> bytes:
    """TLS Handshake record (спрощений ClientHello-подібний буфер для AST)."""
    body = bytes([0x01, 0x00, 0x00, 0x74, 0x03, 0x03] + [0] * 32 + [0x00, 0x0A])
    return struct.pack(">BHH", 0x16, 0x0301, len(body)) + body


def probe_tls(
    hosts: list[tuple[str, int]] | None = None,
    timeout: float = 3.0,
) -> list[ProbeMessage]:
    """TCP TLS handshake bytes (без розшифрування — лише record layer)."""
    hosts = hosts or [
        ("cloudflare.com", 443),
        ("github.com", 443),
        ("1.1.1.1", 443),
    ]
    hello = _minimal_tls_client_hello()
    out: list[ProbeMessage] = []
    for host, port in hosts:
        out.append(ProbeMessage("tcp", f"TLS:{host}", "request", hello))
        try:
            sock = socket.create_connection((host, port), timeout=timeout)
            sock.settimeout(timeout)
            sock.sendall(hello)
            resp = sock.recv(8192)
            if resp:
                out.append(ProbeMessage("tcp", f"TLS:{host}", "response", resp))
            sock.close()
        except OSError:
            pass
    return out


def probe_http_hosts(timeout: float = 2.0) -> list[ProbeMessage]:
    """HTTP response bytes (часто gzip/HTML — структура все одно видна)."""
    out: list[ProbeMessage] = []
    for host in ("example.com", "httpbin.org"):
        try:
            sock = socket.create_connection((host, 80), timeout=timeout)
            req = f"GET / HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n".encode()
            out.append(ProbeMessage("tcp", f"HTTP:{host}", "request", req))
            sock.sendall(req)
            resp = b""
            sock.settimeout(timeout)
            while True:
                try:
                    part = sock.recv(4096)
                    if not part:
                        break
                    resp += part
                    if len(resp) > 8192:
                        break
                except socket.timeout:
                    break
            if resp:
                out.append(ProbeMessage("tcp", f"HTTP:{host}", "response", resp))
            sock.close()
        except OSError:
            pass
    return out


def run_active_probes() -> dict[str, list[bytes]]:
    """Повертає групи повідомлень за міткою потоку."""
    groups: dict[str, list[bytes]] = {}
    all_probes = (
        probe_dns()
        + probe_ntp()
        + probe_tls()
        + probe_http_hosts()
    )
    for msg in all_probes:
        key = msg.label.replace(":", "_")
        groups.setdefault(key, []).append(msg.raw)
    return groups
