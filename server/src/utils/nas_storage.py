import os
import stat
import logging
from pathlib import Path
from typing import Optional, Union
from contextlib import contextmanager
from io import BytesIO
from datetime import datetime

# Optional import for paramiko - graceful fallback if not available
try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    paramiko = None
    PARAMIKO_AVAILABLE = False
    logging.warning("paramiko not installed. NAS storage functionality will be disabled.")

class NASStorage:
    """
    Utility class for connecting to QNAP NAS via SFTP and managing file operations.
    Handles saving mockups, designs, and print files to the NAS at /share/Graphics/{shop_name}/
    """
    
    def __init__(self):
        # Check if paramiko is available first
        if not PARAMIKO_AVAILABLE:
            self.enabled = False
            logging.warning("NAS storage disabled: paramiko module not available")
            return
            
        self.host = os.getenv('QNAP_HOST')
        self.port = int(os.getenv('QNAP_PORT', '22'))
        self.username = os.getenv('QNAP_USERNAME')
        self.password = os.getenv('QNAP_PASSWORD')
        self.base_path = os.getenv('NAS_BASE_PATH', '/share/Graphics')
        
        if not all([self.host, self.username, self.password]):
            logging.warning("QNAP NAS credentials not fully configured. NAS storage will be disabled.")
            self.enabled = False
        else:
            self.enabled = True
            logging.info(f"NAS storage configured for host: {self.host}")
    
    @contextmanager
    def get_sftp_connection(self):
        """Context manager for SFTP connections with automatic cleanup"""
        if not self.enabled or not PARAMIKO_AVAILABLE:
            raise Exception("NAS storage is not enabled. Check QNAP configuration or paramiko installation.")
        
        ssh = None
        sftp = None
        try:
            # Create SSH connection
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=30
            )
            
            # Create SFTP connection
            sftp = ssh.open_sftp()
            yield sftp
            
        except Exception as e:
            logging.error(f"Failed to connect to NAS: {e}")
            raise
        finally:
            if sftp:
                sftp.close()
            if ssh:
                ssh.close()
    
    def ensure_directory(self, sftp, directory_path: str) -> bool:
        """
        Ensure directory exists on NAS, creating it if necessary
        Returns True if directory exists or was created successfully
        """
        try:
            # Try to list the directory (this will fail if it doesn't exist)
            sftp.listdir(directory_path)
            return True
        except FileNotFoundError:
            # Directory doesn't exist, try to create it
            try:
                # Create parent directories if they don't exist
                parent_path = str(Path(directory_path).parent)
                if parent_path != '/' and parent_path != directory_path:
                    self.ensure_directory(sftp, parent_path)
                
                sftp.mkdir(directory_path)
                logging.info(f"Created directory on NAS: {directory_path}")
                return True
            except Exception as e:
                logging.error(f"Failed to create directory {directory_path} on NAS: {e}")
                return False
        except Exception as e:
            logging.error(f"Error checking directory {directory_path} on NAS: {e}")
            return False
    
    def upload_file(self, local_file_path: str, shop_name: str, relative_path: str) -> bool:
        """
        Upload a file to the NAS
        
        Args:
            local_file_path: Path to the local file to upload
            shop_name: Name of the shop (used in NAS path)
            relative_path: Relative path within the shop directory (e.g., 'Mockups/BaseMockups/UVDTF/file.png')
        
        Returns:
            bool: True if upload successful, False otherwise
        """
        if not self.enabled:
            logging.warning("NAS storage disabled, skipping upload")
            return False
        
        if not os.path.exists(local_file_path):
            logging.error(f"Local file does not exist: {local_file_path}")
            return False
        
        try:
            with self.get_sftp_connection() as sftp:
                # Build the remote path
                remote_dir = f"{self.base_path}/{shop_name}"
                remote_file_path = f"{remote_dir}/{relative_path}"
                remote_dir_for_file = str(Path(remote_file_path).parent)
                
                # Ensure directory exists
                if not self.ensure_directory(sftp, remote_dir_for_file):
                    return False
                
                # Upload the file
                sftp.put(local_file_path, remote_file_path)
                logging.info(f"Successfully uploaded {local_file_path} to NAS: {remote_file_path}")
                return True
                
        except Exception as e:
            logging.error(f"Failed to upload {local_file_path} to NAS: {e}")
            return False
    
    def save_file_content(self, file_content: bytes, shop_name: str, relative_path: str, local_root_path: Optional[str] = None) -> tuple[bool, str]:
        """
        Save file content either locally + NAS or directly to NAS based on environment
        
        Args:
            file_content: File content as bytes
            shop_name: Name of the shop
            relative_path: Relative path within the shop directory
            local_root_path: Local root path (if None, saves only to NAS)
        
        Returns:
            tuple: (success: bool, file_path: str) - file_path is NAS path if local_root_path is None
        """
        # If local_root_path is provided and we have local storage, save locally and upload to NAS
        if local_root_path:
            import os
            local_file_path = os.path.join(local_root_path, shop_name, relative_path)
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
            
            # Save locally
            with open(local_file_path, "wb") as f:
                f.write(file_content)
                
            # Also upload to NAS
            self.upload_file_content(file_content, shop_name, relative_path)
            return True, local_file_path
            
        # If no local root path, save directly to NAS only (production mode)
        else:
            success = self.upload_file_content(file_content, shop_name, relative_path)
            nas_path = f"{self.base_path}/{shop_name}/{relative_path}" if success else ""
            return success, nas_path

    def upload_file_content(self, file_content: bytes, shop_name: str, relative_path: str) -> bool:
        """
        Upload file content directly to the NAS without saving locally first
        
        Args:
            file_content: File content as bytes
            shop_name: Name of the shop (used in NAS path)
            relative_path: Relative path within the shop directory
        
        Returns:
            bool: True if upload successful, False otherwise
        """
        if not self.enabled:
            logging.warning("NAS storage disabled, skipping upload")
            return False
        
        try:
            with self.get_sftp_connection() as sftp:
                # Build the remote path
                remote_dir = f"{self.base_path}/{shop_name}"
                remote_file_path = f"{remote_dir}/{relative_path}"
                remote_dir_for_file = str(Path(remote_file_path).parent)
                
                # Ensure directory exists
                if not self.ensure_directory(sftp, remote_dir_for_file):
                    return False
                
                # Upload file content using BytesIO
                file_obj = BytesIO(file_content)
                sftp.putfo(file_obj, remote_file_path)
                logging.info(f"Successfully uploaded content to NAS: {remote_file_path}")
                return True
                
        except Exception as e:
            logging.error(f"Failed to upload content to NAS: {e}")
            return False
    
    def download_file(self, shop_name: str, relative_path: str, local_file_path: str) -> bool:
        """
        Download a file from the NAS
        
        Args:
            shop_name: Name of the shop
            relative_path: Relative path within the shop directory
            local_file_path: Where to save the file locally
        
        Returns:
            bool: True if download successful, False otherwise
        """
        if not self.enabled:
            logging.warning("NAS storage disabled, skipping download")
            return False
        
        try:
            with self.get_sftp_connection() as sftp:
                remote_file_path = f"{self.base_path}/{shop_name}/{relative_path}"
                
                # Ensure local directory exists
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                
                # Download the file
                sftp.get(remote_file_path, local_file_path)
                logging.info(f"Successfully downloaded {remote_file_path} from NAS to {local_file_path}")
                return True
                
        except Exception as e:
            logging.error(f"Failed to download {relative_path} from NAS: {e}")
            return False
    
    def file_exists(self, shop_name: str, relative_path: str) -> bool:
        """
        Check if a file exists on the NAS
        
        Args:
            shop_name: Name of the shop
            relative_path: Relative path within the shop directory
        
        Returns:
            bool: True if file exists, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            with self.get_sftp_connection() as sftp:
                remote_file_path = f"{self.base_path}/{shop_name}/{relative_path}"
                sftp.stat(remote_file_path)
                return True
        except FileNotFoundError:
            return False
        except Exception as e:
            logging.error(f"Error checking file existence on NAS: {e}")
            return False
    
    def list_files(self, shop_name: str, relative_path: str = "") -> list:
        """
        List files in a directory on the NAS with metadata

        Args:
            shop_name: Name of the shop
            relative_path: Relative path within the shop directory

        Returns:
            list: List of file info dicts with filename, size, modified, empty list if error
        """
        if not self.enabled:
            return []

        try:
            with self.get_sftp_connection() as sftp:
                remote_dir = f"{self.base_path}/{shop_name}/{relative_path}" if relative_path else f"{self.base_path}/{shop_name}"
                files = []

                # List files with attributes
                for attr in sftp.listdir_attr(remote_dir):
                    if not stat.S_ISDIR(attr.st_mode):  # Only files, not directories
                        files.append({
                            'filename': attr.filename,
                            'size': attr.st_size,
                            'modified': datetime.fromtimestamp(attr.st_mtime) if attr.st_mtime else None
                        })
                return files
        except Exception as e:
            logging.error(f"Failed to list files in {relative_path} on NAS: {e}")
            return []

    def download_file_to_memory(self, shop_name: str, relative_path: str) -> bytes:
        """
        Download a file from the NAS to memory

        Args:
            shop_name: Name of the shop
            relative_path: Relative path within the shop directory

        Returns:
            bytes: File content as bytes, None if error
        """
        if not self.enabled:
            logging.warning("NAS storage disabled, skipping download")
            return None

        try:
            with self.get_sftp_connection() as sftp:
                remote_file_path = f"{self.base_path}/{shop_name}/{relative_path}"

                # Download the file to memory
                file_obj = BytesIO()
                sftp.getfo(remote_file_path, file_obj)
                file_obj.seek(0)
                file_content = file_obj.read()

                logging.info(f"Successfully downloaded {remote_file_path} from NAS to memory ({len(file_content)} bytes)")
                return file_content

        except Exception as e:
            logging.error(f"Failed to download {relative_path} from NAS to memory: {e}")
            return None
    
    def delete_file(self, shop_name: str, relative_path: str) -> bool:
        """
        Delete a file from the NAS
        
        Args:
            shop_name: Name of the shop
            relative_path: Relative path within the shop directory
        
        Returns:
            bool: True if deletion successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            with self.get_sftp_connection() as sftp:
                remote_file_path = f"{self.base_path}/{shop_name}/{relative_path}"
                sftp.remove(remote_file_path)
                logging.info(f"Successfully deleted {remote_file_path} from NAS")
                return True
        except Exception as e:
            logging.error(f"Failed to delete {relative_path} from NAS: {e}")
            return False

# Global instance
nas_storage = NASStorage()