import os 
import uuid 
from typing import Optional

from config import Config

class FileUtils:
    
    @staticmethod
    def make_file(file_content: str, file_name: str, file_type: str) -> Optional[str]:
        try:
            unique_id  = str(uuid.uuid4())
            file_name = file_name + ".py" if file_type == "Python" else file_name + ".cpp"
            temp_dir = os.path.join(os.getcwd(), Config.TEMP_FOLDER_TO_READ, unique_id)
            os.makedirs(temp_dir, exist_ok=True)
            path = os.path.join(temp_dir, file_name)
            with open(path, "w", encoding="utf-8") as f:
                f.write(file_content)
            return path
        except Exception:
            return None
    
    @staticmethod
    def delete_file(full_file_path: str):
        try:
            if os.path.exists(full_file_path):
                os.remove(full_file_path)
                temp_dir = os.path.dirname(full_file_path)
                if os.path.exists(temp_dir) and len(os.listdir(temp_dir)) == 0:
                    os.rmdir(temp_dir)
            return True
        except Exception:
            return False