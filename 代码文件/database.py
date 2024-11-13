import sqlite3


class Database:
    def __init__(self):
        # 初始化数据库连接和游标
        self.conn = sqlite3.connect('student_management.db')
        self.cursor = self.conn.cursor()
        self.setup_tables()

    def setup_tables(self):
        # 创建 Users 表，用于用户信息
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                UserID INTEGER PRIMARY KEY AUTOINCREMENT,
                StudentID INTEGER NOT NULL,
                Name TEXT NOT NULL,
                Password TEXT NOT NULL,
                Role TEXT NOT NULL CHECK (Role IN ('teacher', 'student'))
            )
        ''')

        # 创建 Students 表，用于学生信息
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Students (
                StudentID INTEGER PRIMARY KEY AUTOINCREMENT,
                Name TEXT NOT NULL,
                Gender TEXT NOT NULL,
                Age INTEGER NOT NULL,
                Class TEXT NOT NULL,
                EnrollmentDate TEXT NOT NULL
            )
        ''')

        # 创建 Courses 表，用于课程信息
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Courses (
                CourseID INTEGER PRIMARY KEY AUTOINCREMENT,
                CourseName TEXT NOT NULL,
                CourseDescription TEXT
            )
        ''')

        # 创建 Scores 表，用于成绩信息
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Scores (
                ScoreID INTEGER PRIMARY KEY AUTOINCREMENT,
                StudentID INTEGER,
                CourseID INTEGER,
                RegularGrade REAL,
                MidtermGrade REAL,
                FinalGrade REAL,
                FOREIGN KEY (StudentID) REFERENCES Students (StudentID),
                FOREIGN KEY (CourseID) REFERENCES Courses (CourseID)
            )
        ''')

        # 创建 ExceptionDataHandling 表，用于异常数据处理
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ExceptionDataHandling (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                DataType TEXT NOT NULL,
                ExceptionRule TEXT NOT NULL,
                DetectedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                StudentID INTEGER,
                ScoreID INTEGER,
                Description TEXT
            )
        ''')

        # 创建 Settings 表，用于系统设置
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Settings (
                SettingID INTEGER PRIMARY KEY AUTOINCREMENT,
                Name TEXT NOT NULL UNIQUE,
                Value TEXT
            )
        ''')

        self.conn.commit()  # 提交表的创建

    def authenticate_user(self, username, password):
        # 验证用户名和密码是否正确
        self.cursor.execute("SELECT * FROM Users WHERE Name = ? AND Password = ?", (username, password))
        return self.cursor.fetchone()

    def add_user(self, student_id, name, password, role):
        # 添加新用户
        try:
            self.cursor.execute('''
                INSERT INTO Users (StudentID, Name, Password, Role)
                VALUES (?, ?, ?, ?)
            ''', (student_id, name, password, role))
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            print(f"Error adding user: {e}")
            return False
        return True

    def close(self):
        # 关闭数据库连接
        self.conn.close()
