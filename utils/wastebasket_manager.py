import os
import shutil
from tkinter import messagebox

class WastebasketManager:
    def __init__(self, project_directory):
        self.project_directory = project_directory
        self.wastebasket_path = os.path.join(project_directory, '.wastebasket')
        self.ensure_wastebasket_exists()

    def ensure_wastebasket_exists(self):
        if not os.path.exists(self.wastebasket_path):
            os.makedirs(self.wastebasket_path)

    def list_files(self):
        """获取回收站中的所有.eprj文件"""
        return [f for f in os.listdir(self.wastebasket_path)
                if f.endswith('.eprj')]

    def move_to_wastebasket(self, file_name):
        """将文件移动到回收站"""
        source_path = os.path.join(self.project_directory, file_name)
        target_path = os.path.join(self.wastebasket_path, file_name)
        backup_source = source_path.replace('.eprj', '_backup')
        backup_target = target_path.replace('.eprj', '_backup')

        try:
            # 检查目标文件是否已存在
            if os.path.exists(target_path):
                raise FileExistsError(
                    f"文件 '{file_name}' 已存在于回收站中")

            # 移动主文件
            shutil.move(source_path, target_path)

            # 如果存在备份文件，也移动它
            if os.path.exists(backup_source):
                if os.path.exists(backup_target):
                    shutil.rmtree(backup_target)
                shutil.move(backup_source, backup_target)

            return True

        except Exception as e:
            messagebox.showerror("错误",
                               f"移动文件到回收站时出错: {str(e)}")
            return False

    def restore_file(self, file_name):
        """从回收站还原文件"""
        source_path = os.path.join(self.wastebasket_path, file_name)
        target_path = os.path.join(self.project_directory, file_name)
        backup_source = source_path.replace('.eprj', '_backup')
        backup_target = target_path.replace('.eprj', '_backup')

        try:
            # 检查目标位置是否已存在文件
            if os.path.exists(target_path):
                raise FileExistsError(
                    f"目标位置已存在文件 '{file_name}'")

            # 还原主文件
            shutil.move(source_path, target_path)

            # 如果存在备份文件，也还原它
            if os.path.exists(backup_source):
                if os.path.exists(backup_target):
                    shutil.rmtree(backup_target)
                shutil.move(backup_source, backup_target)

            return True

        except Exception as e:
            messagebox.showerror("错误",
                               f"还原文件时出错: {str(e)}")
            return False

    def delete_file(self, file_name):
        """永久删除回收站中的文件"""
        file_path = os.path.join(self.wastebasket_path, file_name)
        backup_path = file_path.replace('.eprj', '_backup')

        try:
            # 删除主文件
            os.remove(file_path)

            # 如果存在备份目录，也删除它
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)

            return True

        except Exception as e:
            messagebox.showerror("错误",
                               f"永久删除文件时出错: {str(e)}")
            return False
