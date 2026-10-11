let assert = Object.assign(
  function assert(expr, message = "") {
    if (expr == false)
      throw new Error(`Expected ${message || "expr"} to be true, but was ${expr}`);
  }, {
  equals(a, b) {
    if (a === b || (a === a && b === b) || (a !== a && b !== b))
      return;

    throw new Error(`Expected ${a} to be ${b}`);
  }
});

class Base {
  constructor() {
    this.x = 1;
  }
}

class PrivateFieldAfterPreventExtensions extends Base {
  #i = 42;

  constructor() {
    super();
    Object.freeze(this);
    assert(Object.isFrozen(this), "Object.isFrozen(this)");
  }

  get() { return this.#i; }
  set(i) { this.#i = i; }
}

function test(i) {
  let c = new PrivateFieldAfterPreventExtensions;
  c.x = 0.1;
  assert.equals(c.get(), 42);
  c.set(i);
  assert.equals(c.get(), i);
}
noInline(test);

test(0);
test(1);
test(2);
for (var i = 0; i < 200; ++i)
  test(i);

// https://github.com/tc39/proposal-nonextensible-applies-to-private
class AddsPrivateFieldToNonExtensibleObject extends Base {
  #i = (Object.freeze(this), 42);
}

class AddsPrivateMethodToNonExtensibleObject extends (class extends Base { constructor() { super(); Object.freeze(this); } }) {
  #m() { }
}

function testThrows(constructor) {
  let error;
  try {
    new constructor;
  } catch (e) {
    error = e;
  }
  assert(error instanceof TypeError, "error instanceof TypeError");
}
noInline(testThrows);

for (var i = 0; i < 200; ++i) {
  testThrows(AddsPrivateFieldToNonExtensibleObject);
  testThrows(AddsPrivateMethodToNonExtensibleObject);
}
