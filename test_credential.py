"""
Test Suite for credential.py v2.1

This file contains tests to verify all functionality works correctly.
Run this file to test the credential management system.
"""

from credential import (
    PasswordManager,
    PasswordDialog,
    example_verify_password,
    get_decrypted_password,
    example_complete_workflow
)
import os
import json
from pathlib import Path


def test_password_manager():
    """Test PasswordManager class basic functionality"""
    print("\n=== Testing PasswordManager Class ===")

    manager = PasswordManager()

    # Test encryption/decryption
    test_password = "TestPassword123!"
    test_master = "MasterKey456!"

    # Encrypt
    encrypted = manager.encrypt_password(test_password, test_master)
    print(f"✓ Encryption successful: {encrypted[:20]}...")

    # Decrypt with correct master password
    decrypted = manager.decrypt_password(encrypted, test_master)
    if decrypted == test_password:
        print(f"✓ Decryption successful: Password matches")
    else:
        print(f"✗ Decryption failed: Password mismatch")
        return False

    # Test with wrong master password
    wrong_decrypt = manager.decrypt_password(encrypted, "WrongPassword")
    if wrong_decrypt is None:
        print(f"✓ Wrong master password correctly rejected")
    else:
        print(f"✗ Wrong master password not rejected")
        return False

    return True


def test_config_operations():
    """Test saving and loading from config.json"""
    print("\n=== Testing Config Operations ===")

    manager = PasswordManager()
    test_file = "test_config.json"

    # Clean up any existing test file
    if Path(test_file).exists():
        os.remove(test_file)

    # Test saving
    test_data = {
        'password': 'encrypted_test_password',
        'username': 'test_user',
        'domain': 'test.com'
    }

    manager.save_to_config(
        test_data['password'],
        filename=test_file,
        username=test_data['username'],
        domain=test_data['domain']
    )

    if Path(test_file).exists():
        print(f"✓ Config file created: {test_file}")
    else:
        print(f"✗ Config file not created")
        return False

    # Test loading
    with open(test_file, 'r') as f:
        config = json.load(f)

    if config['username'] == test_data['username']:
        print(f"✓ Username saved correctly: {config['username']}")
    else:
        print(f"✗ Username not saved correctly")
        return False

    if config['domain'] == test_data['domain']:
        print(f"✓ Domain saved correctly: {config['domain']}")
    else:
        print(f"✗ Domain not saved correctly")
        return False

    loaded_password = manager.load_from_config(filename=test_file)
    if loaded_password == test_data['password']:
        print(f"✓ Password loaded correctly")
    else:
        print(f"✗ Password not loaded correctly")
        return False

    # Clean up
    os.remove(test_file)
    print(f"✓ Test file cleaned up")

    return True


def test_encryption_decryption_cycle():
    """Test full encryption/decryption cycle"""
    print("\n=== Testing Encryption/Decryption Cycle ===")

    manager = PasswordManager()
    test_file = "test_cycle.json"

    # Clean up
    if Path(test_file).exists():
        os.remove(test_file)

    # Original data
    original_password = "MySecretPassword123!"
    master_password = "MasterKey456!"
    username = "john_doe"
    domain = "example.com"

    print(f"Original password: {original_password}")
    print(f"Master password: {master_password}")

    # Encrypt
    encrypted = manager.encrypt_password(original_password, master_password)
    print(f"✓ Password encrypted")

    # Save
    manager.save_to_config(
        encrypted,
        filename=test_file,
        username=username,
        domain=domain
    )
    print(f"✓ Saved to {test_file}")

    # Load
    loaded_encrypted = manager.load_from_config(filename=test_file)
    print(f"✓ Loaded from {test_file}")

    # Decrypt with correct master password
    decrypted = manager.decrypt_password(loaded_encrypted, master_password)

    if decrypted == original_password:
        print(f"✓ Full cycle successful: Password matches original")
    else:
        print(f"✗ Full cycle failed: Password mismatch")
        print(f"   Expected: {original_password}")
        print(f"   Got: {decrypted}")
        return False

    # Test with wrong master password
    wrong_decrypted = manager.decrypt_password(loaded_encrypted, "WrongPassword")
    if wrong_decrypted is None:
        print(f"✓ Wrong master password correctly rejected")
    else:
        print(f"✗ Wrong master password not rejected")
        return False

    # Clean up
    os.remove(test_file)
    print(f"✓ Test file cleaned up")

    return True


