import jwt
import base64
import json

# # Your tokens
# original = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjp7ImVtYWlsIjoidGVzdEBnbWFpbC5jb20iLCJ1c2VyX2lkIjo2fSwiZXhwIjoxNzQ4NjA1NTg2LCJqdGkiOiI2MDU0ZWIwZi00ZGQwLTQ4ZmYtOGNlZC01ZWI1OTZmZWMzOGMiLCJyZWZyZXNoIjpmYWxzZX0.A_vScVzzXDGiPOJIQ2zMQm-r4uv2Zvowy_ZV_AV67Pc"
# modified = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjp7ImVtYWlsIjoidGVzdEBnbWFpbC5jb20iLCJ1c2VyX2lkIjo2fSwiZXhwIjoxNzQ4NjA1NTg2LCJqdGkiOiI2MDU0ZWIwZi00ZGQwLTQ4ZmYtOGNlZC01ZWI1OTZmZWMzOGMiLCJyZWZyZXNoIjpmYWxzZX0.A_vScVzzXDGiPOJIQ2zMQm-r4uv2Zvowy_ZV_AV67Pe"

# SECRET_KEY = "e-Kvkme6tHg9mbbdIXm8KEYoei1-SFhqX7MszOM3GQk"

# print("=" * 60)
# print("JWT SECURITY VULNERABILITY ANALYSIS")
# print("=" * 60)

# # 1. Verify tokens are different
# print("\n1. TOKEN COMPARISON:")
# print(f"Original ends with: ...{original[-20:]}")
# print(f"Modified ends with: ...{modified[-20:]}")
# print(f"Are tokens different? {original != modified}")

# # 2. Extract and compare signatures
# def extract_signature(token):
#     parts = token.split('.')
#     return parts[2] if len(parts) == 3 else None

# orig_sig = extract_signature(original)
# mod_sig = extract_signature(modified)

# print(f"\nOriginal signature: {orig_sig}")
# print(f"Modified signature: {mod_sig}")
# print(f"Signatures different? {orig_sig != mod_sig}")

# # 3. Test JWT validation with PyJWT
# print("\n2. PYJWT LIBRARY TEST:")
# print("Testing with PyJWT library...")

# try:
#     payload1 = jwt.decode(original, SECRET_KEY, algorithms=["HS256"])
#     print("✅ Original token: VALID")
# except Exception as e:
#     print(f"❌ Original token: INVALID - {e}")

# try:
#     payload2 = jwt.decode(modified, SECRET_KEY, algorithms=["HS256"])
#     print("🚨 Modified token: VALID (THIS IS THE BUG!)")
# except Exception as e:
#     print(f"✅ Modified token: INVALID - {e}")

# # 4. Test with manual HMAC verification
# print("\n3. MANUAL HMAC VERIFICATION:")
# import hmac
# import hashlib

# def verify_jwt_manually(token, secret):
#     try:
#         parts = token.split('.')
#         if len(parts) != 3:
#             return False, "Invalid JWT format"
        
#         header_payload = f"{parts[0]}.{parts[1]}"
#         signature = parts[2]
        
#         # Calculate expected signature
#         expected_signature = base64.urlsafe_b64encode(
#             hmac.new(
#                 secret.encode(),
#                 header_payload.encode(),
#                 hashlib.sha256
#             ).digest()
#         ).decode().rstrip('=')
        
#         # Compare signatures
#         is_valid = hmac.compare_digest(signature, expected_signature)
#         return is_valid, f"Expected: {expected_signature}, Got: {signature}"
#     except Exception as e:
#         return False, str(e)

# orig_valid, orig_msg = verify_jwt_manually(original, SECRET_KEY)
# mod_valid, mod_msg = verify_jwt_manually(modified, SECRET_KEY)

# print(f"Original token manual verification: {'✅ VALID' if orig_valid else '❌ INVALID'}")
# print(f"  {orig_msg}")
# print(f"Modified token manual verification: {'❌ INVALID' if not mod_valid else '🚨 VALID (BUG!)'}")
# print(f"  {mod_msg}")

# # 5. Check PyJWT version
# print(f"\n4. ENVIRONMENT INFO:")
# print(f"PyJWT version: {jwt.__version__}")

# # 6. Test with different options
# print(f"\n5. TESTING DIFFERENT JWT OPTIONS:")

# # Test with verify_signature=False (should always work)
# try:
#     payload = jwt.decode(modified, options={"verify_signature": False})
#     print("⚠️  With verify_signature=False: VALID (expected)")
# except Exception as e:
#     print(f"❌ With verify_signature=False: {e}")

