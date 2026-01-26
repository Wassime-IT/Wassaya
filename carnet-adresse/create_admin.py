
"""
Utility script to create an admin account in the SQLite database.

Usage:
    python create_admin.py
"""
import getpass
from db import create_admin, get_db_path, init_db

def main():
    db_path = get_db_path()
    init_db(db_path)

    username = input("Admin username: ").strip()
    if not username:
        print("Username is required.")
        return

    password = getpass.getpass("Password: ")
    password2 = getpass.getpass("Confirm password: ")
    if password != password2:
        print("Passwords do not match.")
        return

    ok = create_admin(username, password, db_path, is_admin=True)
    if ok:
        print(f"Admin '{username}' created successfully in {db_path}")
    else:
        print("Username already exists.")

if __name__ == "__main__":
    main()