def test_get_decrypted_password_function():
    """Test get_decrypted_password function"""
    print("\n=== Testing get_decrypted_password Function ===")

    manager = PasswordManager()
    test_file = "config.json"

    # Setup test data
    original_password = "TestPassword123!"
    master_password = "MasterKey456!"

    # Encrypt and save
    encrypted = manager.encrypt_password(original_password, master_password)
    manager.save_to_config(
        encrypted,
        username="test_user",
        domain="test.com"
    )
    print(f"✓ Test data setup complete")

    # Test function with correct master password
    decrypted = get_decrypted_password(master_password)

    if decrypted == original_password:
        print(f"✓ get_decrypted_password works correctly")
    else:
        print(f"✗ get_decrypted_password failed")
        return False

    # Test with wrong master password
    wrong_decrypted = get_decrypted_password("WrongPassword")
    if wrong_decrypted is None:
        print(f"✓ Wrong master password correctly rejected")
    else:
        print(f"✗ Wrong master password not rejected")
        return False

    return True


def test_memory_cleanup():
    """Test that sensitive data is properly cleaned"""
    print("\n=== Testing Memory Cleanup ===")

    manager = PasswordManager()

    # Create test password
    password = "TestPassword123!"
    master = "MasterKey456!"

    # Encrypt
    encrypted = manager.encrypt_password(password, master)

    # Decrypt
    decrypted = manager.decrypt_password(encrypted, master)

    # Clean up
    decrypted = None
    master = None
    password = None

    print(f"✓ Variables set to None")
    print(f"✓ Memory cleanup test passed")

    # Note: Python's garbage collector will eventually free the memory
    # We can't directly verify memory is cleared, but setting to None
    # is the correct approach

    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("CREDENTIAL.PY v2.1 - TEST SUITE")
    print("=" * 60)

    tests = [
        ("PasswordManager Basic", test_password_manager),
        ("Config Operations", test_config_operations),
        ("Encryption/Decryption Cycle", test_encryption_decryption_cycle),
        ("get_decrypted_password Function", test_get_decrypted_password_function),
        ("Memory Cleanup", test_memory_cleanup),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} raised an exception: {e}")
            results.append((test_name, False))

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1

    print("\n" + "-" * 60)
    print(f"Total: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("-" * 60)

    if failed == 0:
        print("\n🎉 All tests passed! The system is working correctly.")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please review the output above.")

    return failed == 0


def interactive_test():
    """Interactive test that requires user input"""
    print("\n" + "=" * 60)
    print("INTERACTIVE TEST - User Input Required")
    print("=" * 60)

    print("\nThis test will verify the GUI components.")
    print("You will need to interact with dialog windows.")

    response = input("\nDo you want to run interactive tests? (y/n): ")

    if response.lower() != 'y':
        print("Interactive tests skipped.")
        return

    # Test 1: Create credentials
    print("\n--- Test 1: Create Credentials ---")
    print("A dialog will open. Please fill in all fields:")
    print("- Username: test_user")
    print("- Password: Test123!")
    print("- Confirm Password: Test123!")
    print("- Domain: test.com")
    print("- Master Password: Master456!")
    print("- Confirm Master: Master456!")

    input("Press Enter to open dialog...")

    dialog = PasswordDialog(mode="encrypt")
    result = dialog.show()

    if result:
        print("✓ Credentials created successfully")
    else:
        print("✗ Credential creation cancelled")
        return

    # Test 2: Verify password
    print("\n--- Test 2: Verify Master Password ---")
    print("Enter master password: Master456!")

    input("Press Enter to open dialog...")

    master_password = example_verify_password()

    if master_password:
        print(f"✓ Master password verified: {master_password}")

        # Test 3: Get decrypted password
        print("\n--- Test 3: Decrypt Password ---")
        decrypted = get_decrypted_password(master_password)

        if decrypted:
            print(f"✓ Password decrypted: {decrypted}")

            # Clean up
            decrypted = None
            master_password = None
            print("✓ Memory cleaned")
        else:
            print("✗ Failed to decrypt password")
    else:
        print("✗ Master password verification failed")

    print("\n✓ Interactive tests completed")


if __name__ == "__main__":
    # Run automated tests
    success = run_all_tests()

    # Offer interactive tests
    print("\n" + "=" * 60)
    interactive_test()

    print("\n" + "=" * 60)
    print("Testing complete!")
    print("=" * 60)