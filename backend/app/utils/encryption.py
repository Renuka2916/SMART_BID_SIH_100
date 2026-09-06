import os
import base64
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from app.core.config import settings

# Derive a 256-bit key from settings.SECRET_KEY using PBKDF2
def _get_aes_key() -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 256 bits
        salt=b"gem_sih_ps100_aes256_audit_salt",
        iterations=100_000,
    )
    return kdf.derive(settings.SECRET_KEY.encode("utf-8"))

_GLOBAL_AES_KEY = _get_aes_key()

def encrypt_field(plaintext: Optional[str]) -> Optional[str]:
    """
    Encrypts a sensitive PII field (e.g. PAN, GSTIN, Udyam) using AES-256-GCM.
    Returns a Base64-encoded string containing [12-byte Nonce + Ciphertext + Tag].
    """
    if not plaintext:
        return None
    
    aesgcm = AESGCM(_GLOBAL_AES_KEY)
    nonce = os.urandom(12)  # 96-bit random nonce for GCM
    ciphertext = aesgcm.encrypt(nonce, plaintext.strip().encode("utf-8"), None)
    payload = nonce + ciphertext
    return base64.b64encode(payload).decode("utf-8")

def decrypt_field(ciphertext_b64: Optional[str]) -> Optional[str]:
    """
    Decrypts an AES-256-GCM encrypted Base64 string.
    Raises ValueError if ciphertext has been tampered with or is invalid.
    """
    if not ciphertext_b64:
        return None
    
    try:
        raw = base64.b64decode(ciphertext_b64.encode("utf-8"))
        if len(raw) < 28:  # 12-byte nonce + minimum 16-byte GCM tag
            raise ValueError("Invalid ciphertext length")
        
        nonce = raw[:12]
        ciphertext = raw[12:]
        aesgcm = AESGCM(_GLOBAL_AES_KEY)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
    except Exception as e:
        raise ValueError(f"AES-256 decryption failed: {e}")

def mask_pan(pan: Optional[str]) -> Optional[str]:
    """Masks PAN: ABCDE1234F -> ABC****34F"""
    if not pan or len(pan.strip()) < 10:
        return pan
    p = pan.strip().upper()
    return f"{p[:3]}****{p[-3:]}"

def mask_gstin(gstin: Optional[str]) -> Optional[str]:
    """Masks GSTIN: 07ABCDE1234F1Z5 -> 07A******1Z5"""
    if not gstin or len(gstin.strip()) < 15:
        return gstin
    g = gstin.strip().upper()
    return f"{g[:3]}******{g[-3:]}"

def mask_udyam(udyam: Optional[str]) -> Optional[str]:
    """Masks Udyam: UDYAM-DL-01-0029145 -> UDYAM-**-**-***9145"""
    if not udyam:
        return None
    u = udyam.strip().upper()
    parts = u.split("-")
    if len(parts) == 4:
        return f"{parts[0]}-**-**-***{parts[3][-4:]}"
    return f"{u[:6]}****{u[-4:]}"
