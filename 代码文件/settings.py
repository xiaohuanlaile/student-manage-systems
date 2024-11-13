class Settings:
    def __init__(self, conn, cursor):
        self.conn = conn
        self.cursor = cursor

    def get_setting(self, name):
        self.cursor.execute("SELECT Value FROM Settings WHERE Name = ?", (name,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def set_setting(self, name, value):
        self.cursor.execute("INSERT OR REPLACE INTO Settings (Name, Value) VALUES (?, ?)", (name, value))
        self.conn.commit()

    def reset_settings(self):
        self.cursor.execute("DELETE FROM Settings")
        self.conn.commit()