# # Test with explicit verification
# try:
#     payload = jwt.decode(modified, SECRET_KEY, algorithms=["HS256"], options={"verify_signature": True})
#     print("🚨 With explicit verify_signature=True: VALID (THIS IS THE BUG!)")
# except Exception as e:
#     print(f"✅ With explicit verify_signature=True: INVALID - {e}")

# print("\n" + "=" * 60)
# print("DIAGNOSIS:")
# if orig_valid and not mod_valid:
#     print("✅ JWT validation is working correctly")
# elif orig_valid and mod_valid:
#     print("🚨 CRITICAL: Both tokens validate - JWT security is completely broken!")
#     print("   Possible causes:")
#     print("   - PyJWT library bug or wrong version")
#     print("   - Signature verification is disabled somewhere")
#     print("   - Secret key mismatch during encoding/decoding")
# else:
#     print("❓ Unexpected result - needs investigation")
# print("=" * 60)




"""
Deep test for pyjwt library
"""
# import jwt
# import sys
# import inspect

# # Your tokens
# original = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjp7ImVtYWlsIjoidGVzdEBnbWFpbC5jb20iLCJ1c2VyX2lkIjo2fSwiZXhwIjoxNzQ4NjA1NTg2LCJqdGkiOiI2MDU0ZWIwZi00ZGQwLTQ4ZmYtOGNlZC01ZWI1OTZmZWMzOGMiLCJyZWZyZXNoIjpmYWxzZX0.A_vScVzzXDGiPOJIQ2zMQm-r4uv2Zvowy_ZV_AV67Pc"
# modified = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjp7ImVtYWlsIjoidGVzdEBnbWFpbC5jb20iLCJ1c2VyX2lkIjo2fSwiZXhwIjoxNzQ4NjA1NTg2LCJqdGkiOiI2MDU0ZWIwZi00ZGQwLTQ4ZmYtOGNlZC01ZWI1OTZmZWMzOGMiLCJyZWZyZXNoIjpmYWxzZX0.A_vScVzzXDGiPOJIQ2zMQm-r4uv2Zvowy_ZV_AV67Pe"

# SECRET_KEY = "e-Kvkme6tHg9mbbdIXm8KEYoei1-SFhqX7MszOM3GQk"

# print("=" * 70)
# print("DEEP PYJWT DEBUGGING")
# print("=" * 70)

# print(f"Python version: {sys.version}")
# print(f"PyJWT version: {jwt.__version__}")
# print(f"PyJWT location: {jwt.__file__}")

# # Check what decode function we're actually calling
# print(f"\nPyJWT decode function: {jwt.decode}")
# print(f"PyJWT decode signature: {inspect.signature(jwt.decode)}")

# # Test step by step with maximum verbosity
# print("\n" + "="*50)
# print("STEP-BY-STEP PYJWT ANALYSIS")
# print("="*50)

# # Test 1: Decode with all default options
# print("\n1. Default decode (should verify signature):")
# try:
#     result1 = jwt.decode(original, SECRET_KEY, algorithms=["HS256"])
#     print("✅ Original with defaults: VALID")
# except Exception as e:
#     print(f"❌ Original with defaults: {type(e).__name__}: {e}")

# try:
#     result2 = jwt.decode(modified, SECRET_KEY, algorithms=["HS256"])
#     print("🚨 Modified with defaults: VALID (THIS IS THE BUG!)")
#     print(f"   Returned payload: {result2}")
# except Exception as e:
#     print(f"✅ Modified with defaults: {type(e).__name__}: {e}")

# # Test 2: Explicitly enable signature verification
# print("\n2. Explicit signature verification enabled:")
# try:
#     result3 = jwt.decode(
#         original, 
#         SECRET_KEY, 
#         algorithms=["HS256"],
#         options={"verify_signature": True}
#     )
#     print("✅ Original with verify_signature=True: VALID")
# except Exception as e:
#     print(f"❌ Original with verify_signature=True: {type(e).__name__}: {e}")

# try:
#     result4 = jwt.decode(
#         modified, 
#         SECRET_KEY, 
#         algorithms=["HS256"],
#         options={"verify_signature": True}
#     )
#     print("🚨 Modified with verify_signature=True: VALID (CRITICAL BUG!)")
# except Exception as e:
#     print(f"✅ Modified with verify_signature=True: {type(e).__name__}: {e}")

