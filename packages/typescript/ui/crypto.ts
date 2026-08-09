/* Client-side encryption helpers (WebCrypto AES-GCM).
 *
 * Used to seal the reporter's private journal and their local case copy so
 * plaintext never leaves the browser. Production server-side storage must use
 * KMS/HSM envelope encryption for investigator access; this module implements
 * the browser half of that guarantee for reporter-held data.
 */

const encoder = new TextEncoder();
const decoder = new TextDecoder();

function toBase64(bytes: Uint8Array): string {
  let binary = '';
  for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
  return btoa(binary);
}

function fromBase64(value: string): Uint8Array<ArrayBuffer> {
  const binary = atob(value);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

export function generateRandomKey(): Promise<CryptoKey> {
  return crypto.subtle.generateKey({ name: 'AES-GCM', length: 256 }, true, ['encrypt', 'decrypt']);
}

export async function encryptString(key: CryptoKey, plaintext: string): Promise<string> {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ciphertext = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    key,
    encoder.encode(plaintext),
  );
  return `${toBase64(iv)}.${toBase64(new Uint8Array(ciphertext))}`;
}

export async function decryptString(key: CryptoKey, sealed: string): Promise<string> {
  const [ivB64, dataB64] = sealed.split('.');
  if (!ivB64 || !dataB64) throw new Error('Malformed sealed payload');
  const plaintext = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: fromBase64(ivB64) },
    key,
    fromBase64(dataB64),
  );
  return decoder.decode(plaintext);
}

export async function exportKeyBase64(key: CryptoKey): Promise<string> {
  const raw = await crypto.subtle.exportKey('raw', key);
  return toBase64(new Uint8Array(raw));
}

export async function importKeyBase64(value: string): Promise<CryptoKey> {
  return crypto.subtle.importKey('raw', fromBase64(value), { name: 'AES-GCM' }, true, [
    'encrypt',
    'decrypt',
  ]);
}

export async function sha256Hex(text: string): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', encoder.encode(text));
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

/* Small local "vault" keyed to a logical name. In production this key should
 * live in platform key storage or behind the OS credential store. */
const VAULT_PREFIX = 'wpc:vault:key:';

export async function loadOrCreateVaultKey(name: string): Promise<CryptoKey> {
  const stored = localStorage.getItem(`${VAULT_PREFIX}${name}`);
  if (stored) {
    try {
      return await importKeyBase64(stored);
    } catch {
      localStorage.removeItem(`${VAULT_PREFIX}${name}`);
    }
  }
  const key = await generateRandomKey();
  localStorage.setItem(`${VAULT_PREFIX}${name}`, await exportKeyBase64(key));
  return key;
}

export async function clearVaultKey(name: string): Promise<void> {
  localStorage.removeItem(`${VAULT_PREFIX}${name}`);
}
