#
#
# Makefile IOT-AFL
# -----------------------------

all: 
	$(MAKE) -C AFL
	@echo "\033[32m[+]\033[0m Compilation Completed"

test_x86: 
	$(MAKE) -C AFL test_x86

afl-gcc: 
	$(MAKE) -C AFL afl-gcc
	@echo "\033[32m[+]\033[0m Compilation afl-gcc Completed"

afl-as: $(MAKE) -C AFL afl-as
	@echo "\033[32m[+]\033[0m Compilation afl-as Completed"

afl-fuzz: 
	$(MAKE) -C AFL afl-fuzz
	$(MAKE) -C AFL afl-fuzz_equafl
	@echo "\033[32m[+]\033[0m Compilation afl-fuzz Completed"

afl-showmap: 
	$(MAKE) -C AFL afl-showmap
	@echo "\033[32m[+]\033[0m Compilation afl-showmap Completed"

afl-tmin: 
	$(MAKE) -C AFL afl-tmin
	@echo "\033[32m[+]\033[0m Compilation afl-tmin Completed"

afl-analyze: 
	$(MAKE) -C AFL afl-analyze
	@echo "\033[32m[+]\033[0m Compilation afl-analyze Completed"

afl-gotcpu: 
	$(MAKE) -C AFL afl-gotcpu
	@echo "\033[32m[+]\033[0m Compilation afl-gotcpu Completed"

test_build: 
	$(MAKE) -C AFL test_build
	@echo "\033[32m[+]\033[0m Compilation test_build Completed"

all_done: 
	$(MAKE) -C AFL all_done

qemu_all:
	./build_qemu_support.sh all

afl-qemu-system-trace:
	./build_qemu_support.sh qemu

afl-qemu-trace :
	./build_qemu_support.sh user

.NOTPARALLEL: 
	$(MAKE) -C AFL publish

clean:
	$(MAKE) -C AFL clean

install: 
	$(MAKE) -C AFL install

publish:
	$(MAKE) -C AFL publish
	
