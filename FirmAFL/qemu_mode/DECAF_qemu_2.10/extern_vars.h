#define MAX_PROCESS_NAME_LENGTH 30
extern int debug;
extern int debug_pc;
extern int fuzz;
extern int target_syscall;
extern unsigned long target_pc;
extern char *target_pattern;
extern int execution_mode;
extern char *target_exec;
extern char *target_channel;
extern int ignore_addr;
extern int init_syscalls[4];
extern int target_syscalls[4];
extern unsigned long cur_program_pc;
