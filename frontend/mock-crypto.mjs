import * as originalCrypto from 'node:crypto';

export const checkPrime = originalCrypto.checkPrime;
export const checkPrimeSync = originalCrypto.checkPrimeSync;
export const createCipheriv = originalCrypto.createCipheriv;
export const createDecipheriv = originalCrypto.createDecipheriv;
export const createDiffieHellman = originalCrypto.createDiffieHellman;
export const createDiffieHellmanGroup = originalCrypto.createDiffieHellmanGroup;
export const createECDH = originalCrypto.createECDH;
export const createHash = originalCrypto.createHash;
export const createHmac = originalCrypto.createHmac;
export const createPrivateKey = originalCrypto.createPrivateKey;
export const createPublicKey = originalCrypto.createPublicKey;
export const createSecretKey = originalCrypto.createSecretKey;
export const createSign = originalCrypto.createSign;
export const createVerify = originalCrypto.createVerify;
export const diffieHellman = originalCrypto.diffieHellman;
export const generatePrime = originalCrypto.generatePrime;
export const generatePrimeSync = originalCrypto.generatePrimeSync;
export const getCiphers = originalCrypto.getCiphers;
export const getCipherInfo = originalCrypto.getCipherInfo;
export const getCurves = originalCrypto.getCurves;
export const getDiffieHellman = originalCrypto.getDiffieHellman;
export const getHashes = originalCrypto.getHashes;
export const hkdf = originalCrypto.hkdf;
export const hkdfSync = originalCrypto.hkdfSync;
export const pbkdf2 = originalCrypto.pbkdf2;
export const pbkdf2Sync = originalCrypto.pbkdf2Sync;
export const generateKeyPair = originalCrypto.generateKeyPair;
export const generateKeyPairSync = originalCrypto.generateKeyPairSync;
export const generateKey = originalCrypto.generateKey;
export const generateKeySync = originalCrypto.generateKeySync;
export const privateDecrypt = originalCrypto.privateDecrypt;
export const privateEncrypt = originalCrypto.privateEncrypt;
export const publicDecrypt = originalCrypto.publicDecrypt;
export const publicEncrypt = originalCrypto.publicEncrypt;
export const randomBytes = originalCrypto.randomBytes;
export const randomFill = originalCrypto.randomFill;
export const randomFillSync = originalCrypto.randomFillSync;
export const randomInt = originalCrypto.randomInt;
export const randomUUID = originalCrypto.randomUUID;
export const scrypt = originalCrypto.scrypt;
export const scryptSync = originalCrypto.scryptSync;
export const sign = originalCrypto.sign;
export const setEngine = originalCrypto.setEngine;
export const timingSafeEqual = originalCrypto.timingSafeEqual;
export const getFips = originalCrypto.getFips;
export const setFips = originalCrypto.setFips;
export const verify = originalCrypto.verify;
export const Certificate = originalCrypto.Certificate;
export const Cipher = originalCrypto.Cipher;
export const Cipheriv = originalCrypto.Cipheriv;
export const Decipher = originalCrypto.Decipher;
export const Decipheriv = originalCrypto.Decipheriv;
export const DiffieHellman = originalCrypto.DiffieHellman;
export const DiffieHellmanGroup = originalCrypto.DiffieHellmanGroup;
export const ECDH = originalCrypto.ECDH;
export const Hash = originalCrypto.Hash;
export const Hmac = originalCrypto.Hmac;
export const KeyObject = originalCrypto.KeyObject;
export const Sign = originalCrypto.Sign;
export const Verify = originalCrypto.Verify;
export const X509Certificate = originalCrypto.X509Certificate;
export const secureHeapUsed = originalCrypto.secureHeapUsed;
export const constants = originalCrypto.constants;
export const webcrypto = originalCrypto.webcrypto;
export const subtle = originalCrypto.subtle;
export const getRandomValues = originalCrypto.getRandomValues;

// Polyfill hash
export function hash(algorithm, data, outputEncoding = 'hex') {
  const hashObj = originalCrypto.createHash(algorithm);
  hashObj.update(data);
  return hashObj.digest(outputEncoding);
}

// Export default
const defaultExport = {
  ...originalCrypto,
  hash
};
export default defaultExport;
