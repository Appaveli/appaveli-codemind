"""
File utility functions for Appaveli CodeMind
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional


class FileUtils:
    """Utility functions for file operations"""
    
    @staticmethod
    def read_file(file_path: str, encoding: str = 'utf-8') -> str:
        """
        Read file content safely
        
        Args:
            file_path: Path to file
            encoding: File encoding (default: utf-8)
            
        Returns:
            File content as string
        """
        try:
            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                return f.read()
        except Exception as e:
            raise IOError(f"Error reading file {file_path}: {e}")
    
    @staticmethod
    def write_file(file_path: str, content: str, encoding: str = 'utf-8') -> None:
        """
        Write content to file safely
        
        Args:
            file_path: Path to file
            content: Content to write
            encoding: File encoding (default: utf-8)
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
        except Exception as e:
            raise IOError(f"Error writing file {file_path}: {e}")
    
    @staticmethod
    def find_files_by_extension(directory: str, extensions: List[str]) -> List[str]:
        """
        Find all files with specified extensions in directory
        
        Args:
            directory: Directory to search
            extensions: List of file extensions (e.g., ['.java', '.kt'])
            
        Returns:
            List of file paths
        """
        files = []
        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                if any(filename.endswith(ext) for ext in extensions):
                    files.append(os.path.join(root, filename))
        return files
    
    @staticmethod
    def backup_file(file_path: str) -> str:
        """
        Create a backup of a file
        
        Args:
            file_path: Path to file to backup
            
        Returns:
            Path to backup file
        """
        backup_path = f"{file_path}.backup"
        shutil.copy2(file_path, backup_path)
        return backup_path
