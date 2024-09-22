import logging
import sqlite3
import uuid
from abc import ABC, abstractmethod

from models import KVStoreItem


class Store(ABC):
    def __init__(self, conn: None):
        self.conn = conn

    @abstractmethod
    def create_store(self):
        pass

    @abstractmethod
    def read_categories(self) -> list[KVStoreItem]:
        pass

    @abstractmethod
    def read_value(self, category: str, key: str) -> KVStoreItem | None:
        pass

    @abstractmethod
    def read_values(self, category: str, key: str) -> list[KVStoreItem]:
        pass

    @abstractmethod
    def upsert_value(self, category: str, key: str, value: str) -> KVStoreItem:
        pass

    @abstractmethod
    def delete_value(self, category: str, key: str, value: str) -> int:
        pass

    @abstractmethod
    def delete_key(self, category: str, key: str) -> int:
        pass

    @abstractmethod
    def delete(self, category: str) -> int:
        pass


class SQLiteCKVStore(Store):
    def __init__(self, conn=None):
        super().__init__(conn)
        if self.conn is None:
            self.conn = sqlite3.connect(
                "data/kvstore.db", check_same_thread=False)

    def create_store(self):
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS kvstore (category text, key text, value text)")
        self.conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS kvstore_index ON kvstore (category, key, value)")

    def read_categories(self) -> list[KVStoreItem]:
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT DISTINCT category FROM kvstore")
            result = cursor.fetchall()
            if result is None:
                return []

            kv_list = []
            for row in result:
                kv_list.append(KVStoreItem(
                    category=row[0], key="", value=""))

            cursor.close()

            return kv_list
        except:
            logging.error(f"Failed to read value for all users")
            return []
        finally:
            cursor.close()

    def read_value(self, category, key) -> KVStoreItem | None:
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT category, key, value FROM kvstore WHERE category=? AND key=?",
                           (category, key))
            result = cursor.fetchone()
            kv = KVStoreItem(
                category=result[0], key=result[1], value=result[2])
            if result is None:
                return None
            return kv
        except:
            logging.error(f"Failed to set value for {category} {key}")
            return None
        finally:
            cursor.close()

    def read_values(self, category: str, key: str = None) -> list[KVStoreItem]:
        cursor = self.conn.cursor()
        try:
            if key == None:
                cursor.execute(
                    "SELECT category, key, value FROM kvstore WHERE category=?", (category,))
            else:
                cursor.execute("SELECT category, key, value FROM kvstore WHERE category=? AND key=?",
                               (category, key))
            result = cursor.fetchall()
            if result is None:
                return []

            kv_list = []
            for row in result:
                kv_list.append(KVStoreItem(
                    category=row[0], key=row[1], value=row[2]))

            cursor.close()

            return kv_list
        except:
            logging.error(f"Failed to read value for {category} {key}")
            return []
        finally:
            cursor.close()

    def upsert_value(self, category: str, key: str, value: str) -> KVStoreItem:
        cursor = self.conn.cursor()
        try:
            if key != "file":
                cursor.execute("DELETE from kvstore WHERE category=? and key=?",
                               (category, key))
            else:
                cursor.execute("DELETE from kvstore WHERE category=? and key=? and value=?",
                               (category, key, value))
            cursor.execute("INSERT INTO kvstore VALUES (?, ?, ?)",
                           (category, key, value))
            self.conn.commit()
            logging.info(f"Value set: {category} {key} {value}")
            return KVStoreItem(category=category, key=key, value=value)
        except:
            logging.error(f"Failed to set value for {category} {key} {value}")
            return None
        finally:
            cursor.close()

    def delete_value(self, category: str, key: str, value: str) -> int:
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM kvstore WHERE category=? and key=? and value=?", (category, key, value))
            self.conn.commit()
            logging.info(f"For user {category} Deleted {cursor.rowcount} rows")
            return self.conn.total_changes
        except:
            logging.info(f"Unable to delete the values for {category}")
            return -1
        finally:
            cursor.close()

    def delete_key(self, category: str, key: str) -> int:
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM kvstore WHERE category=? and key=?", (category, key))
            self.conn.commit()
            logging.info(f"For user {category} Deleted {cursor.rowcount} rows")
            return self.conn.total_changes
        except:
            logging.info(f"Unable to delete the values for {category}")
            return -1
        finally:
            cursor.close()

    def delete(self, category: str) -> int:
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM kvstore WHERE category=?", (category,))
            self.conn.commit()
            logging.info(f"For user {category} Deleted {cursor.rowcount} rows")
            return self.conn.total_changes
        except:
            logging.info(f"Unable to delete the values for {category}")
            return -1
        finally:
            cursor.close()


