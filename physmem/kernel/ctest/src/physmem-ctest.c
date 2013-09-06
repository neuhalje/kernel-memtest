#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>

#include <phys_mem.h>



int main(int argc, char* argv[])
{
  int dev;
  int ret;

  dev = open("/dev/phys_mem", O_RDONLY);
  if (dev < 0)
  {
    fprintf(stderr, "Open error: %s\n", "/dev/phys_mem");
    return 1;
  }

 char r[200];
 size_t x;
/*
  struct phys_mem_request r;
  r.num_requests=0;
  r.protocol_version=1;
  r.req = NULL;
*/

  ret = ioctl(dev, 1074547456,&r);
  printf("Ret is %d\n",ret);


  close (dev);

  return 0;
}
