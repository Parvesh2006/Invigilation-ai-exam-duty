if (typeof globalThis.CustomEvent === 'undefined') {
  class CustomEvent extends Event {
    constructor(event, params = {}) {
      super(event, params);
      this.detail = params.detail || null;
    }
  }
  globalThis.CustomEvent = CustomEvent;
}

export async function resolve(specifier, context, nextResolve) {
  if ((specifier === 'node:util' || specifier === 'util') && !context.parentURL?.endsWith('mock-util.mjs')) {
    return {
      shortCircuit: true,
      url: new URL('./mock-util.mjs', import.meta.url).href
    };
  }
  if ((specifier === 'node:crypto' || specifier === 'crypto') && !context.parentURL?.endsWith('mock-crypto.mjs')) {
    return {
      shortCircuit: true,
      url: new URL('./mock-crypto.mjs', import.meta.url).href
    };
  }
  return nextResolve(specifier, context);
}
