package com.craftinginterpreters.vox;

import java.util.List;

class VoxFunction implements Callable {
  private final Stmt.Function declaration;
  private final Local closure;

  VoxFunction(Stmt.Function declaration, Local closure) {
    this.declaration = declaration;
    this.closure = closure;
  }

  VoxFunction bind(VoxObject self) {
    return new VoxFunction(declaration, new Local(closure, "this", self));
  }

  @Override
  public String toString() {
    return declaration.name.text;
  }

  @Override
  public int requiredArguments() {
    return declaration.parameters.size();
  }

  @Override
  public Object call(Interpreter interpreter, List<Object> arguments) {
    try {
      Local locals = closure;
      for (int i = 0; i < declaration.parameters.size(); i++) {
        // TODO: Handle duplicate?
        locals = new Local(locals, declaration.parameters.get(i).text, arguments.get(i));
      }

      interpreter.execute(declaration.body, locals);
      return null;
    } catch (Return returnValue) {
      return returnValue.value;
    }
  }
}
