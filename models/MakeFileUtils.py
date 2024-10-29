import os
import logging
import uuid
from typing import Optional
from config import Config

class MakeFileUtils:
    
    @staticmethod
    def make_file(file_content: str, file_name: str) -> Optional[str]:
        unique_id = str(uuid.uuid4())
        temp_dir = os.path.join(Config.TEMP_FOLDER, unique_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        path = os.path.join(temp_dir, file_name)
        with open(path, 'w') as file:
            file.write(file_content)
        return path

    @staticmethod
    def delete_file(file_path: str) -> bool:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                temp_dir = os.path.dirname(file_path)
                if os.path.exists(temp_dir) and len(os.listdir(temp_dir)) == 0:
                    os.rmdir(temp_dir)
            return True
        except Exception as e:
            logging.exception(f"Error {e} in deleting file: {file_path}")
            return False
