#include <stdlib.h>

#include "common.h"
#include "compiler.h"
#include "memory.h"
#include "object.h"
#include "vm.h"

#ifdef DEBUG_TRACE_GC
#include <stdio.h>
#include "debug.h"
#endif

void* reallocate(void* previous, size_t size) {
#ifdef DEBUG_STRESS_GC
  collectGarbage();
#endif
  
  // TODO: Tune this or come up with better algorithm.
  // TODO: Doesn't take into account growing an existing allocation.
  vm.bytesAllocated += size;
  if (vm.bytesAllocated > 1024 * 1024 * 10) {
    collectGarbage();
    vm.bytesAllocated = 0;
  }
  
  return realloc(previous, size);
}

// TODO: "Object" or "obj"?
void grayObject(Obj* obj) {
  // TODO: Remove this when nil is a separate value type.
  if (obj == NULL) return;
  
  // Don't get caught in cycle.
  if (obj->isDark) return;
  
#ifdef DEBUG_TRACE_GC
  printf("%p gray ", value);
  printValue(value);
  printf("\n");
#endif
  
  obj->isDark = true;
  
  if (vm.grayCapacity < vm.grayCount + 1) {
    vm.grayCapacity = vm.grayCapacity == 0 ? 4 : vm.grayCapacity * 2;
    // Not using reallocate() here because we don't want to trigger the GC
    // inside a GC!
    vm.grayStack = realloc(vm.grayStack, sizeof(Obj*) * vm.grayCapacity);
  }
  
  vm.grayStack[vm.grayCount++] = obj;
}

void grayValue(Value value) {
  if (!IS_OBJ(value)) return;
  grayObject(AS_OBJ(value));
}

static void grayArray(ValueArray* array) {
  for (int i = 0; i < array->count; i++) {
    grayValue(array->values[i]);
  }
}

static void blackenObject(Obj* obj) {
#ifdef DEBUG_TRACE_GC
  printf("%p blacken ", obj);
  printValue((Value)obj);
  printf("\n");
#endif
  
  switch (obj->type) {
    case OBJ_BOUND_METHOD: {
      ObjBoundMethod* bound = (ObjBoundMethod*)obj;
      grayValue(bound->receiver);
      grayObject((Obj*)bound->method);
      break;
    }
      
    case OBJ_CLASS: {
      ObjClass* klass = (ObjClass*)obj;
      grayObject((Obj*)klass->name);
      grayTable(&klass->methods);
      break;
    }
      
    case OBJ_CLOSURE: {
      ObjClosure* closure = (ObjClosure*)obj;
      grayObject((Obj*)closure->function);
      for (int i = 0; i < closure->function->upvalueCount; i++) {
        grayObject((Obj*)closure->upvalues[i]);
      }
      break;
    }
      
    case OBJ_FUNCTION: {
      ObjFunction* function = (ObjFunction*)obj;
      grayObject((Obj*)function->name);
      grayArray(&function->constants);
      break;
    }
      
    case OBJ_INSTANCE: {
      ObjInstance* instance = (ObjInstance*)obj;
      grayObject((Obj*)instance->klass);
      grayTable(&instance->fields);
      break;
    }
      
    case OBJ_UPVALUE:
      grayValue(((ObjUpvalue*)obj)->closed);
      break;
      
    case OBJ_NATIVE:
    case OBJ_STRING:
      // No references.
      break;
  }
}

static void freeObject(Obj* obj) {
#ifdef DEBUG_TRACE_GC
  printf("%p free ", obj);
  printValue((Value)obj);
  printf("\n");
#endif
  
  switch (obj->type) {
    case OBJ_CLASS: {
      ObjClass* klass = (ObjClass*)obj;
      freeTable(&klass->methods);
      break;
    }

    case OBJ_CLOSURE: {
      ObjClosure* closure = (ObjClosure*)obj;
      free(closure->upvalues);
      break;
    }
      
    case OBJ_FUNCTION: {
      ObjFunction* function = (ObjFunction*)obj;
      free(function->code);
      freeArray(&function->constants);
      break;
    }
      
    case OBJ_INSTANCE: {
      ObjInstance* instance = (ObjInstance*)obj;
      freeTable(&instance->fields);
      break;
    }
      
    case OBJ_BOUND_METHOD:
    case OBJ_NATIVE:
    case OBJ_STRING:
    case OBJ_UPVALUE:
      // No separately allocated memory.
      break;
  }
  
  free(obj);
}

void collectGarbage() {
#ifdef DEBUG_TRACE_GC
  printf("-- gc --\n");
#endif
  
  // Mark the stack roots.
  for (Value* slot = vm.stack; slot < vm.stackTop; slot++) {
    grayValue(*slot);
  }
  
  for (int i = 0; i < vm.frameCount; i++) {
    grayObject((Obj*)vm.frames[i].closure);
  }
  
  // Mark the open upvalues.
  for (ObjUpvalue* upvalue = vm.openUpvalues;
       upvalue != NULL;
       upvalue = upvalue->next) {
    grayObject((Obj*)upvalue);
  }
  
  // Mark the global roots.
  grayTable(&vm.globals);
  grayCompilerRoots();
  grayObject((Obj*)vm.initString);
  
  // Traverse the references.
  while (vm.grayCount > 0) {
    // Pop an item from the gray stack.
    Obj* obj = vm.grayStack[--vm.grayCount];
    blackenObject(obj);
  }
  
  // Delete unused interned strings.
  tableRemoveWhite(&vm.strings);
  
  // Collect the white objects.
  Obj** obj = &vm.objects;
  while (*obj != NULL) {
    if (!((*obj)->isDark)) {
      // This object wasn't reached, so remove it from the list and free it.
      Obj* unreached = *obj;
      *obj = unreached->next;
      freeObject(unreached);
    } else {
      // This object was reached, so unmark it (for the next GC) and move on to
      // the next.
      (*obj)->isDark = false;
      obj = &(*obj)->next;
    }
  }
}

void freeObjects() {
  // Free all objects.
  Obj* obj = vm.objects;
  while (obj != NULL) {
    Obj* next = obj->next;
    freeObject(obj);
    obj = next;
  }
  
  free(vm.grayStack);
}