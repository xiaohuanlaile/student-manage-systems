from data_export_import import DataExportImport
from settings import Settings
from tkinter import Tk, Label, Entry, Button, messagebox, filedialog, StringVar
from tkinter import ttk
from fpdf import FPDF
import sqlite3
import matplotlib.pyplot as plt
from tkinter import simpledialog
# LoginApp 类，用于登录界面
class LoginApp:
    def __init__(self, root, db):
        self.root = root
        self.conn = db.conn
        self.cursor = db.cursor
        self.root.title("用户登录")
        self.root.geometry("300x250")

        Label(root, text="用户名:").pack(pady=5)
        self.username_entry = Entry(root)
        self.username_entry.pack(pady=5)

        Label(root, text="密码:").pack(pady=5)
        self.password_entry = Entry(root, show="*")
        self.password_entry.pack(pady=5)

        Button(root, text="登录", command=self.login).pack(pady=10)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        # 使用数据库中的游标验证用户名和密码
        self.cursor.execute("SELECT Password FROM Users WHERE Name = ?", (username,))
        db_password = self.cursor.fetchone()

        if db_password and db_password[0] == password:
            # 根据用户角色启动主界面
            self.cursor.execute("SELECT StudentID, Role FROM Users WHERE Name = ? AND Password = ?", (username, password))
            result = self.cursor.fetchone()
            if result:
                student_id, role = result
                self.root.destroy()  # 关闭登录窗口
                StudentManagementApp(Tk(), role, self.conn, self.cursor, student_id=student_id)
            else:
                messagebox.showerror("登录失败", "角色或学号不正确")
        else:
            messagebox.showerror("登录失败", "用户名或密码错误")


