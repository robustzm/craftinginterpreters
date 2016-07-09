//>= Statements and State
package com.craftinginterpreters.vox;

import java.util.HashMap;
import java.util.Map;

class Environment {
//>= Functions
  private final Environment enclosing;
//>= Statements and State
  private final Map<String, Object> values = new HashMap<>();

//>= Functions
  Environment() {
    enclosing = null;
  }

  Environment(Environment enclosing) {
    this.enclosing = enclosing;
  }

//>= Statements and State
  Object get(Token name) {
    if (values.containsKey(name.text)) {
      return values.get(name.text);
    }

/*== Functions
    if (enclosing != null) return enclosing.get(name, token);

*/
//>= Statements and State
    throw new RuntimeError(name,
        "Undefined variable '" + name.text + "'.");
  }

//>= Resolving Names
  Object getAt(int distance, String name) {
    Environment environment = this;
    for (int i = 0; i < distance; i++) {
      environment = environment.enclosing;
    }

    return environment.values.get(name);
  }

//>= Statements and State
  void set(Token name, Object value) {
    if (values.containsKey(name.text)) {
      values.put(name.text, value);
      return;
    }

/*== Functions
    if (enclosing != null) {
      enclosing.set(name, value);
      return;
    }

*/
//>= Statements and State
    throw new RuntimeError(name,
        "Undefined variable '" + name.text + "'.");
  }

//>= Resolving Names
  void setAt(int distance, Token name, Object value) {
    Environment environment = this;
    for (int i = 0; i < distance; i++) {
      environment = environment.enclosing;
    }

    environment.values.put(name.text, value);
  }

//>= Closures
  void declare(Token name) {
    // Note: Can't just use define(name, null). That will
    // overwrite a previously defined global value.
    if (!values.containsKey(name.text)) {
      values.put(name.text, null);
    }
  }

//>= Statements and State
  void define(String name, Object value) {
    values.put(name, value);
  }

//>= Functions
  Environment enterScope() {
    return new Environment(this);
  }

//>= Statements and State
  @Override
  public String toString() {
/*>= Statements and State <= Control Flow
    return values.toString();
*/
//>= Functions
    String result = values.toString();
    if (enclosing != null) {
      result += " -> " + enclosing.toString();
    }

    return result;
//>= Statements and State
  }
}
