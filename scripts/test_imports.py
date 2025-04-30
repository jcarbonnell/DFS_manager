# test_imports.py
try:
    from py_near.account import Account
    from py_near.dapps.core import NEAR
    print("Imports successful")
    print(f"Account: {Account}, NEAR: {NEAR}")
except ImportError as e:
    print(f"Import error: {e}")