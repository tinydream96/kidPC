import hashlib
import requests
import os
import shutil
import configparser


def read_gitignore():
    """
    读取 .gitignore 文件并返回忽略规则列表
    """
    ignore_rules = []
    if os.path.exists('.gitignore'):
        with open('.gitignore', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    ignore_rules.append(line)
    return ignore_rules


def should_ignore(file_path, ignore_rules):
    """
    检查文件是否应被忽略
    """
    for rule in ignore_rules:
        if rule.endswith('/'):
            # 目录规则
            if file_path.startswith(rule.rstrip('/')):
                return True
        elif '*' in rule:
            # 通配符规则
            pattern = rule.replace('.', r'\.').replace('*', '.*')
            import re
            if re.match(pattern, file_path):
                return True
        else:
            # 精确匹配规则
            if file_path == rule:
                return True
    return False


def get_github_file_content(repo_owner, repo_name, file_path, branch='main', proxy=None):
    """
    通过 GitHub API 获取文件内容
    """
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}?ref={branch}"
    headers = {
        "Accept": "application/vnd.github.v3.raw"
    }
    proxies = {}
    if proxy:
        proxies = {
            'http': proxy,
            'https': proxy
        }
    response = requests.get(url, headers=headers, proxies=proxies)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to get file content from GitHub: {response.text}")
        return None


def calculate_file_hash(file_content):
    """
    计算文件内容的哈希值
    """
    hash_object = hashlib.sha256()
    hash_object.update(file_content.encode())
    return hash_object.hexdigest()


def get_local_file_hash(file_path):
    """
    计算本地文件的哈希值
    """
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return calculate_file_hash(content)
    return None


def download_file(url, save_path, proxy=None):
    """
    使用代理下载文件
    """
    proxies = {}
    if proxy:
        proxies = {
            'http': proxy,
            'https': proxy
        }
    response = requests.get(url, stream=True, proxies=proxies)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            shutil.copyfileobj(response.raw, file)
        print(f"File downloaded successfully: {save_path}")
    else:
        print(f"Failed to download file: {response.text}")


def get_all_python_files():
    """
    递归获取当前目录下的所有 Python 文件
    """
    python_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file).replace('\\', '/')
                python_files.append(file_path)
    return python_files


def check_and_update_files(repo_owner, repo_name, branch='main', proxy=None):
    """
    检查并更新文件
    """
    ignore_rules = read_gitignore()
    file_paths = get_all_python_files()
    for file_path in file_paths:
        if should_ignore(file_path, ignore_rules):
            print(f"Skipping {file_path} due to .gitignore rules.")
            continue
        # 获取 GitHub 上文件的内容和哈希值
        github_content = get_github_file_content(repo_owner, repo_name, file_path, branch, proxy)
        if github_content is None:
            continue
        github_hash = calculate_file_hash(github_content)

        # 获取本地文件的哈希值
        local_hash = get_local_file_hash(file_path)

        # 比较哈希值
        if local_hash != github_hash:
            print(f"File {file_path} has an update. Downloading...")
            download_url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/{branch}/{file_path}"
            download_file(download_url, file_path, proxy)
        else:
            print(f"File {file_path} is up to date.")


def main():
    # 读取配置文件
    config = configparser.ConfigParser()
    if not os.path.exists('config.ini'):
        print("config.ini not found!")
        return
    try:
        config.read('config.ini')
        proxy = config.get('Settings', 'proxy', fallback='')
    except Exception as e:
        print(f"Error reading config.ini: {str(e)}")
        return

    # 配置 GitHub 仓库信息
    repo_owner = 'your_github_username'
    repo_name = 'your_repo_name'
    branch = 'main'

    # 检查并更新文件
    check_and_update_files(repo_owner, repo_name, branch, proxy)


if __name__ == "__main__":
    main()