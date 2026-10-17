/* ==============================================================================
 * OSify Bare-Metal Network Stack & NIC Driver (sistema/nucleo/kernel/include/osify_net.h)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Driver di rete Ethernet (Intel e1000 & Realtek RTL8139), stack di pacchetti
 * ARP, IPv4, UDP e client DHCP per configurazione automatica della connessione.
 * ==============================================================================
 */

#ifndef OSIFY_NET_H
#define OSIFY_NET_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

/* Intestazione Frame Ethernet II (14 byte) */
typedef struct {
    uint8_t  dest_mac[6];
    uint8_t  src_mac[6];
    uint16_t ethertype;     /* 0x0800 = IPv4, 0x0806 = ARP */
} __attribute__((packed)) osify_eth_hdr_t;

/* Intestazione Pacchetto ARP (28 byte) */
typedef struct {
    uint16_t hw_type;       /* 1 = Ethernet */
    uint16_t proto_type;    /* 0x0800 = IPv4 */
    uint8_t  hw_len;        /* 6 */
    uint8_t  proto_len;     /* 4 */
    uint16_t opcode;        /* 1 = Request, 2 = Reply */
    uint8_t  sender_mac[6];
    uint32_t sender_ip;
    uint8_t  target_mac[6];
    uint32_t target_ip;
} __attribute__((packed)) osify_arp_hdr_t;

/* Intestazione Pacchetto IPv4 (20 byte) */
typedef struct {
    uint8_t  ver_ihl;
    uint8_t  tos;
    uint16_t total_len;
    uint16_t id;
    uint16_t flags_frag;
    uint8_t  ttl;
    uint8_t  protocol;      /* 1 = ICMP, 6 = TCP, 17 = UDP */
    uint16_t checksum;
    uint32_t src_ip;
    uint32_t dest_ip;
} __attribute__((packed)) osify_ipv4_hdr_t;

/* Intestazione Datagramma UDP (8 byte) */
typedef struct {
    uint16_t src_port;
    uint16_t dest_port;
    uint16_t length;
    uint16_t checksum;
} __attribute__((packed)) osify_udp_hdr_t;

/* Costanti PCI Hardware Ethernet */
#define PCI_VENDOR_INTEL       0x8086
#define PCI_DEVICE_E1000_82540 0x100E
#define PCI_DEVICE_E1000_82545 0x1004
#define PCI_VENDOR_REALTEK     0x10EC
#define PCI_DEVICE_RTL8139     0x8139

/* Stato Scheda di Rete e Configurazione IP */
typedef struct {
    uint16_t vendor_id;
    uint16_t device_id;
    char     nic_name[32];
    uint8_t  mac_addr[6];
    uint32_t ip_addr;       /* es. 192.168.1.150 */
    uint32_t subnet_mask;   /* es. 255.255.255.0 */
    uint32_t gateway_ip;    /* es. 192.168.1.1 */
    uint32_t dns_server;    /* Quad9 9.9.9.9 per zero-telemetria */
    bool     link_up;
    bool     dhcp_acquired;
    uint32_t packets_rx;
    uint32_t packets_tx;
} osify_net_device_t;

/* Funzioni di Rete Bare-Metal */
void osify_net_init(void);
bool osify_net_send_packet(const void *data, size_t len);
void osify_net_handle_packet(const void *data, size_t len);
bool osify_net_dhcp_request(void);
bool osify_net_ping(uint32_t target_ip, uint32_t *latency_ms);
void osify_net_format_ip(uint32_t ip, char *buf, size_t len);
void osify_net_format_mac(const uint8_t *mac, char *buf, size_t len);
const osify_net_device_t *osify_net_get_device(void);

#endif /* OSIFY_NET_H */