# # Test 3: Check what options are actually being used
# print("\n3. Inspect PyJWT internal behavior:")

# # Try to access internal functions
# try:
#     from jwt.api_jwt import PyJWT
#     jwt_instance = PyJWT()
    
#     # Check default options
#     print(f"Default options: {getattr(jwt_instance, 'options', 'Not found')}")
    
#     # Try to see what's happening internally
#     print("Attempting to trace PyJWT internal calls...")
    
#     # Monkey patch to see what's happening
#     original_decode = jwt_instance.decode
    
#     def debug_decode(*args, **kwargs):
#         print(f"PyJWT.decode called with args: {args}")
#         print(f"PyJWT.decode called with kwargs: {kwargs}")
#         result = original_decode(*args, **kwargs)
#         print(f"PyJWT.decode returning: {type(result)}")
#         return result
    
#     jwt_instance.decode = debug_decode
#     jwt.decode = jwt_instance.decode
    
#     print("\n--- Tracing original token decode ---")
#     jwt.decode(original, SECRET_KEY, algorithms=["HS256"])
    
#     print("\n--- Tracing modified token decode ---")
#     jwt.decode(modified, SECRET_KEY, algorithms=["HS256"])
    
# except Exception as e:
#     print(f"Internal inspection failed: {e}")

# # Test 4: Try different PyJWT calling patterns
# print("\n4. Different calling patterns:")

# patterns = [
#     {"key": SECRET_KEY, "algorithms": ["HS256"]},
#     {"key": SECRET_KEY, "algorithms": ["HS256"], "options": {}},
#     {"key": SECRET_KEY, "algorithms": ["HS256"], "options": {"verify_signature": True}},
#     {"key": SECRET_KEY, "algorithms": ["HS256"], "verify": True},
# ]

# for i, pattern in enumerate(patterns, 1):
#     print(f"\nPattern {i}: {pattern}")
#     try:
#         jwt.decode(modified, **pattern)
#         print(f"🚨 Modified token accepted with pattern {i}")
#     except Exception as e:
#         print(f"✅ Modified token rejected with pattern {i}: {type(e).__name__}")

# # Test 5: Check if there are multiple jwt libraries installed
# print("\n5. Library conflict check:")
# try:
#     import importlib
#     import pkgutil
    
#     jwt_packages = []
#     for finder, name, ispkg in pkgutil.iter_modules():
#         if 'jwt' in name.lower():
#             jwt_packages.append(name)
    
#     print(f"JWT-related packages found: {jwt_packages}")
    
#     # Check if there's another jwt module
#     try:
#         import jwt as jwt1
#         try:
#             # import PyJWT as jwt2
#             print("Both 'jwt' and 'PyJWT' modules available")
#             print(f"jwt module: {jwt1}")
#             # print(f"PyJWT module: {jwt2}")
#         except ImportError:
#             print("Only 'jwt' module found")
#     except ImportError:
#         print("No jwt module found (weird)")
        
# except Exception as e:
#     print(f"Library check failed: {e}")

# print("\n" + "="*70)
# print("SUMMARY:")
# print("If the modified token is being accepted by PyJWT, this indicates:")
# print("1. A critical bug in your PyJWT version 2.10.1")
# print("2. A corrupted installation")
# print("3. Some kind of monkey-patching or override happening")
# print("4. Multiple JWT libraries conflicting")
# print("="*70)

"""
Lucky Coincidence" Theory:
JWT signatures use Base64URL encoding, where certain character changes might not affect the underlying binary data due to:

Base64 padding/encoding quirks
Similar-looking characters that decode to the same bytes
Edge cases in the specific signature
"""

import jwt
import base64
import string

# Your tokens
original = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjp7ImVtYWlsIjoidGVzdEBnbWFpbC5jb20iLCJ1c2VyX2lkIjo2fSwiZXhwIjoxNzQ4NjA1NTg2LCJqdGkiOiI2MDU0ZWIwZi00ZGQwLTQ4ZmYtOGNlZC01ZWI1OTZmZWMzOGMiLCJyZWZyZXNoIjpmYWxzZX0.A_vScVzzXDGiPOJIQ2zMQm-r4uv2Zvowy_ZV_AV67Pc"
SECRET_KEY = "e-Kvkme6tHg9mbbdIXm8KEYoei1-SFhqX7MszOM3GQk"

print("="*60)
print("JWT COINCIDENCE ANALYSIS")
print("="*60)

