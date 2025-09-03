import os
import hashlib
import json
from datetime import datetime

# 在 GitHub Actions 中，默认工作目录就是仓库根目录
ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) + "/.."
OUTPUT_FILE = os.path.join(ROOT_DIR, "manifest.json")


def file_hash(filepath, algo="md5"):
    """计算文件哈希"""
    h = hashlib.new(algo)
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_manifest(root_dir):
    manifest = {
        "version": datetime.now().strftime("%Y%m%d-%H%M%S"),
        "files": {}
    }

    def should_include_file(filepath):
        """判断文件是否应该被包含"""
        if filepath.endswith("AchievementData.csv"):
            return True
        if filepath.startswith("Posters/") and filepath.lower().endswith(".jpg"):
            return True
        return False

    # 统计符合条件的文件
    total_files = 0
    for root, _, files in os.walk(root_dir):
        for filename in files:
            filepath = os.path.join(root, filename)
            relpath = os.path.relpath(filepath, root_dir).replace("\\", "/")
            if should_include_file(relpath):
                total_files += 1

    print(f"📁 发现 {total_files} 个符合条件的文件，开始处理...")

    processed_files = 0
    for root, _, files in os.walk(root_dir):
        for filename in files:
            filepath = os.path.join(root, filename)
            relpath = os.path.relpath(filepath, root_dir).replace("\\", "/")

            if should_include_file(relpath):
                manifest["files"][relpath] = {
                    "hash": file_hash(filepath, "md5"),
                    "size": os.path.getsize(filepath)
                }

                processed_files += 1
                if processed_files % 5 == 0 or processed_files == total_files:
                    progress = (processed_files / total_files) * 100
                    print(f"⏳ 进度: {processed_files}/{total_files} ({progress:.1f}%) - 当前处理: {relpath}")

    return manifest


if __name__ == "__main__":
    manifest = generate_manifest(ROOT_DIR)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"✅ manifest.json 已生成，共 {len(manifest['files'])} 个文件")
