import tempfile
import shutil
from git import Repo, GitCommandError

class GitServiceImpl:
    @staticmethod
    def test_connection(config: dict) -> (bool, str):
        url = config.get('url')
        branch = config.get('branch', 'main')
        username = config.get('username')
        token = config.get('token')
        if not url:
            return False, 'URL no especificada'
        # Construir URL con autenticación si es necesario
        if username and token and '://' in url:
            proto, rest = url.split('://', 1)
            url = f"{proto}://{username}:{token}@{rest}"
        temp_dir = tempfile.mkdtemp()
        try:
            Repo.clone_from(url, temp_dir, branch=branch, depth=1, no_checkout=True)
            return True, 'Conexión exitosa'
        except GitCommandError as e:
            return False, f'Error de conexión: {str(e)}'
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True) 