# Extract signature part
signature = original.split('.')[-1]
print(f"Original signature: {signature}")
print(f"Length: {len(signature)}")

# Test what happens when we decode the signature to bytes
try:
    orig_bytes = base64.urlsafe_b64decode(signature + '==')
    print(f"Original signature as bytes: {orig_bytes.hex()}")
except Exception as e:
    print(f"Error decoding original: {e}")

# Test the specific change you made (c -> e)
modified_signature = signature[:-1] + 'e'
print(f"\nModified signature: {modified_signature}")

try:
    mod_bytes = base64.urlsafe_b64decode(modified_signature + '==')
    print(f"Modified signature as bytes: {mod_bytes.hex()}")
    print(f"Bytes are identical: {orig_bytes == mod_bytes}")
except Exception as e:
    print(f"Error decoding modified: {e}")

# Comprehensive test: try changing EVERY character in the signature
print(f"\n{'='*60}")
print("SYSTEMATIC SIGNATURE TAMPERING TEST")
print("="*60)

base_token = original[:-1]  # Token without last character
valid_changes = []
total_tests = 0

# Test all possible characters for the last position
test_chars = string.ascii_letters + string.digits + '-_='
print(f"Testing {len(test_chars)} different characters for last position...")

for char in test_chars:
    test_token = base_token + char
    total_tests += 1
    
    try:
        payload = jwt.decode(test_token, SECRET_KEY, algorithms=["HS256"])
        valid_changes.append(char)
        if char != 'c':  # Original was 'c'
            print(f"🚨 FOUND ANOTHER VALID CHARACTER: '{char}'")
    except:
        pass  # Expected - invalid signature

print(f"\nRESULTS:")
print(f"Total characters tested: {total_tests}")
print(f"Valid characters found: {len(valid_changes)}")
print(f"Valid characters: {valid_changes}")

if len(valid_changes) > 1:
    print(f"\n🎯 COINCIDENCE CONFIRMED!")
    print(f"Your signature happens to be valid with {len(valid_changes)} different characters")
    print(f"This is due to Base64URL encoding quirks, not a security vulnerability")
else:
    print(f"\n❓ Only original character works - this might not be coincidence")

# Let's also test a few other positions
print(f"\n{'='*40}")
print("TESTING OTHER POSITIONS")
print("="*40)

# Test changing character at different positions
test_positions = [-2, -3, -4, -5]  # Test last few characters
for pos in test_positions:
    if abs(pos) <= len(signature):
        print(f"\nTesting position {pos} (character '{signature[pos]}'):")
        base = signature[:pos] + 'X' + signature[pos+1:]
        test_token = original.split('.')[0] + '.' + original.split('.')[1] + '.' + base
        
        try:
            jwt.decode(test_token, SECRET_KEY, algorithms=["HS256"])
            print(f"✅ Position {pos}: Changing '{signature[pos]}' to 'X' still works!")
        except:
            print(f"❌ Position {pos}: Changing '{signature[pos]}' to 'X' breaks signature (expected)")

# Test with your new token to confirm it works properly
print(f"\n{'='*60}")
print("TESTING YOUR NEW TOKEN")
print("="*60)
print("Please paste your new access token here and we'll test if signature validation")
print("works properly with character modifications...")

# Base64URL decode explanation
print(f"\n{'='*60}")
print("BASE64URL ENCODING EXPLANATION")
print("="*60)
print("Base64URL uses: A-Z, a-z, 0-9, -, _")
print("Some character changes might not affect the decoded bytes due to:")
print("1. Base64 padding rules")
print("2. Character encoding boundaries") 
print("3. Specific bit patterns in your signature")
print("\nThis is why 'c' and 'e' might decode to the same binary value!")

# Let's verify this theory
print(f"\nBASE64URL DECODING TEST:")
try:
    # Add padding and decode both
    orig_padded = signature + '=='
    mod_padded = modified_signature + '=='
    
    orig_decoded = base64.urlsafe_b64decode(orig_padded)
    mod_decoded = base64.urlsafe_b64decode(mod_padded)
    
    print(f"Original decoded: {orig_decoded.hex()}")
    print(f"Modified decoded: {mod_decoded.hex()}")
    print(f"Identical after decoding: {orig_decoded == mod_decoded}")
    
    if orig_decoded == mod_decoded:
        print("🎯 CONFIRMED: 'c' and 'e' decode to identical bytes!")
        print("This explains why both tokens are valid - it's not a security bug!")
    
except Exception as e:
    print(f"Decoding test failed: {e}")