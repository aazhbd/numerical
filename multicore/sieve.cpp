#include <iostream>
#include <chrono>
#include <math.h>

#define N 100

using namespace std;

int sieveSerial(int *comp) {
    int i, j, count = 0;
    comp[1] = 1;

	for(i = 2; i*i <= N; i++) {
		if(comp[i] != 1){
			for(j = i*i; j <= N; j += i){
				comp[j] = 1;
			}
		}
	}

	for(i = 2; i <= N; i++) {
		if(!comp[i]){
			count++;
		}
	}

    return count;
}

int sieveParallel(int *comp) {
    int i, j, count = 0;
    comp[1] = 1;
    int sq = (int) sqrt(N);

    #pragma omp parallel for
	for(i = 2; i <= sq; i++) {
		if(comp[i] != 1){
			for(j = i*i; j <= N; j += i){
				comp[j] = 1;
			}
		}
	}

    //#pragma omp parallel for
	for(i = 2; i <= N; i++) {
		if(!comp[i]){
			count++;
		}
	}

    return count;
}

int main() {
    int nums[N] = {0};
    int total_primes;

    auto ts1 = std::chrono::high_resolution_clock::now();
    total_primes = sieveSerial(nums);
    auto ts2 = std::chrono::high_resolution_clock::now();
    auto s_duration = std::chrono::duration_cast<std::chrono::microseconds>(ts2 - ts1).count();
    cout <<"Serial exec. Found total prime: "<<total_primes<<" and time taken: "<<s_duration<<endl;


    int nump[N] = {0};
    auto tp1 = std::chrono::high_resolution_clock::now();
    total_primes = sieveParallel(nump);
    auto tp2 = std::chrono::high_resolution_clock::now();
    auto p_duration = std::chrono::duration_cast<std::chrono::microseconds>(tp2 - tp1).count();
    cout <<"Parallel exec. Found total prime: "<<total_primes<<" and time taken: "<<p_duration<<endl;

    return 0;
}

