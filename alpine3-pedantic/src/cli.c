#include "cli.h"

#include "stdLib.h"

void *readCLI(void *_rcvdExitCmd) {
    bool *rcvdExitCmd = (bool *)_rcvdExitCmd;
    char line[50];
    int length = 0;

    // printf("CLI thread started\n");

    while (false == *rcvdExitCmd) {
        length = 0;
        while ((line[length] = getchar()) != '\n') {
            length++;
            if (length >= 49)
                break;
        }
        line[length] = '\0';

        if ((line[0] == 'q') && (strlen(line) == 1)) {
            *rcvdExitCmd = true;
            printf("Stopped by user\n");
        }
    }
    printf("CLI thread terminating\n");
    return NULL;
}