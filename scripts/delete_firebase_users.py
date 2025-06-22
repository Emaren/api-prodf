# scripts/delete_firebase_users.py

import firebase_admin
from firebase_admin import auth, credentials

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

uids_to_keep = {
    "3ouPzpiDdZYLaQTbKVOtKe5fR9m2",  # Emaren
    "sBNTpYszj3XkHwsCYtuTQa3yUZ63",  # Tralalero
    "w5AvpfaDgXP14LvjBtYwgbURdaf1",  # AS_godofredo
}

def delete_selected_users():
    page = auth.list_users()
    deleted_count = 0
    skipped_count = 0

    while page:
        for user in page.users:
            if user.uid in uids_to_keep:
                print(f"Skipping user: {user.uid} ({user.email})")
                skipped_count += 1
            else:
                print(f"Deleting user: {user.uid} ({user.email})")
                auth.delete_user(user.uid)
                deleted_count += 1
        page = page.get_next_page()

    print(f"✅ Done. Deleted: {deleted_count}, Skipped: {skipped_count}")

if __name__ == "__main__":
    delete_selected_users()
