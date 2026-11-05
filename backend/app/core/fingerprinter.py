"""
Text Fingerprinter Service
محاسبه SimHash برای تشخیص تکرار نزدیک
"""

import hashlib
import re
from typing import List, Optional


class TextFingerprinter:
    """
    Computes SimHash fingerprints for near-duplicate detection.
    Implementation based on Charikar (2002) with Persian text optimizations.
    """

    # 64-bit fingerprint size
    FINGERPRINT_BITS = 64
    
    # Feature extraction: Persian word n-grams
    SHINGLE_SIZE = 3  # Trigrams for Persian
    
    # Weight for different features
    WORD_WEIGHT = 1
    TRIGRAM_WEIGHT = 2

    def __init__(self, bits: int = 64):
        self.bits = bits
        self.mask = (1 << bits) - 1

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """
        Tokenize Persian text into words.
        Removes punctuation, normalizes whitespace.
        """
        if not text:
            return []
        # Remove punctuation, keep Persian/Arabic/English alphanumerics
        text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip().split()

    @staticmethod
    def _get_trigrams(text: str) -> List[str]:
        """Extract character trigrams for fuzzy matching."""
        if not text or len(text) < 3:
            return []
        trigrams = []
        for i in range(len(text) - 2):
            trigram = text[i:i+3]
            if trigram.strip():  # Skip whitespace-only trigrams
                trigrams.append(trigram)
        return trigrams

    @classmethod
    def compute_simhash(cls, text: str) -> str:
        """
        Compute SimHash fingerprint for text.
        
        Args:
            text: Input text
            
        Returns:
            64-character hexadecimal fingerprint
        """
        if not text:
            return "0" * 16  # 64 bits = 16 hex chars
        
        # Normalize text
        text = re.sub(r'\s+', ' ', text.strip().lower())
        
        # Initialize 64-bit vector
        vector = [0] * 64
        
        # 1. Word features (higher weight)
        words = cls._tokenize(text)
        for word in words:
            if len(word) < 2:
                continue
            hash_val = cls._hash_feature(word)
            weight = cls.WORD_WEIGHT
            for i in range(64):
                bit = (hash_val >> i) & 1
                vector[i] += weight if bit else -weight
        
        # 2. Trigram features (for fuzzy matching)
        trigrams = cls._get_trigrams(text)
        for trigram in trigrams:
            hash_val = cls._hash_feature(trigram)
            weight = cls.TRIGRAM_WEIGHT
            for i in range(64):
                bit = (hash_val >> i) & 1
                vector[i] += weight if bit else -weight
        
        # 3. Build fingerprint
        fingerprint = 0
        for i in range(64):
            if vector[i] > 0:
                fingerprint |= (1 << i)
        
        # Return as 16-char hex string
        return format(fingerprint, '016x')

    @staticmethod
    def _hash_feature(feature: str) -> int:
        """Hash a feature to 64-bit integer using MD5."""
        # Use MD5 for consistent hashing, take first 64 bits
        hash_bytes = hashlib.md5(feature.encode('utf-8')).digest()
        # Convert first 8 bytes to 64-bit int
        return int.from_bytes(hash_bytes[:8], byteorder='little')

    @staticmethod
    def hamming_distance(fp1: str, fp2: str) -> int:
        """Calculate Hamming distance between two fingerprints."""
        if len(fp1) != len(fp2):
            raise ValueError("Fingerprints must have same length")
        
        # Convert hex to int
        try:
            val1 = int(fp1, 16)
            val2 = int(fp2, 16)
        except ValueError:
            return 64  # Max distance for invalid fingerprints
        
        xor = val1 ^ val2
        return bin(xor).count('1')

    @staticmethod
    def similarity(fp1: str, fp2: str) -> float:
        """Calculate similarity percentage (0.0 to 1.0)."""
        distance = TextFingerprinter.hamming_distance(fp1, fp2)
        return 1.0 - (distance / 64.0)

    @classmethod
    def is_similar(cls, fp1: str, fp2: str, threshold: float = 0.95) -> bool:
        """Check if two fingerprints are similar above threshold."""
        return cls.similarity(fp1, fp2) >= threshold

    @classmethod
    def find_similar(cls, target_fp: str, candidates: dict, threshold: float = 0.95) -> List[tuple]:
        """
        Find similar fingerprints from candidates.
        
        Args:
            target_fp: Target fingerprint
            candidates: Dict of {id: fingerprint}
            threshold: Minimum similarity (0.95 = 95%)
            
        Returns:
            List of (id, similarity) tuples sorted by similarity
        """
        results = []
        for cid, fp in candidates.items():
            sim = cls.similarity(target_fp, fp)
            if sim >= threshold:
                results.append((cid, sim))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results