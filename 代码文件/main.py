from tkinter import Tk
from ui import LoginApp
from database import Database

# 初始化数据库并创建必要的表和示例数据
def initialize_database():
    db = Database()
    return db

if __name__ == "__main__":
    db = initialize_database()  # 初始化数据库
    root = Tk()
    app = LoginApp(root, db)    # 启动登录界面
    root.mainloop()
    db.close()  # 关闭数据库连接
