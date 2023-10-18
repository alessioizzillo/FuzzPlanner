typedef struct {
    char * aflFile;
    int buf_read_index;
} SharedVariables;

extern SharedVariables *extern_struct;
extern int debug;
extern int debug_pc;