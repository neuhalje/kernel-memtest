#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>

#define PAGESIZE  (4096)
#define SIZE (1024*PAGESIZE*4)

int main(int argc, char *argv[])
{
    int i;
    int fd = -1;
    int *map; 


    map = mmap(0, SIZE, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANONYMOUS, fd, 0);
    if (map == MAP_FAILED) {
	perror("Error mmapping");
	exit(EXIT_FAILURE);
    }
    
    long maxIdx = SIZE/sizeof(int);

// "endless"
    int maxLoops = 0;
    while(1 || maxLoops--){
        for (i = 0; i < maxIdx; i++) {
	    map[i] = 42;
        }
    }

    if (munmap(map, SIZE) == -1) {
	perror("Error un-mmapping the file");
    }
    return 0;
}
