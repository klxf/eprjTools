import sqlite3
import json
from tkinter import messagebox


class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path

    def execute_query(self, query, params=None):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor.fetchall()
        except sqlite3.Error as e:
            error_msg = f"数据库错误: {str(e)}\n查询: {query}"
            messagebox.showerror("数据库错误", error_msg)
            return []
        except Exception as e:
            error_msg = f"执行查询时发生错误: {str(e)}\n查询: {query}"
            messagebox.showerror("错误", error_msg)
            return []

    def get_project_info(self):
        return self.execute_query("""
            SELECT boards FROM projects;
        """)

    def get_documents(self):
        return self.execute_query("""
            SELECT uuid, display_title, docType 
            FROM documents;
        """)

    def get_schematics(self):
        return self.execute_query("""
            SELECT uuid, display_name, sort 
            FROM schematics;
        """)
