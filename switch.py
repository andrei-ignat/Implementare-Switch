import sys
import struct
import wrapper
import threading
import time
from wrapper import recv_from_any_link, send_to_link, get_switch_mac, get_interface_name

bridge_id_root = -1
lock = threading.Lock()
MAC_Table = {}
Table_v = {}
Int_Table = {}
port = {} 
path_cost_root = 0
own_bridge_id = -1
port_root = -1
bridge_id_root_bpdu = -1
path_cost_sender_bpdu = -1
bridge_id_sender_bpdu = -1

def parse_ethernet_header(data):
    """
    Parsează header-ul Ethernet pentru a extrage MAC de destinație, MAC sursă, EtherType și VLAN ID (dacă există).
    """
    dest_mac = data[0:6]
    src_mac = data[6:12]
    ether_type = (data[12] << 8) + data[13]

    vlan_id = -1
    if ether_type == 0x8200:  # Check pentru tag-ul VLAN 802.1Q
        vlan_tci = int.from_bytes(data[14:16], byteorder='big')
        vlan_id = vlan_tci & 0x0FFF  # Extrage VLAN ID (12 biți)
        ether_type = (data[16] << 8) + data[17]

    return dest_mac, src_mac, ether_type, vlan_id

def create_vlan_tag(vlan_id):
    """
    Creează tag-ul VLAN (header 802.1Q) pentru un VLAN specific.
    """
    return struct.pack('!H', 0x8200) + struct.pack('!H', vlan_id & 0x0FFF)

def is_unicast(str):
    return str != "FF:FF:FF:FF:FF:FF"
def send_bdpu_every_sec(interfaces, bridge_id_root_bpdu):
    """
    Trimite BPDU-uri (Bridge Protocol Data Units) la fiecare secundă pentru a menține spanning tree-ul.
    """
    while True:
        if own_bridge_id == bridge_id_root:
            for interface in interfaces:
                if Table_v[interface] == "TRUNK":
                    dst_mac = b'\x01\x80\xc2\x00\x00\x00'
                    src_mac = get_switch_mac()
                    root_bridge_id_bytes = bridge_id_root.to_bytes(8, byteorder="big")
                    sender_bridge_id_bytes = own_bridge_id.to_bytes(8, byteorder="big")
                    sender_path_cost_bytes = 0
                    sender_path_cost_bytes = sender_path_cost_bytes.to_bytes(4, byteorder="big")  # Costul căii pentru root este 0
                    dsap = 66
                    ssap = 66
                    control = 3
                    bpdu = (src_mac + dst_mac + root_bridge_id_bytes + sender_bridge_id_bytes + 
                            sender_path_cost_bytes + struct.pack('!B', dsap) + struct.pack('!B', ssap) + 
                            struct.pack('!B', control))
                    send_to_link(interface, len(bpdu), bpdu)
        time.sleep(1)

def receive_bpu(interfaces,interface):
    global bridge_id_root, path_cost_root, port_root, bridge_id_root_bpdu, path_cost_sender_bpdu, bridge_id_sender_bpdu
    with lock:
        if bridge_id_root_bpdu < bridge_id_root:
            path_cost_root = path_cost_sender_bpdu + 10
            port_root = interface
            if own_bridge_id == bridge_id_root:
                for i in interfaces:
                    if i != port_root:
                        if Table_v[i] == "TRUNK":
                            port[i] = "b"
            bridge_id_root = bridge_id_root_bpdu
            port[port_root] = "l"
             
        elif bridge_id_root_bpdu == bridge_id_root:
            if interface == port_root and path_cost_sender_bpdu + 10 < path_cost_root:
                path_cost_root = path_cost_sender_bpdu + 10
            elif interface != port_root:
                if path_cost_sender_bpdu > path_cost_root:
                    port[interface] = "l"
        elif bridge_id_sender_bpdu == own_bridge_id:
            port[interface] = "b"

    if own_bridge_id == bridge_id_root:
        for i in interfaces:
           port[i] = "l"
        

