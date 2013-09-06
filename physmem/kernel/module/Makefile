obj-m := phys_mem.o

phys_mem-objs := main.o file_operations.o  mmap_phys.o
phys_mem-objs += page_claiming/page_claiming.o

phys_mem-objs += page_claiming/free_page_claiming.o
phys_mem-objs += page_claiming/free_buddy_page_claiming.o
phys_mem-objs += page_claiming/page_cache_claiming.o
phys_mem-objs += page_claiming/anon_page_claiming.o
phys_mem-objs += page_claiming/helper.o
phys_mem-objs += page_claiming/page_alloc_copy.o
phys_mem-objs += page_claiming/hwpoison/hw_poison_claiming.o
phys_mem-objs += page_claiming/hwpoison/memory-failure_clone.o
phys_mem-objs += page_claiming/difficult_pages.o



EXTRA_CFLAGS += -I$(PWD)/include

EXTRA_CFLAGS += -DUSE_HW_POISON_IMPLEMENTATION_CLONEx

KDIR  := /lib/modules/$(shell uname -r)/build
PWD   := $(shell pwd)


.PHONY: all
all: clean module

module:
	echo $(EXTRA_CFLAGS)
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE)  -C $(KDIR) M=$(PWD) clean

test: module
	sudo phys_mem.ko
	sudo ../test/tests.sh || true
	sudo rmmod phys_mem
