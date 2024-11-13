import pandas as pd
from tkinter import Tk, Label, Entry, Button, messagebox, filedialog, StringVar

class DataExportImport:
    def __init__(self, conn, cursor):
        self.conn = conn
        self.cursor = cursor

    def export_data(self):
        try:
            df_students = pd.read_sql_query("SELECT * FROM Students", self.conn)
            df_courses = pd.read_sql_query("SELECT * FROM Courses", self.conn)
            df_scores = pd.read_sql_query("SELECT * FROM Scores", self.conn)

            # 如果没有数据，给出提示
            if df_students.empty or df_courses.empty or df_scores.empty:
                messagebox.showwarning("警告", "没有数据可导出。")
                return

            df_students.to_csv('students.csv', index=False, encoding='utf-8-sig')
            df_courses.to_csv('courses.csv', index=False, encoding='utf-8-sig')
            df_scores.to_csv('scores.csv', index=False, encoding='utf-8-sig')

            messagebox.showinfo("成功", "数据已导出到 CSV 文件。")

        except Exception as e:
            messagebox.showerror("导出失败", f"出现错误: {e}")

    def import_data(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            try:
                self.data_import_export.import_data(file_path)
                messagebox.showinfo("成功", "数据导入成功")
                self.load_students()  # 重新加载学生列表以显示新数据
            except Exception as e:
                messagebox.showerror("错误", f"数据导入失败: {e}")