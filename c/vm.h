#ifndef cvox_vm_h
#define cvox_vm_h

#include "object.h"

#define MAX_STACK       256
#define MAX_FRAMES      64
#define MAX_HEAP        (10 * 1024 * 1024)

typedef enum {
  OP_CONSTANT,
  OP_NULL,
  OP_POP,
  OP_GET_LOCAL,
  OP_SET_LOCAL,
  OP_GET_GLOBAL,
  OP_DEFINE_GLOBAL,
  OP_SET_GLOBAL,
  OP_EQUAL,
  OP_GREATER,
  OP_LESS,
  OP_ADD,
  OP_SUBTRACT,
  OP_MULTIPLY,
  OP_DIVIDE,
  OP_NOT,
  OP_NEGATE,
  OP_JUMP,
  OP_JUMP_IF_FALSE,
  OP_LOOP,
  OP_CALL_0,
  OP_CALL_1,
  OP_CALL_2,
  OP_CALL_3,
  OP_CALL_4,
  OP_CALL_5,
  OP_CALL_6,
  OP_CALL_7,
  OP_CALL_8,
  OP_RETURN
} OpCode;

typedef struct {
  ObjFunction* function;
  uint8_t* ip;
  Value* slots;
} CallFrame;

struct sVM {
  Value stack[MAX_STACK];
  Value* stackTop;
  
  CallFrame frames[MAX_FRAMES];
  int frameCount;
  
  ObjTable* globals;
  
  size_t bytesAllocated;
  size_t nextGC;
  
  Obj* objects;
  
  int grayCount;
  int grayCapacity;
  Obj** grayStack;
};

typedef enum {
  INTERPRET_OK,
  INTERPRET_COMPILE_ERROR,
  INTERPRET_RUNTIME_ERROR
} InterpretResult;

// The singleton VM.
extern VM vm;

void initVM();
InterpretResult interpret(const char* source);
void endVM();

#endif
