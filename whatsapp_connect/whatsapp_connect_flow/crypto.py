# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Encryption of the Flow data endpoint, as Meta specifies it.

Meta encrypts each request with a new AES-128 key (AES-GCM) and encrypts that
key with the business public key (RSA-OAEP, SHA-256). The answer is encrypted
with the same AES key and the request's IV with every bit flipped.
"""

import base64
import json

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEY_SIZE = 2048


class FlowDecryptionError(Exception):
	"""The request could not be decrypted; Meta expects HTTP 421 so it refreshes the key."""


def generate_key_pair() -> tuple[str, str]:
	"""
	Create a new RSA key pair for the Flow endpoint.

	Returns:
	        tuple[str, str]: (private key PEM, public key PEM).
	"""
	private_key = rsa.generate_private_key(public_exponent=65537, key_size=KEY_SIZE)
	private_pem = private_key.private_bytes(
		serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
	)
	public_pem = private_key.public_key().public_bytes(
		serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
	)
	return private_pem.decode(), public_pem.decode()


def decrypt_request(body: dict, private_key_pem: str) -> tuple[dict, bytes, bytes]:
	"""
	Decrypt a Flow endpoint request.

	Parameters:
	        body (dict, required): encrypted_flow_data, encrypted_aes_key and initial_vector (base64).
	        private_key_pem (str, required): The business private key.

	Returns:
	        tuple[dict, bytes, bytes]: (decrypted request, AES key, IV), the last two for the answer.
	"""
	try:
		private_key = serialization.load_pem_private_key(private_key_pem.encode(), password=None)
		aes_key = private_key.decrypt(
			base64.b64decode(body["encrypted_aes_key"]),
			padding.OAEP(
				mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None
			),
		)
		iv = base64.b64decode(body["initial_vector"])
		data = AESGCM(aes_key).decrypt(iv, base64.b64decode(body["encrypted_flow_data"]), None)
		return json.loads(data), aes_key, iv
	except Exception as error:
		raise FlowDecryptionError(str(error)) from error


def encrypt_response(answer: dict, aes_key: bytes, iv: bytes) -> str:
	"""
	Encrypt the answer to a Flow endpoint request.

	Parameters:
	        answer (dict, required): The answer object.
	        aes_key (bytes, required): The AES key of the request.
	        iv (bytes, required): The IV of the request.

	Returns:
	        str: Base64 of the ciphertext with its GCM tag, sent as plain text.
	"""
	flipped_iv = bytes(byte ^ 0xFF for byte in iv)
	encrypted = AESGCM(aes_key).encrypt(flipped_iv, json.dumps(answer).encode(), None)
	return base64.b64encode(encrypted).decode()