# 学生管理主界面类
class StudentManagementApp:
    def __init__(self, root, role, conn, cursor, student_id=None):
        self.root = root
        self.conn = conn
        self.cursor = cursor
        self.student_id = student_id  # 保存登录的学生ID
        self.role = role
        self.data_import_export = DataExportImport(conn, cursor)

        # 根据角色创建不同的界面
        self.tab_control = ttk.Notebook(root)
        if role == 'teacher':
            self.create_student_tab()
            self.create_score_tab()
            self.create_export_import_tab()
            self.create_anomaly_handling_tab()
            self.create_all_scores_tab()  # 添加此行，创建所有学生成绩展示的标签页
            # 其他教师界面...
        elif role == 'student':
            self.create_view_own_scores_tab()  # 学生仅能查看自己的成绩

        self.tab_control.pack(expand=1, fill='both')
        # 美化界面...

        style = ttk.Style()
        style.configure("TLabel", font=("Arial", 12))
        style.configure("TButton", font=("Arial", 10))
        style.configure("TNotebook", font=("Arial", 12), padding=5)
        style.configure("TNotebook.Tab", font=("Arial", 11), padding=[10, 5])

    def load_students_into_combo(self):
        self.cursor.execute("SELECT Name FROM Students")
        students = [student[0] for student in self.cursor.fetchall()]
        self.student_combo['values'] = students  # 将学生名称列表设置为下拉框的选项
    def create_anomaly_handling_tab(self):
        self.anomaly_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.anomaly_tab, text="异常数据处理")

        Label(self.anomaly_tab, text="异常数据列表:").grid(row=0, column=0, padx=10, pady=5)

        # 异常数据的表格显示
        self.anomaly_tree = ttk.Treeview(self.anomaly_tab, columns=("ID", "StudentID", "ScoreID", "Description", "DetectedAt"), show="headings")
        self.anomaly_tree.heading("ID", text="ID")
        self.anomaly_tree.heading("StudentID", text="学生ID")
        self.anomaly_tree.heading("ScoreID", text="成绩ID")
        self.anomaly_tree.heading("Description", text="异常描述")
        self.anomaly_tree.heading("DetectedAt", text="检测时间")
        self.anomaly_tree.grid(row=1, column=0, columnspan=3, padx=10, pady=10)

        # 添加编辑和删除按钮
        Button(self.anomaly_tab, text="编辑异常", command=self.edit_anomaly).grid(row=2, column=0, pady=5)
        Button(self.anomaly_tab, text="删除异常", command=self.delete_anomaly).grid(row=2, column=1, pady=5)

        # 加载异常数据到界面
        self.load_anomalies()
    def load_students(self):
        for row in self.student_tree.get_children():
            self.student_tree.delete(row)

        # 教师查看所有学生数据
        self.cursor.execute("SELECT * FROM Students")
        for student in self.cursor.fetchall():
            self.student_tree.insert("", "end", values=student)

    from tkinter import simpledialog, messagebox

    def delete_anomaly(self):
        # 获取选中的异常数据项
        selected_items = self.anomaly_tree.selection()

        # 检查是否选择了异常数据
        if not selected_items:
            messagebox.showwarning("警告", "请先选择一个或多个异常记录进行删除")
            return

        # 确认删除操作
        confirm = messagebox.askyesno("确认删除", "确定要删除选中的异常记录吗？")

        if confirm:
            # 循环删除所有选中的异常数据
            for item in selected_items:
                anomaly_info = self.anomaly_tree.item(item, "values")
                anomaly_id = anomaly_info[0]

                # 在数据库中删除对应 ID 的异常数据
                self.cursor.execute("DELETE FROM ExceptionDataHandling WHERE Id = ?", (anomaly_id,))

            # 提交事务
            self.conn.commit()

            # 从界面中删除选中项
            for item in selected_items:
                self.anomaly_tree.delete(item)

            # 提示用户删除成功
            messagebox.showinfo("删除成功", "选中的异常数据已成功删除。")

            # 重新加载异常数据，确保界面同步更新
            self.load_anomalies()

    def load_anomalies(self):
        # 清空现有异常数据列表
        for row in self.anomaly_tree.get_children():
            self.anomaly_tree.delete(row)

        # 从 ExceptionDataHandling 表中查询异常数据
        self.cursor.execute("SELECT Id, StudentID, ScoreID, Description, DetectedAt FROM ExceptionDataHandling")
        anomalies = self.cursor.fetchall()

        # 将查询到的异常数据插入到 Treeview 控件中
        for anomaly in anomalies:
            self.anomaly_tree.insert("", "end", values=anomaly)

    def update_student_combo(self):
        # 从数据库中获取学生名称
        self.cursor.execute("SELECT Name FROM Students")
        students = [student[0] for student in self.cursor.fetchall()]
        # 更新下拉选项
        self.student_combo['values'] = students

    def create_all_scores_tab(self):
        # 创建展示所有学生成绩的标签页
        self.all_scores_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.all_scores_tab, text="所有学生成绩")

        # 添加表头标签
        Label(self.all_scores_tab, text="所有学生成绩（含平均分和最高分）", font=("Arial", 14)).pack(pady=10)

        # 创建表格视图
        columns = ("StudentID", "Name", "Course", "RegularGrade", "MidtermGrade", "FinalGrade", "Average", "Highest")
        self.all_scores_tree = ttk.Treeview(self.all_scores_tab, columns=columns, show="headings")

        # 定义表格列的标题
        self.all_scores_tree.heading("StudentID", text="学生ID")
        self.all_scores_tree.heading("Name", text="姓名")
        self.all_scores_tree.heading("Course", text="课程")
        self.all_scores_tree.heading("RegularGrade", text="平时成绩")
        self.all_scores_tree.heading("MidtermGrade", text="期中成绩")
        self.all_scores_tree.heading("FinalGrade", text="期末成绩")
        self.all_scores_tree.heading("Average", text="平均分")
        self.all_scores_tree.heading("Highest", text="最高分")

        # 调整列宽
        for col in columns:
            self.all_scores_tree.column(col, width=100, anchor='center')

        # 将表格添加到标签页中
        self.all_scores_tree.pack(expand=True, fill='both', padx=10, pady=10)

        # 加载所有学生成绩数据
        self.load_all_scores()

    def load_all_scores(self):
        # 清空表格中的现有数据
        for row in self.all_scores_tree.get_children():
            self.all_scores_tree.delete(row)

        # 查询所有学生成绩和各科的平均分、最高分
        query = '''
            SELECT Students.StudentID, Students.Name, Courses.CourseName,
                   Scores.RegularGrade, Scores.MidtermGrade, Scores.FinalGrade,
                   AVG((Scores.RegularGrade + Scores.MidtermGrade + Scores.FinalGrade) / 3.0) AS AverageScore,
                   MAX((Scores.RegularGrade + Scores.MidtermGrade + Scores.FinalGrade) / 3.0) AS HighestScore
            FROM Scores
            JOIN Students ON Scores.StudentID = Students.StudentID
            JOIN Courses ON Scores.CourseID = Courses.CourseID
            GROUP BY Students.StudentID, Courses.CourseID
            ORDER BY Students.StudentID, Courses.CourseID
        '''
        self.cursor.execute(query)
        all_scores = self.cursor.fetchall()

        # 将查询结果插入到表格中
        for score in all_scores:
            self.all_scores_tree.insert("", "end", values=score)
    def fill_entries_from_selection(self):
        selected_item = self.student_tree.selection()
        if not selected_item:
            messagebox.showwarning("警告", "请先选择一名学生")
            return

        # 获取选中的学生信息
        student_info = self.student_tree.item(selected_item, "values")

        # 将信息填入输入框
        self.name_entry.delete(0, 'end')
        self.name_entry.insert(0, student_info[1])

        self.gender_entry.delete(0, 'end')
        self.gender_entry.insert(0, student_info[2])

        self.age_entry.delete(0, 'end')
        self.age_entry.insert(0, student_info[3])

        self.class_entry.delete(0, 'end')
        self.class_entry.insert(0, student_info[4])

        self.enrollment_date_entry.delete(0, 'end')
        self.enrollment_date_entry.insert(0, student_info[5])

    def create_settings_tab(self):
        if self.role == 'teacher':  # 仅限管理员（假设 teacher 是管理员）
            self.create_student_management_tab()  # 添加学生信息维护界面
            self.settings_tab = ttk.Frame(self.tab_control)
            self.tab_control.add(self.settings_tab, text="系统设置")

            # 添加配置项的输入框和标签
            Label(self.settings_tab, text="系统主题:").grid(row=0, column=0, padx=10, pady=5, sticky='e')
            self.theme_entry = Entry(self.settings_tab)
            self.theme_entry.grid(row=0, column=1, padx=10, pady=5)
            self.theme_entry.insert(0, Settings.get_setting("Theme") or "默认主题")  # 预加载现有配置

            Label(self.settings_tab, text="默认语言:").grid(row=1, column=0, padx=10, pady=5, sticky='e')
            self.language_entry = Entry(self.settings_tab)
            self.language_entry.grid(row=1, column=1, padx=10, pady=5)
            self.language_entry.insert(0, Settings.get_setting("Language") or "中文")  # 预加载现有配置

            # 保存按钮
            Button(self.settings_tab, text="保存设置", command=self.save_settings).grid(row=2, column=0, columnspan=2,
                                                                                        pady=10)

            # 重置按钮
            Button(self.settings_tab, text="重置设置", command=self.reset_settings).grid(row=3, column=0, columnspan=2,
                                                                                        pady=10)

    def edit_anomaly(self):
        selected_item = self.anomaly_tree.selection()
        if not selected_item:
            messagebox.showwarning("警告", "请先选择一个异常记录进行编辑")
            return

        # 获取选中的异常数据的 ID 和当前描述
        anomaly_info = self.anomaly_tree.item(selected_item, "values")
        anomaly_id, student_id, score_id, description, detected_at = anomaly_info

        # 弹出输入框以输入新的描述或成绩数据
        new_description = simpledialog.askstring("编辑异常", f"编辑异常描述 (ID: {anomaly_id})",
                                                 initialvalue=description)
        if new_description is not None:
            self.cursor.execute("UPDATE ExceptionDataHandling SET Description = ? WHERE Id = ?",
                                (new_description, anomaly_id))
            self.conn.commit()
            self.load_anomalies()
            messagebox.showinfo("编辑成功", f"异常ID {anomaly_id} 已成功更新")

        # 选择是否纠正成绩数据
        if messagebox.askyesno("纠正成绩", "是否纠正该成绩数据？"):
            new_regular_grade = simpledialog.askfloat("输入平时成绩", "请输入新的平时成绩（0-100）：")
            new_midterm_grade = simpledialog.askfloat("输入期中成绩", "请输入新的期中成绩（0-100）：")
            new_final_grade = simpledialog.askfloat("输入期末成绩", "请输入新的期末成绩（0-100）：")

            if new_regular_grade is not None and new_midterm_grade is not None and new_final_grade is not None:
                self.cursor.execute('''
                    UPDATE Scores
                    SET RegularGrade = ?, MidtermGrade = ?, FinalGrade = ?
                    WHERE ScoreID = ?
                ''', (new_regular_grade, new_midterm_grade, new_final_grade, score_id))
                self.conn.commit()
                messagebox.showinfo("纠正成功", f"成绩ID {score_id} 的成绩已更新。")

    def create_student_management_tab(self):
        # 创建学生信息维护的标签页
        self.student_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.student_tab, text="学生信息维护")

        # 输入字段和标签
        Label(self.student_tab, text="姓名:").grid(row=0, column=0, padx=10, pady=5)
        self.name_entry = Entry(self.student_tab)
        self.name_entry.grid(row=0, column=1, padx=10, pady=5)

        Label(self.student_tab, text="性别:").grid(row=1, column=0, padx=10, pady=5)
        self.gender_entry = Entry(self.student_tab)
        self.gender_entry.grid(row=1, column=1, padx=10, pady=5)

        Label(self.student_tab, text="年龄:").grid(row=2, column=0, padx=10, pady=5)
        self.age_entry = Entry(self.student_tab)
        self.age_entry.grid(row=2, column=1, padx=10, pady=5)

        Label(self.student_tab, text="班级:").grid(row=3, column=0, padx=10, pady=5)
        self.class_entry = Entry(self.student_tab)
        self.class_entry.grid(row=3, column=1, padx=10, pady=5)

        Label(self.student_tab, text="入学日期:").grid(row=4, column=0, padx=10, pady=5)
        self.enrollment_date_entry = Entry(self.student_tab)
        self.enrollment_date_entry.grid(row=4, column=1, padx=10, pady=5)

        # **添加用户名和密码输入框**
        Label(self.student_tab, text="用户名:").grid(row=5, column=0, padx=10, pady=5)
        self.username_entry = Entry(self.student_tab)
        self.username_entry.grid(row=5, column=1, padx=10, pady=5)

        Label(self.student_tab, text="密码:").grid(row=6, column=0, padx=10, pady=5)
        self.password_entry = Entry(self.student_tab, show="*")
        self.password_entry.grid(row=6, column=1, padx=10, pady=5)

        # 按钮：添加学生、查看学生列表、删除学生
        Button(self.student_tab, text="添加学生", command=self.add_student).grid(row=7, column=0, padx=10, pady=10)
        Button(self.student_tab, text="查看学生列表", command=self.load_students).grid(row=7, column=1, padx=10,
                                                                                       pady=10)
        Button(self.student_tab, text="删除学生", command=self.delete_student).grid(row=7, column=2, padx=10, pady=10)

        # 学生列表显示表格
        self.student_tree = ttk.Treeview(self.student_tab,
                                         columns=("ID", "Name", "Gender", "Age", "Class", "EnrollmentDate"),
                                         show="headings")
        self.student_tree.heading("ID", text="ID")
        self.student_tree.heading("Name", text="姓名")
        self.student_tree.heading("Gender", text="性别")
        self.student_tree.heading("Age", text="年龄")
        self.student_tree.heading("Class", text="班级")
        self.student_tree.heading("EnrollmentDate", text="入学日期")
        self.student_tree.grid(row=8, column=0, columnspan=3, padx=10, pady=10)

        # 加载学生信息到表格
        self.load_students()
        self.student_tree.bind("<<TreeviewSelect>>", lambda event: self.fill_entries_from_selection())

    def save_settings(self):
        theme = self.theme_entry.get()
        language = self.language_entry.get()
        Settings.set_setting("Theme", theme)
        Settings.set_setting("Language", language)
        messagebox.showinfo("保存成功", "系统设置已保存。")

    def reset_settings(self):
        Settings.reset_settings()
        self.theme_entry.delete(0, 'end')
        self.language_entry.delete(0, 'end')
        self.theme_entry.insert(0, "默认主题")
        self.language_entry.insert(0, "中文")
        messagebox.showinfo("重置成功", "系统设置已重置为默认值。")
    def plot_student_performance(self, student_id):
        # 查询学生的所有课程成绩
        self.cursor.execute('''
            SELECT Courses.CourseName, Scores.RegularGrade, Scores.MidtermGrade, Scores.FinalGrade
            FROM Scores
            JOIN Courses ON Scores.CourseID = Courses.CourseID
            WHERE Scores.StudentID = ?
        ''', (student_id,))
        scores = self.cursor.fetchall()

        # 检查是否有成绩记录
        if not scores:
            messagebox.showinfo("图表", "没有找到该学生的成绩数据。")
            return

        # 提取课程名称和成绩数据
        course_names = [score[0] for score in scores]
        regular_grades = [score[1] for score in scores]
        midterm_grades = [score[2] for score in scores]
        final_grades = [score[3] for score in scores]

        # 横轴为“平时、期中、期末”，纵轴为成绩
        stages = ['平时', '期中', '期末']

        plt.figure(figsize=(10, 6))

        # 为每门课程绘制一条折线
        for i, course_name in enumerate(course_names):
            plt.plot(stages, [regular_grades[i], midterm_grades[i], final_grades[i]], marker='o', label=course_name)

        # 添加图例、标题和标签
        plt.title("学生各学科成绩表现")
        plt.xlabel("考试阶段")
        plt.ylabel("成绩")
        plt.legend(title="课程名称")  # 显示课程名称图例
        plt.ylim(0, 100)  # 假设成绩范围为0到100
        plt.tight_layout()
        plt.show()

    def delete_student(self):
        selected_item = self.student_tree.selection()
        if not selected_item:
            messagebox.showwarning("警告", "请先选择一名学生")
            return

        # 获取选中的学生ID
        student_info = self.student_tree.item(selected_item, "values")
        student_id = student_info[0]

        # 确认删除
        confirm = messagebox.askyesno("确认删除", f"确定要删除学生ID {student_id} 吗？")
        if confirm:
            # 从数据库中删除该学生
            self.cursor.execute("DELETE FROM Students WHERE StudentID = ?", (student_id,))
            self.conn.commit()

            # 从界面中删除选中项
            self.student_tree.delete(selected_item)
            messagebox.showinfo("删除成功", f"学生ID {student_id} 已成功删除")

    def export_report_as_pdf(self, student_id):
        self.cursor.execute('''
            SELECT Courses.CourseName, Scores.RegularGrade, Scores.MidtermGrade, Scores.FinalGrade
            FROM Scores
            JOIN Courses ON Scores.CourseID = Courses.CourseID
            WHERE Scores.StudentID = ?
        ''', (student_id,))

        scores = self.cursor.fetchall()

        if not scores:
            messagebox.showinfo("报告", "没有找到该学生的成绩数据。")
            return

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 12)

        # 设置 PDF 的标题
        title = f"Student ID: {student_id} Academic Performance Report"
        pdf.cell(200, 10, title, ln=True, align='C')
        pdf.set_font("Arial", "", 10)

        pdf.cell(40, 10, "Course", border=1)
        pdf.cell(30, 10, "Regular", border=1)
        pdf.cell(30, 10, "Midterm", border=1)
        pdf.cell(30, 10, "Final", border=1)
        pdf.cell(30, 10, "Average", border=1)
        pdf.ln()

        total_sum, subject_count = 0, 0
        for course, regular, midterm, final in scores:
            average = (regular + midterm + final) / 3
            pdf.cell(40, 10, course.encode('latin-1', 'replace').decode('latin-1'), border=1)  # 处理 Unicode 编码
            pdf.cell(30, 10, str(regular), border=1)
            pdf.cell(30, 10, str(midterm), border=1)
            pdf.cell(30, 10, str(final), border=1)
            pdf.cell(30, 10, f"{average:.2f}", border=1)
            pdf.ln()
            total_sum += average
            subject_count += 1

        overall_average = total_sum / subject_count if subject_count > 0 else 0
        pdf.cell(160, 10, f"Overall Average: {overall_average:.2f}", border=1)

        pdf.output(f"student_{student_id}_report.pdf")
        messagebox.showinfo("导出成功", f"报告已保存为 student_{student_id}_report.pdf")

    def generate_student_report(self, student_id):
        self.cursor.execute('''
            SELECT Courses.CourseName, Scores.RegularGrade, Scores.MidtermGrade, Scores.FinalGrade
            FROM Scores
            JOIN Courses ON Scores.CourseID = Courses.CourseID
            WHERE Scores.StudentID = ?
        ''', (student_id,))
        scores = self.cursor.fetchall()

        if not scores:
            messagebox.showinfo("报告", "没有找到该学生的成绩数据。")
            return

        report_text = f"学生ID: {student_id} 学业表现报告\n"
        report_text += "课程名称\t平时成绩\t期中成绩\t期末成绩\t平均成绩\n"
        total_sum, subject_count = 0, 0

        for course, regular, midterm, final in scores:
            average = (regular + midterm + final) / 3
            report_text += f"{course}\t{regular}\t{midterm}\t{final}\t{average:.2f}\n"
            total_sum += average
            subject_count += 1

        overall_average = total_sum / subject_count if subject_count > 0 else 0
        report_text += f"\n总体平均成绩: {overall_average:.2f}"

        messagebox.showinfo("学业表现报告", report_text)

    def check_for_anomalies(self):
        # 使用 self.cursor 而不是 cursor
        self.cursor.execute('''
            SELECT ScoreID, StudentID, RegularGrade, MidtermGrade, FinalGrade
            FROM Scores
            WHERE RegularGrade < 0 OR RegularGrade > 100
            OR MidtermGrade < 0 OR MidtermGrade > 100
            OR FinalGrade < 0 OR FinalGrade > 100
        ''')
        anomalies = self.cursor.fetchall()

        for anomaly in anomalies:
            score_id, student_id, regular, midterm, final = anomaly
            description = f"异常成绩: 平时{regular}, 期中{midterm}, 期末{final}"

            # 插入异常数据记录到 ExceptionDataHandling 表
            self.cursor.execute('''
                INSERT INTO ExceptionDataHandling (DataType, ExceptionRule, StudentID, ScoreID, Description)
                VALUES (?, ?, ?, ?, ?)
            ''', ("成绩", "成绩超出合理范围", student_id, score_id, description))

        self.conn.commit()
        messagebox.showinfo("检测完成", f"检测到 {len(anomalies)} 条异常数据。")
        self.load_anomalies()  # 检测完成后加载异常数据到界面

    def create_student_tab(self):
        if self.role == 'teacher':
            self.student_tab = ttk.Frame(self.tab_control)
            self.tab_control.add(self.student_tab, text="学生管理")

            # 输入字段和标签
            Label(self.student_tab, text="姓名:").grid(row=0, column=0, padx=10, pady=5)
            self.name_entry = Entry(self.student_tab)
            self.name_entry.grid(row=0, column=1, padx=10, pady=5)

            Label(self.student_tab, text="性别:").grid(row=1, column=0, padx=10, pady=5)
            self.gender_entry = Entry(self.student_tab)
            self.gender_entry.grid(row=1, column=1, padx=10, pady=5)

            Label(self.student_tab, text="年龄:").grid(row=2, column=0, padx=10, pady=5)
            self.age_entry = Entry(self.student_tab)
            self.age_entry.grid(row=2, column=1, padx=10, pady=5)

            Label(self.student_tab, text="班级:").grid(row=3, column=0, padx=10, pady=5)
            self.class_entry = Entry(self.student_tab)
            self.class_entry.grid(row=3, column=1, padx=10, pady=5)

            Label(self.student_tab, text="入学日期:").grid(row=4, column=0, padx=10, pady=5)
            self.enrollment_date_entry = Entry(self.student_tab)
            self.enrollment_date_entry.grid(row=4, column=1, padx=10, pady=5)

            # **添加用户名和密码输入框**
            Label(self.student_tab, text="用户名:").grid(row=5, column=0, padx=10, pady=5)
            self.username_entry = Entry(self.student_tab)
            self.username_entry.grid(row=5, column=1, padx=10, pady=5)

            Label(self.student_tab, text="密码:").grid(row=6, column=0, padx=10, pady=5)
            self.password_entry = Entry(self.student_tab, show="*")
            self.password_entry.grid(row=6, column=1, padx=10, pady=5)

            # 按钮：添加学生、查看学生列表、删除学生
            Button(self.student_tab, text="添加学生", command=self.add_student).grid(row=7, column=0, padx=10, pady=10)
            Button(self.student_tab, text="查看学生列表", command=self.load_students).grid(row=7, column=1, padx=10,
                                                                                           pady=10)
            Button(self.student_tab, text="删除学生", command=self.delete_student).grid(row=7, column=2, padx=10,
                                                                                        pady=10)

            # 学生列表显示表格
            self.student_tree = ttk.Treeview(self.student_tab,
                                             columns=("ID", "Name", "Gender", "Age", "Class", "EnrollmentDate"),
                                             show="headings")
            self.student_tree.heading("ID", text="ID")
            self.student_tree.heading("Name", text="姓名")
            self.student_tree.heading("Gender", text="性别")
            self.student_tree.heading("Age", text="年龄")
            self.student_tree.heading("Class", text="班级")
            self.student_tree.heading("EnrollmentDate", text="入学日期")
            self.student_tree.grid(row=8, column=0, columnspan=3, padx=10, pady=10)

            # 加载学生信息到表格
            self.load_students()
            self.student_tree.bind("<<TreeviewSelect>>", lambda event: self.fill_entries_from_selection())

    def add_student(self):
        # 获取输入的数据
        name = self.name_entry.get()
        gender = self.gender_entry.get()
        age = self.age_entry.get()
        student_class = self.class_entry.get()
        enrollment_date = self.enrollment_date_entry.get()
        username = self.username_entry.get()
        password = self.password_entry.get()

        # 打印调试信息，查看输入数据
        print(
            f"Adding student - Name: {name}, Gender: {gender}, Age: {age}, Class: {student_class}, Date: {enrollment_date}")

        # 验证输入
        if name and gender and age and student_class and enrollment_date and username and password:
            try:
                # 插入到 Students 表
                self.cursor.execute('''
                    INSERT INTO Students (Name, Gender, Age, Class, EnrollmentDate)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, gender, age, student_class, enrollment_date))
                self.conn.commit()  # 提交到数据库
                student_id = self.cursor.lastrowid  # 获取新插入的学生ID

                # 插入到 Users 表
                self.cursor.execute('''
                    INSERT INTO Users (StudentID, Name, Password, Role)
                    VALUES (?, ?, ?, ?)
                ''', (student_id, username, password, 'student'))
                self.conn.commit()  # 提交到数据库

                # 打印调试信息，查看 Users 表和 Students 表是否正确插入
                self.cursor.execute("SELECT * FROM Students")
                students = self.cursor.fetchall()
                print("Current Students in database:", students)

                self.cursor.execute("SELECT * FROM Users")
                users = self.cursor.fetchall()
                print("Current Users in database:", users)

                messagebox.showinfo("成功", f"学生 {name} 已成功添加，用户名为 {username}。")
                self.clear_entries()
                self.load_students()  # 刷新表格
                self.update_student_combo()  # 添加成功后刷新下拉选项
            except sqlite3.IntegrityError as e:
                print(f"Error inserting student: {e}")
                messagebox.showerror("错误", "用户名已存在，请选择一个不同的用户名。")
        else:
            messagebox.showwarning("输入错误", "请填写所有字段。")

    def edit_student(self):
        # 获取选中的学生记录
        selected_item = self.student_tree.selection()
        if not selected_item:
            messagebox.showwarning("警告", "请先选择一名学生进行编辑")
            return
            # 获取学生ID
            student_id = self.student_tree.item(selected_item, "values")[0]

            # 获取输入的数据
            name = self.name_entry.get()
            gender = self.gender_entry.get()
            age = self.age_entry.get()
            student_class = self.class_entry.get()
            enrollment_date = self.enrollment_date_entry.get()

            # 验证输入
            if name and gender and age and student_class and enrollment_date:
                self.cursor.execute('''
                        UPDATE Students SET Name = ?, Gender = ?, Age = ?, Class = ?, EnrollmentDate = ?
                        WHERE StudentID = ?
                    ''', (name, gender, age, student_class, enrollment_date, student_id))
                self.conn.commit()
                messagebox.showinfo("成功", f"学生 {name} 的信息已更新。")
                self.clear_entries()
                self.load_students()  # 刷新表格
            else:
                messagebox.showwarning("输入错误", "请填写所有字段。")

    def create_analysis_tab(self):
        self.analysis_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.analysis_tab, text="统计与分析")

        Label(self.analysis_tab, text="选择统计类型:").grid(row=0, column=0, padx=10, pady=5)
        self.analysis_option = StringVar()
        self.analysis_combo = ttk.Combobox(self.analysis_tab, textvariable=self.analysis_option)
        self.analysis_combo['values'] = ("平均分", "最高分", "最低分")
        self.analysis_combo.grid(row=0, column=1, padx=10, pady=5)

        Button(self.analysis_tab, text="执行统计", command=self.perform_analysis).grid(row=1, column=0, columnspan=2,
                                                                                       pady=10)

    def perform_analysis(self):
        analysis_type = self.analysis_option.get()
        query = ""
        if analysis_type == "平均分":
            query = "SELECT AVG((RegularGrade + MidtermGrade + FinalGrade) / 3) FROM Scores"
        elif analysis_type == "最高分":
            query = "SELECT MAX((RegularGrade + MidtermGrade + FinalGrade) / 3) FROM Scores"
        elif analysis_type == "最低分":
            query = "SELECT MIN((RegularGrade + MidtermGrade + FinalGrade) / 3) FROM Scores"

        if query:
            self.cursor.execute(query)
            result = self.cursor.fetchone()[0]
            messagebox.showinfo("统计结果", f"{analysis_type}为: {result:.2f}")
        else:
            messagebox.showwarning("错误", "请选择统计类型。")

    def clear_entries(self):
        self.name_entry.delete(0, 'end')
        self.gender_entry.delete(0, 'end')
        self.age_entry.delete(0, 'end')
        self.class_entry.delete(0, 'end')
        self.enrollment_date_entry.delete(0, 'end')

    def create_score_tab(self):
            if self.role != 'teacher':
                return  # 如果不是教师，退出方法

            self.score_tab = ttk.Frame(self.tab_control)
            self.tab_control.add(self.score_tab, text="成绩管理")

            # 添加输入字段和按钮
            Label(self.score_tab, text="选择学生:").grid(row=0, column=0, padx=10, pady=5)
            self.student_combo = ttk.Combobox(self.score_tab)
            self.student_combo.grid(row=0, column=1, padx=10, pady=5)
            self.load_students_into_combo()  # 加载所有学生到下拉框

            Label(self.score_tab, text="课程ID:").grid(row=1, column=0, padx=10, pady=5)
            self.course_id_entry = Entry(self.score_tab)
            self.course_id_entry.grid(row=1, column=1, padx=10, pady=5)

            Label(self.score_tab, text="平时成绩:").grid(row=2, column=0, padx=10, pady=5)
            self.regular_grade_entry = Entry(self.score_tab)
            self.regular_grade_entry.grid(row=2, column=1, padx=10, pady=5)

            Label(self.score_tab, text="期中成绩:").grid(row=3, column=0, padx=10, pady=5)
            self.midterm_grade_entry = Entry(self.score_tab)
            self.midterm_grade_entry.grid(row=3, column=1, padx=10, pady=5)

            Label(self.score_tab, text="期末成绩:").grid(row=4, column=0, padx=10, pady=5)
            self.final_grade_entry = Entry(self.score_tab)
            self.final_grade_entry.grid(row=4, column=1, padx=10, pady=5)

            Button(self.score_tab, text="录入成绩", command=self.add_score).grid(row=5, column=0, columnspan=2, pady=10)

            # 添加检测异常数据的按钮
            Button(self.score_tab, text="检测异常数据", command=self.check_for_anomalies).grid(row=6, column=0,
                                                                                                   columnspan=2, pady=10)

            # 异常数据列表
            self.anomaly_tree = ttk.Treeview(self.score_tab,
                                             columns=("ID", "StudentID", "ScoreID", "Description", "DetectedAt"),
                                             show="headings")
            self.anomaly_tree.heading("ID", text="ID")
            self.anomaly_tree.heading("StudentID", text="学生ID")
            self.anomaly_tree.heading("ScoreID", text="成绩ID")
            self.anomaly_tree.heading("Description", text="异常描述")
            self.anomaly_tree.heading("DetectedAt", text="检测时间")
            self.anomaly_tree.grid(row=7, column=0, columnspan=2, pady=10)
            self.load_anomalies()



    def load_courses_into_combo(self):
            self.cursor.execute("SELECT CourseID, CourseName FROM Courses")
            courses = self.cursor.fetchall()
            course_list = [f"{course[0]} - {course[1]}" for course in courses]
            self.course_combo['values'] = course_list

    # 创建学生查看自己成绩的界面（学生可见）
    def create_view_own_scores_tab(self):
        if self.role != 'student':
            return  # 如果不是学生，退出方法

        self.view_own_scores_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.view_own_scores_tab, text="我的成绩")

        Label(self.view_own_scores_tab, text="我的成绩记录", font=("Arial", 14)).pack(pady=10)

        # 仅显示自己的成绩
        self.own_scores_tree = ttk.Treeview(self.view_own_scores_tab,
                                            columns=("Course", "Regular", "Midterm", "Final"), show="headings")
        self.own_scores_tree.heading("Course", text="课程")
        self.own_scores_tree.heading("Regular", text="平时成绩")
        self.own_scores_tree.heading("Midterm", text="期中成绩")
        self.own_scores_tree.heading("Final", text="期末成绩")
        self.own_scores_tree.pack(expand=True, fill='both', padx=10, pady=10)

        self.load_own_scores()  # 仅加载该学生的成绩数据

        Button(self.view_own_scores_tab, text="生成学业表现报告",
                   command=lambda: self.generate_student_report(self.student_id)).pack(pady=10)
        Button(self.view_own_scores_tab, text="显示学业表现图表",
                   command=lambda: self.plot_student_performance(self.student_id)).pack(pady=10)
        Button(self.view_own_scores_tab, text="导出学业报告为 PDF",
                   command=lambda: self.export_report_as_pdf(self.student_id)).pack(pady=10)

    # 创建数据导入导出页（教师可见）
    def create_export_import_tab(self):
        self.export_import_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.export_import_tab, text="导入/导出数据")

        Button(self.export_import_tab, text="导出数据到 CSV", command=self.data_import_export.export_data).pack(pady=10)
        Button(self.export_import_tab, text="从 CSV 导入数据", command=self.import_data).pack(pady=10)

    def import_data(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            try:
                DataExportImport.import_data(file_path)
                messagebox.showinfo("成功", "数据导入成功")
            except Exception as e:
                messagebox.showerror("错误", f"数据导入失败: {e}")

    # 创建统计分析页（学生和教师都可见）
    def create_analysis_tab(self):
        self.analysis_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.analysis_tab, text="统计与分析")

        Label(self.analysis_tab, text="选择统计类型:").grid(row=0, column=0, padx=10, pady=5)
        self.analysis_option = StringVar()
        self.analysis_combo = ttk.Combobox(self.analysis_tab, textvariable=self.analysis_option)
        self.analysis_combo['values'] = ("平均分", "最高分", "最低分")
        self.analysis_combo.grid(row=0, column=1, padx=10, pady=5)

        Button(self.analysis_tab, text="执行统计", command=self.perform_analysis).grid(row=1, column=0, columnspan=2,
                                                                                       pady=10)

    def perform_analysis(self):
        analysis_type = self.analysis_option.get()
        query = ""
        if analysis_type == "平均分":
            query = "SELECT AVG((RegularGrade + MidtermGrade + FinalGrade) / 3) FROM Scores"
        elif analysis_type == "最高分":
            query = "SELECT MAX((RegularGrade + MidtermGrade + FinalGrade) / 3) FROM Scores"
        elif analysis_type == "最低分":
            query = "SELECT MIN((RegularGrade + MidtermGrade + FinalGrade) / 3) FROM Scores"

        self.cursor.execute(query)
        result = self.cursor.fetchone()[0]
        messagebox.showinfo("统计结果", f"{analysis_type}为: {result:.2f}")


    def add_score(self):
        student_name = self.student_combo.get()
        self.cursor.execute("SELECT StudentID FROM Students WHERE Name = ?", (student_name,))
        result = self.cursor.fetchone()
        if not result:
            messagebox.showwarning("错误", "请选择有效的学生")
            return

        student_id = result[0]
        course_id = self.course_id_entry.get()
        regular_grade = self.regular_grade_entry.get()
        midterm_grade = self.midterm_grade_entry.get()
        final_grade = self.final_grade_entry.get()

        print(f"Inserting score for StudentID: {student_id}, CourseID: {course_id}, "
              f"RegularGrade: {regular_grade}, MidtermGrade: {midterm_grade}, FinalGrade: {final_grade}")

        if course_id and regular_grade and midterm_grade and final_grade:
            self.cursor.execute('''
                INSERT INTO Scores (StudentID, CourseID, RegularGrade, MidtermGrade, FinalGrade)
                VALUES (?, ?, ?, ?, ?)
                ''', (student_id, course_id, regular_grade, midterm_grade, final_grade))
            self.conn.commit()
            messagebox.showinfo("成功", "成绩已成功录入。")

            # 打印 Scores 表的内容
            self.cursor.execute("SELECT * FROM Scores")
            scores = self.cursor.fetchall()
            print("Current Scores in database:", scores)

        else:
            messagebox.showwarning("输入错误", "请填写所有字段。")

    def load_own_scores(self):
        if self.student_id:
            # 使用 JOIN 查询 Scores 和 Courses 表以加载课程名称
            self.cursor.execute('''
                SELECT Courses.CourseName, Scores.RegularGrade, Scores.MidtermGrade, Scores.FinalGrade
                FROM Scores
                JOIN Courses ON Scores.CourseID = Courses.CourseID
                WHERE Scores.StudentID = ?
            ''', (self.student_id,))

            scores = self.cursor.fetchall()

            # 调试信息，查看查询结果
            print(f"Scores for student {self.student_id}:", scores)

            # 清空表格并加载数据
            for row in self.own_scores_tree.get_children():
                self.own_scores_tree.delete(row)
            for score in scores:
                self.own_scores_tree.insert("", "end", values=score)

    def clear_entries(self):
        self.name_entry.delete(0, 'end')
        self.gender_entry.delete(0, 'end')
        self.age_entry.delete(0, 'end')
        self.class_entry.delete(0, 'end')
        self.enrollment_date_entry.delete(0, 'end')

    def import_data(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            try:
                self.data_import_export.import_data(file_path)
                messagebox.showinfo("成功", "数据导入成功")
                self.load_students()  # 重新加载学生列表以显示新数据
            except Exception as e:
                messagebox.showerror("错误", f"数据导入失败: {e}")

    def perform_analysis(self):
        analysis_type = self.analysis_option.get()
        if analysis_type == "平均分":
            self.cursor.execute('SELECT AVG((RegularGrade + MidtermGrade + FinalGrade) / 3) FROM Scores')
            avg_score = self.cursor.fetchone()[0]
            messagebox.showinfo("平均分", f"平均分为: {avg_score:.2f}")
        elif analysis_type == "最高分":
            self.cursor.execute('SELECT MAX((RegularGrade + MidtermGrade + FinalGrade) / 3) FROM Scores')
            max_score = self.cursor.fetchone()[0]
            messagebox.showinfo("最高分", f"最高分为: {max_score:.2f}")
        elif analysis_type == "最低分":
            self.cursor.execute('SELECT MIN((RegularGrade + MidtermGrade + FinalGrade) / 3) FROM Scores')
            min_score = self.cursor.fetchone()[0]
            messagebox.showinfo("最低分", f"最低分为: {min_score:.2f}")
        else:
            messagebox.showwarning("错误", "请选择统计类型。")