ckvstore_instance: Store = None


def CKVStoreInstance():
    global ckvstore_instance
    if ckvstore_instance is None:
        ckvstore_instance = SQLiteCKVStore()
        ckvstore_instance.create_store()
    return ckvstore_instance


class AHMemory:
    def __init__(self, store: Store = None):
        self.kvstore: Store = store if store is not None else CKVStoreInstance()

    def get_user(self, username: str) -> list[KVStoreItem]:
        """
        Get all the values for a user in the kvstore
        """
        return self.kvstore.read_values(username, None)

    def del_user(self, username: str) -> int:
        """
        Delete all the values for a user in the kvstore
        """
        return self.kvstore.delete(username)

    def get_all_users(self) -> list[KVStoreItem]:
        """
        Get all the users in the kvstore
        """
        return self.kvstore.read_categories()
        # cursor = self.conn.cursor()
        # try:
        #     cursor.execute("SELECT DISTINCT username FROM kvstore")
        #     result = cursor.fetchall()
        #     if result is None:
        #         return []

        #     kv_list = []
        #     for row in result:
        #         kv_list.append(KVStoreItem(
        #             category=row[0], key="", value=""))

        #     cursor.close()

        #     return kv_list
        # except:
        #     logging.error(f"Failed to read value for all users")
        #     return []
        # finally:
        #     cursor.close()

    def get_user_id(self, username: str) -> KVStoreItem | None:
        return self.kvstore.read_value(username, "id")

    def get_assistant(self, username: str) -> KVStoreItem | None:
        return self.kvstore.read_value(username, "assistant")

    def create_assistant(self, user_name: str, name: str, instructions: str, tools: str, assistant_id: str, thread_id: str, vector_store_id: str) -> KVStoreItem:
        # This id will be used to create an images folder
        self.kvstore.upsert_value(user_name, "id", str(uuid.uuid4()))
        # The assistant name
        self.kvstore.upsert_value(user_name, "name", name)
        # The assistant instructions
        self.kvstore.upsert_value(user_name, "instructions", instructions)
        # The assistant tools
        self.kvstore.upsert_value(user_name, "tools", tools)
        # The thread id
        self.kvstore.upsert_value(user_name, "thread", thread_id)
        self.kvstore.upsert_value(user_name, "vector_store", vector_store_id)
        # The assistant id
        return self.kvstore.upsert_value(user_name, "assistant", assistant_id)

    def del_assistant(self, username: str) -> int:
        return self.kvstore.delete_key(username, "assistant")

    def get_thread(self, username: str) -> KVStoreItem | None:
        return self.kvstore.read_value(username, "thread")

    def create_thread(self, username: str, thread_id: str) -> KVStoreItem | None:
        return self.kvstore.upsert_value(username, "thread", thread_id)

    def del_thread(self, username: str) -> int:
        return self.kvstore.delete_key(username, "thread")

    def get_files(self, username: str) -> list[KVStoreItem]:
        return self.kvstore.read_values(username, "file")

    def create_files(self, username: str, json_data: str) -> list[KVStoreItem]:
        return self.kvstore.upsert_value(username, "files", json_data)

    def create_file(self, username: str, file_id: str) -> list[KVStoreItem]:
        return self.kvstore.upsert_value(username, "file", file_id)

    def delete_file(self, username: str, file_id: str) -> int:
        return self.kvstore.delete_value(username, "file", file_id)

    def delete_files(self, username: str) -> int:
        return self.kvstore.delete_key(username, "files")


ahmemory: AHMemory = None


def AHMemoryInstance():
    global ahmemory
    if ahmemory is None:
        ahmemory = AHMemory()
    return ahmemory