def main():
    switch_id = sys.argv[1]
    open_file = "./configs/switch" + str(switch_id) + ".cfg"
    
    # Inițializează interfața de rețea
    num_interfaces = wrapper.init(sys.argv[2:])
    interfaces = range(0, num_interfaces)

    global bridge_id_root
    global own_bridge_id
    global port_root
    global bridge_id_root_bpdu
    global bridge_id_sender_bpdu
    global path_cost_sender_bpdu


    for i in interfaces:
        Table_v[i] = "TRUNK"

    file_open = open(open_file,"r")  
    line_file = file_open.readlines()
    l1 = line_file[0]
    switch_priority = int(l1.split()[0])

    for i in interfaces:
        for line1 in line_file[1:]:
            string = line1.split()[0]
            if string == get_interface_name(i):
                vlan_value = line1.split()[1]
                Table_v[i] = int(vlan_value) if vlan_value.isdigit() else "TRUNK"

    for i in interfaces:
        if (Table_v.get(i) == "TRUNK"):
            port[i] = "b"
    own_bridge_id = switch_priority
    bridge_id_root = own_bridge_id
    path_cost_root = 0

    if own_bridge_id == bridge_id_root:
        for i in interfaces:
            port[i] = "l"

    print(f"# Pornire switch cu ID {switch_id}")
    print(f"[INFO] Switch MAC: {':'.join(f'{b:02x}' for b in get_switch_mac())}")

    t = threading.Thread(target=send_bdpu_every_sec, args=(interfaces, bridge_id_root_bpdu))
    t.start()

    while True:
        interface, data, length = recv_from_any_link()

        if data[6:12] == b'\x01\x80\xc2\x00\x00\x00':
            bridge_id_root_bpdu = int.from_bytes(data[12:20], byteorder='big')
            bridge_id_sender_bpdu = int.from_bytes(data[20:28], byteorder='big')
            path_cost_sender_bpdu = int.from_bytes(data[28:32], byteorder='big')
            receive_bpu(interfaces, interface)
        else:
            dest_mac, src_mac, ethertype, vlan_id = parse_ethernet_header(data)

            dest_mac = ':'.join(f'{b:02x}' for b in dest_mac)
            src_mac = ':'.join(f'{b:02x}' for b in src_mac)

            print(f'Destination MAC: {dest_mac}')
            print(f'Source MAC: {src_mac}')
            print(f'EtherType: {ethertype}')

            print(f"Received frame of size {length} on interface {interface}")


            MAC_Table[src_mac] = interface

            if is_unicast(dest_mac):
                if dest_mac in MAC_Table:
                    if vlan_id == -1:
                        vlan_id = Table_v[interface] if Table_v[interface] != "TRUNK" else 1
                        data = data[0:12] + create_vlan_tag(vlan_id) + data[12:]
                        length += 4
                        if Table_v.get(MAC_Table[dest_mac]) == "TRUNK" and port.get(MAC_Table[dest_mac]) == "l":
                            send_to_link(MAC_Table[dest_mac], len(data), data)
                        else:
                            data = data[0:12] + data[16:]
                            send_to_link(MAC_Table[dest_mac], len(data), data)
                    elif vlan_id != -1:
                        data = data[0:12] + data[16:]
                        length -= 4
                        if Table_v.get(MAC_Table[dest_mac]) == "TRUNK" and port.get(MAC_Table[dest_mac]) == "l":
                            data = data[0:12] + create_vlan_tag(vlan_id) + data[12:]
                            send_to_link(MAC_Table[dest_mac], length + 4, data)
                        else:
                            send_to_link(MAC_Table[dest_mac], length, data)


                else:
                    if vlan_id == -1:
                        vlan_id = Table_v[interface] if Table_v[interface] != "TRUNK" else 1
                        data = data[0:12] + create_vlan_tag(vlan_id) + data[12:]
                        length += 4
                        for i in interfaces:
                            if i != interface:
                                if Table_v.get(i) == "TRUNK" and port.get(i) == "l":
                                    send_to_link(i, length, data)
                                elif Table_v.get(i) == vlan_id:
                                    tag = data[0:12] + data[16:]
                                    send_to_link(i, len(tag), tag)

                    elif vlan_id != -1:
                        data = data[0:12] + data[16:]
                        length -= 4
                        for i in interfaces:
                            if i != interface:
                                if Table_v.get(i) == "TRUNK" and port.get(i) == "l":
                                    tag = data[0:12] + create_vlan_tag(vlan_id) + data[12:]
                                    send_to_link(i, len(tag), tag)
                                elif Table_v.get(i) == vlan_id:
                                    send_to_link(i, length, data)
            else:
                if vlan_id == -1:
                    vlan_id = Table_v[interface] if Table_v[interface] != "TRUNK" else 1
                    data = data[0:12] + create_vlan_tag(vlan_id) + data[12:]
                    length += 4
                    for i in interfaces:
                        if i != interface:
                            if i != interface and Table_v.get(i) == "TRUNK" and port.get(i) == "l":
                                send_to_link(i, length, data)
                            elif Table_v.get(i) == vlan_id:
                                tag = data[0:12] + data[16:]
                                send_to_link(i, len(tag), tag)
                elif vlan_id != -1:
                    data = data[0:12] + data[16:]
                    length -= 4
                    for i in interfaces:
                        if i != interface:
                            if Table_v.get(i) == "TRUNK" and port.get(i) == "l":
                                tag = data[0:12] + create_vlan_tag(vlan_id) + data[12:]
                                send_to_link(i, len(tag), tag)
                            elif Table_v.get(i) == vlan_id:
                                send_to_link(i, length, data)
if __name__ == "__main__":
    main()
