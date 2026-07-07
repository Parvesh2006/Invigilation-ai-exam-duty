import * as originalUtil from 'node:util';

export const _errnoException = originalUtil._errnoException;
export const _exceptionWithHostPort = originalUtil._exceptionWithHostPort;
export const _extend = originalUtil._extend;
export const callbackify = originalUtil.callbackify;
export const debug = originalUtil.debug;
export const debuglog = originalUtil.debuglog;
export const deprecate = originalUtil.deprecate;
export const format = originalUtil.format;
export const formatWithOptions = originalUtil.formatWithOptions;
export const getSystemErrorMap = originalUtil.getSystemErrorMap;
export const getSystemErrorName = originalUtil.getSystemErrorName;
export const inherits = originalUtil.inherits;
export const inspect = originalUtil.inspect;
export const isArray = originalUtil.isArray;
export const isBoolean = originalUtil.isBoolean;
export const isBuffer = originalUtil.isBuffer;
export const isDeepStrictEqual = originalUtil.isDeepStrictEqual;
export const isNull = originalUtil.isNull;
export const isNullOrUndefined = originalUtil.isNullOrUndefined;
export const isNumber = originalUtil.isNumber;
export const isString = originalUtil.isString;
export const isSymbol = originalUtil.isSymbol;
export const isUndefined = originalUtil.isUndefined;
export const isRegExp = originalUtil.isRegExp;
export const isObject = originalUtil.isObject;
export const isDate = originalUtil.isDate;
export const isError = originalUtil.isError;
export const isFunction = originalUtil.isFunction;
export const isPrimitive = originalUtil.isPrimitive;
export const log = originalUtil.log;
export const promisify = originalUtil.promisify;
export const stripVTControlCharacters = originalUtil.stripVTControlCharacters;
export const toUSVString = originalUtil.toUSVString;
export const transferableAbortSignal = originalUtil.transferableAbortSignal;
export const transferableAbortController = originalUtil.transferableAbortController;
export const aborted = originalUtil.aborted;
export const types = originalUtil.types;
export const parseArgs = originalUtil.parseArgs;
export const TextDecoder = originalUtil.TextDecoder;
export const TextEncoder = originalUtil.TextEncoder;
export const MIMEType = originalUtil.MIMEType;
export const MIMEParams = originalUtil.MIMEParams;

// Polyfill styleText
export function styleText(format, text) {
  const codes = {
    bold: [1, 22],
    italic: [3, 23],
    underline: [4, 24],
    red: [31, 39],
    green: [32, 39],
    yellow: [33, 39],
    blue: [34, 39],
    magenta: [35, 39],
    cyan: [36, 39],
    white: [37, 39],
    gray: [90, 39],
  };
  const [on, off] = codes[format] || [0, 0];
  if (on === 0) return text;
  return `\u001b[${on}m${text}\u001b[${off}m`;
}

// Polyfill parseEnv
export function parseEnv(content) {
  const result = {};
  if (typeof content !== 'string') return result;
  
  const lines = content.split(/\r?\n/);
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    
    const firstEquals = trimmed.indexOf('=');
    if (firstEquals === -1) continue;
    
    const key = trimmed.slice(0, firstEquals).trim();
    let val = trimmed.slice(firstEquals + 1).trim();
    
    if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
      val = val.slice(1, -1);
    }
    
    result[key] = val;
  }
  return result;
}

// Export default
const defaultExport = {
  ...originalUtil,
  styleText,
  parseEnv
};
export default defaultExport;
