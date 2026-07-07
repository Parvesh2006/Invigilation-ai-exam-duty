if (typeof globalThis.CustomEvent === 'undefined') {
  class CustomEvent extends Event {
    constructor(event, params = {}) {
      super(event, params);
      this.detail = params.detail || null;
    }
  }
  globalThis.CustomEvent = CustomEvent;
}
