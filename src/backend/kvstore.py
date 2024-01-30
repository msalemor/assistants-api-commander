import logging
import sqlite3
import json
import uuid
from pydantic import BaseModel


class KVStoreItem(BaseModel):
    username: str
    key: str
    value: str


conn = sqlite3.connect("data/kvstore.db", check_same_thread=False)


def create_store():
    conn.execute(
        "CREATE TABLE IF NOT EXISTS kvstore (username text, key text, value text)")
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS kvstore_index ON kvstore (username, key, value)")


def __read_value(username, key) -> KVStoreItem | None:
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT username, key, value FROM kvstore WHERE username=? AND key=?",
                       (username, key))
        result = cursor.fetchone()
        kv = KVStoreItem(username=result[0], key=result[1], value=result[2])
        if result is None:
            return None
        return kv
    except:
        logging.error(f"Failed to set value for {username} {key}")
        return None
    finally:
        cursor.close()


def __read_values(username: str, key: str) -> list[KVStoreItem]:
    cursor = conn.cursor()
    try:
        if key == None:
            cursor.execute(
                "SELECT username, key, value FROM kvstore WHERE username=?", (username,))
        else:
            cursor.execute("SELECT username, key, value FROM kvstore WHERE username=? AND key=?",
                           (username, key))
        result = cursor.fetchall()
        if result is None:
            return []

        kv_list = []
        for row in result:
            kv_list.append(KVStoreItem(
                username=row[0], key=row[1], value=row[2]))

        cursor.close()

        return kv_list
    except:
        logging.error(f"Failed to read value for {username} {key}")
        return []
    finally:
        cursor.close()


def __upsert_value(username: str, key: str, value: str) -> KVStoreItem:
    cursor = conn.cursor()
    try:
        if key != "file":
            cursor.execute("DELETE from kvstore WHERE username=? and key=?",
                           (username, key))
        else:
            cursor.execute("DELETE from kvstore WHERE username=? and key=? and value=?",
                           (username, key, value))
        cursor.execute("INSERT INTO kvstore VALUES (?, ?, ?)",
                       (username, key, value))
        conn.commit()
        logging.info(f"Value set: {username} {key} {value}")
        return KVStoreItem(username=username, key=key, value=value)
    except:
        logging.error(f"Failed to set value for {username} {key} {value}")
        return None
    finally:
        cursor.close()


def __delete_value(username: str) -> int:
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM kvstore WHERE username=?", (username,))
        conn.commit()
        logging.info(f"For user {username} Deleted {cursor.rowcount} rows")
        return conn.total_changes
    except:
        logging.info(f"Unable to delete the values for {username}")
        return -1
    finally:
        cursor.close()


def create_assistant(user_name: str, name: str, instructions: str, tools: str, assistant_id: str) -> KVStoreItem:
    # This id will be used to create an images folder
    __upsert_value(user_name, "id", str(uuid.uuid4()))
    # The assistant name
    __upsert_value(user_name, "name", name)
    # The assistant instructions
    __upsert_value(user_name, "instructions", instructions)
    # The assistant tools
    __upsert_value(user_name, "tools", tools)
    # The assistant id
    return __upsert_value(user_name, "assistant", assistant_id)


def get_user_id(username: str) -> KVStoreItem | None:
    return __read_value(username, "id")


def get_assistant(username: str) -> KVStoreItem | None:
    return __read_value(username, "assistant")


def create_thread(username: str, thread_id: str) -> KVStoreItem | None:
    return __upsert_value(username, "thread", thread_id)


def get_thread(username: str) -> KVStoreItem | None:
    return __read_value(username, "thread")


def create_files(username: str, file_urls: list[(str, str)]) -> KVStoreItem | None:
    if username is None or username == "":
        logging.error("create_files, No username provided")
        return []
    if file_urls is None or file_urls == []:
        logging.error("create_files, No file urls provided")
        return []
    for (file_name, id) in file_urls:
        fileData = json.dumps({"name": file_name, "id": id})
        __upsert_value(username, "file", fileData)


def get_files(username: str) -> list[KVStoreItem]:
    return __read_values(username, "file")


def delete_file(username: str, file_id: str) -> int:
    return __delete_value(username, file_id)


def get_all(username: str) -> list[KVStoreItem]:
    return __read_values(username, None)


def del_user(username: str) -> int:
    return __delete_value(username)


def tests():
    create_assistant("alex", "assistant_id")
    create_thread("alex", "thread_id")
    create_files("alex", [("file_1", "file_id_1"), ("file_2", "file_id_2")])
    print(get_files("alex"))
    all = get_all("alex")
    for item in all:
        print(item)
    print(del_user("alex"))
