#include <iostream>
#include <stdlib.h>

using namespace std;

int main(int argv, char **argc) {
    int SIZE = 0, sum = 0;
    if(argv < 2) {
        cout<<"We need more parameters. Mention the size of the array."<<endl;
        return 1;
    }

    try {
        SIZE = atoi(argc[1]);
    }
    catch(std::exception const & e) {
        std::cout<<"error : " << e.what() <<endl;
    }

    int **first = new int*[SIZE];
    int **second = new int*[SIZE];
    int **result = new int*[SIZE];

    #pragma omp parallel for
    for(int i = 0; i < SIZE; i++) {
        first[i] = new int[SIZE];
        second[i] = new int[SIZE];
        result[i] = new int[SIZE];
        for(int j = 0; j < SIZE; j++) {
            first[i][j] = rand() % SIZE;
            second[i][j] = rand() % SIZE;
            result[i][j] = 0;
        }
    }

    #pragma omp parallel for
    for(int c = 0; c < SIZE; c++) {
        for(int d = 0; d < SIZE; d++) {
            for(int e = 0; e < SIZE; e++) {
                sum += first[c][d] * second[d][e];
                result[c][d] = sum;
            }
        }
    }

    delete first;
    delete second;
    delete result;

    return 0;
}
