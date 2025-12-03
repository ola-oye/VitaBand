#!/usr/bin/env python3
"""
mDNS Service Advertiser & Discovery for VitaBand Health Monitoring System

Advertises the health monitoring service on the local network
so mobile apps can automatically discover it.

Discovery also included for testing / mobile simulation.
"""

import socket
import time
from zeroconf import (
    Zeroconf, ServiceInfo, ServiceBrowser, ServiceStateChange, InterfaceChoice
)


# Utility helping functions

def safe_decode(value):
    """Decode bytes → string safely."""
    if isinstance(value, bytes):
        try:
            return value.decode()
        except:
            return str(value)
    return value


def get_local_ip():
    """Get local IPv4 address safely."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# Advertiser

class HealthMonitorService:
    """
    Advertises health monitoring service via mDNS/Zeroconf
    """

    SERVICE_TYPE = "_mqtt._tcp.local."

    def __init__(self, service_name="VitaBand", port=1883):
        self.service_name = service_name
        self.port = port
        self.zeroconf = None
        self.info = None

        print(f"[INIT] mDNS Service initialized: {service_name}")

    def start(self):
        """Start advertising the service."""
        try:
            local_ip = get_local_ip()
            hostname = socket.gethostname()

            print(f"[INFO] Local IP: {local_ip}")
            print(f"[INFO] Hostname: {hostname}.local")

            # Fix double-dot issue
            service_full_name = f"{self.service_name}.{self.SERVICE_TYPE}"

            # Create service info
            self.info = ServiceInfo(
                type_=self.SERVICE_TYPE,
                name=service_full_name,
                server=f"{hostname}.local.",
                port=self.port,
                properties={
                    b"version": b"1.0",
                    b"service": b"health-monitoring",
                    b"description": b"Real-time health and activity monitoring",
                },
                addresses=[socket.inet_aton(local_ip)],
            )

            # Zeroconf instance (IPv4 only for reliability)
            self.zeroconf = Zeroconf(interfaces=InterfaceChoice.Default)

            print(f"\n[ADVERTISE] Broadcasting service: {self.service_name}")
            print(f"  Type: {self.SERVICE_TYPE}")
            print(f"  Host: {hostname}.local")
            print(f"  IP:   {local_ip}:{self.port}")

            self.zeroconf.register_service(self.info)

            print("\n✓ Service advertised successfully!")
            print(f"\n→ Discoverable as:")
            print(f"  - Name: {self.service_name}")
            print(f"  - Host: {hostname}.local")
            print(f"  - MQTT: mqtt://{local_ip}:{self.port}\n")

            return True

        except Exception as e:
            print(f"✗ Failed to start mDNS service: {e}")
            return False

    def stop(self):
        """Stop advertising the mDNS service."""
        try:
            if self.zeroconf and self.info:
                print("\n[STOP] Unregistering mDNS service...")
                self.zeroconf.unregister_service(self.info)
                self.zeroconf.close()
                print("✓ mDNS service stopped")
        except Exception as e:
            print(f"[ERROR] Failed to stop service: {e}")


# Discovery Listener (Modern API)

class MDNSListener:
    """Handles added/removed/updated services."""

    def __init__(self, target_list):
        self.target_list = target_list

    def add_service(self, zeroconf, service_type, name):
        info = zeroconf.get_service_info(service_type, name)
        if not info:
            return

        props = {
            safe_decode(k): safe_decode(v)
            for k, v in info.properties.items()
        }

        # Only track our target service
        if props.get("service") != "health-monitoring":
            return

        addresses = [socket.inet_ntoa(addr) for addr in info.addresses]

        entry = {
            "name": name,
            "host": info.server,
            "port": info.port,
            "address": addresses[0] if addresses else "unknown",
            "properties": props,
        }

        self.target_list.append(entry)

        print(f"  ✓ Found service: {name}")

    def update_service(self, *args):
        pass  # Not needed for your use case

    def remove_service(self, *args):
        pass


# Discovery Tool

class ServiceDiscovery:
    """Discovers VitaBand services via mDNS."""

    SERVICE_TYPE = "_mqtt._tcp.local."

    def __init__(self):
        self.zeroconf = None
        self.discovered_services = []

        print("[INIT] Service Discovery initialized")

    def discover(self, timeout=5):
        """Discover mDNS services."""

        print(f"\n[DISCOVERY] Searching for services ({timeout}s)...")

        self.discovered_services = []
        self.zeroconf = Zeroconf(interfaces=InterfaceChoice.Default)

        listener = MDNSListener(self.discovered_services)
        browser = ServiceBrowser(self.zeroconf, self.SERVICE_TYPE, listener)

        time.sleep(timeout)  # Wait for events

        self.zeroconf.close()

        if self.discovered_services:
            print(f"\n✓ Found {len(self.discovered_services)} service(s):")
            for i, svc in enumerate(self.discovered_services, 1):
                print(f"\n  Service {i}:")
                print(f"    Name: {svc['name']}")
                print(f"    Host: {svc['host']}")
                print(f"    Address: {svc['address']}:{svc['port']}")
                print(f"    Properties: {svc['properties']}")
        else:
            print("\n✗ No health-monitoring services found")

        return self.discovered_services


# Test Tools (Advertiser & Discovery)

def test_mdns_advertiser():
    print("=" * 70)
    print("TESTING mDNS SERVICE ADVERTISER")
    print("=" * 70)

    service = HealthMonitorService("Health Monitor", 1883)

    if service.start():
        print("\nService is now discoverable on the network!")
        print("Press Ctrl+C to stop...\n")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopped by user")

    service.stop()


def test_mdns_discovery():
    print("=" * 70)
    print("TESTING mDNS SERVICE DISCOVERY")
    print("=" * 70)

    print("Searching for devices running integrated_system.py...\n")

    discovery = ServiceDiscovery()
    services = discovery.discover(timeout=5)

    if services:
        print("\nAvailable MQTT Service Endpoints:")
        for svc in services:
            print(f"  mqtt://{svc['address']}:{svc['port']}")
    else:
        print("\n⚠️ No services detected.")
        print("Make sure the advertiser is running on local network.\n")


# Main

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--discover":
        test_mdns_discovery()
    else:
        test_mdns_advertiser()
