#include <stdio.h>
#include <stdlib.h>
#include <string.h>

unsigned int calculate_serial(const char *login) {
    size_t len = strlen(login);

    if (len < 4) {
        fprintf(stderr, "Login must be at least 4 characters\n");
        exit(1);
    }

    unsigned int v4 = ((unsigned int)login[3] ^ 0x1337) + 6221293;

    for (size_t i = 0; i < len; i++) {
        v4 += (v4 ^ (unsigned int)login[i]) % 0x539;
    }

    return v4;
}

int main() {
    char login[256];

    printf("Enter login: ");
    fgets(login, sizeof(login), stdin);

    login[strcspn(login, "\n")] = '\0';

    unsigned int serial = calculate_serial(login);
    printf("Serial: %u\n", serial);

    return 0;
}


