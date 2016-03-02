#include <stdio.h>

#include "debug.h"

void printValue(Value value) {
  switch (value->type) {
    case OBJ_ARRAY:
      printf("array[%d]", ((ObjArray*)value)->size);
      break;
      
    case OBJ_FORWARD:
      printf("fwd->%p", ((ObjForward*)value)->to);
      break;

    case OBJ_FUNCTION:
      printf("function");
      break;
      
    case OBJ_NUMBER:
      printf("%g", ((ObjNumber*)value)->value);
      break;
      
    case OBJ_STRING:
      printf("string[%d]", ((ObjString*)value)->length);
      break;
      
    case OBJ_TABLE:
      printf("table");
      break;
      
    case OBJ_TABLE_ENTRIES:
      printf("table entries");
      break;
  }
}

void printStack() {
  for (int i = 0; i < vm.stackSize; i++) {
    printf("%d: ", i);
    printValue(vm.stack[i]);
    printf("\n");
  }
}

void printFunction(ObjFunction* function) {
  for (int i = 0; i < function->codeSize;) {
    switch (function->code->chars[i++]) {
      case OP_CONSTANT: {
        uint8_t constant = function->code->chars[i++];
        printf("%-10s %5d '", "OP_CONSTANT", constant);
        printValue(function->constants->elements[constant]);
        printf("'\n");
        break;
      }
      case OP_ADD: printf("OP_ADD\n"); break;
      case OP_SUBTRACT: printf("OP_SUBTRACT\n"); break;
      case OP_MULTIPLY: printf("OP_MULTIPLY\n"); break;
      case OP_DIVIDE: printf("OP_DIVIDE\n"); break;
      case OP_RETURN: printf("OP_RETURN\n"); break;
    }
  }
  
  // TODO: Dump constant table?
}
