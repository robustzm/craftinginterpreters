//>= Chunks of Bytecode
#include <stdio.h>
#include <stdlib.h>

#include "common.h"
/*== Chunks of Bytecode
#include "chunk.h"
#include "debug.h"
*/
//>= Uhh
#include "vm.h"
//>= Scanning Without Allocating

#define MAX_LINE_LENGTH 1024

static void repl() {
  char line[MAX_LINE_LENGTH];
  for (;;) {
    printf("> ");
    
    if (!fgets(line, MAX_LINE_LENGTH, stdin)) {
      printf("\n");
      break;
    }
    
    interpret(line);
  }
}

// Reads the contents of the file at [path] and returns it as a heap allocated
// string.
//
// Exits if it was found but could not be found or read.
static char* readFile(const char* path) {
  FILE* file = fopen(path, "rb");
  if (file == NULL) {
    fprintf(stderr, "Could not find file \"%s\".\n", path);
    exit(74);
  }
  
  // Find out how big the file is.
  fseek(file, 0L, SEEK_END);
  size_t fileSize = ftell(file);
  rewind(file);
  
  // Allocate a buffer for it.
  char* buffer = (char*)malloc(fileSize + 1);
  if (buffer == NULL) {
    fprintf(stderr, "Could not read file \"%s\".\n", path);
    exit(74);
  }
  
  // Read the entire file.
  size_t bytesRead = fread(buffer, sizeof(char), fileSize, file);
  if (bytesRead < fileSize) {
    fprintf(stderr, "Could not read file \"%s\".\n", path);
    exit(74);
  }
  
  // Terminate the string.
  buffer[bytesRead] = '\0';
  
  fclose(file);
  return buffer;
}

static void runFile(const char* path) {
  char* source = readFile(path);
  InterpretResult result = interpret(source);
  free(source);
  
  if (result == INTERPRET_COMPILE_ERROR) exit(65);
  if (result == INTERPRET_RUNTIME_ERROR) exit(70);
}
//>= Chunks of Bytecode

int main(int argc, const char* argv[]) {
/*== Chunks of Bytecode
  Chunk chunk;
  initChunk(&chunk);
  
  addConstant(&chunk, 12.34);
  writeChunk(&chunk, OP_CONSTANT, 10);
  writeChunk(&chunk, 0, 1);

  addConstant(&chunk, 5.6);
  writeChunk(&chunk, OP_CONSTANT, 11);
  writeChunk(&chunk, 1, 1);

  disassembleChunk(&chunk, "test chunk");
*/
//>= A Virtual Machine
  initVM();
/*== A Virtual Machine
 
  uint8_t bytecode[] = {
    OP_CONSTANT, 0,
    OP_CONSTANT, 1,
    OP_ADD,
    OP_CONSTANT, 2,
    OP_MULTIPLY,
    OP_RETURN
  };
  double constants[] = {1.0, 2.0, 3.0};
  
  interpret(bytecode, constants);
*/
//>= Scanning Without Allocating
  
  if (argc == 1) {
    repl();
  } else if (argc == 2) {
    runFile(argv[1]);
  } else {
    fprintf(stderr, "Usage: cvox [path]\n");
    exit(64);
  }
//>= A Virtual Machine
  
  endVM();
//>= Chunks of Bytecode
  return 0;
}
