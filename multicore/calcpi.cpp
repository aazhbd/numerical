#include <stdio.h>
#include <omp.h>

using namespace std;

int main() {
    int r[2801];
    int i, j, b, d, c = 0;

    #pragma omp parallel for
    for (i = 0; i < 2800; i++) {
        r[i] = 2000;
    }

    #pragma omp parallel for
    for (j = 2800; j > 0; j -= 14) {
        d = 0;

        i = j;
        while (1) {
            d += r[i] * 10000;
            b = 2 * i - 1;
            r[i] = d % b;
            d /= b;
            i--;
            if(i == 0) break;
            d *= i;
        }
        printf("%.4d", c + d / 10000);
        c = d % 10000;
    }
    printf("\n");

    return 0;
}
