import os
import hashlib
import json
from datetime import datetime
import subprocess

# 根目录和 manifest
ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) + "/.."
OUTPUT_FILE = os.path.join(ROOT_DIR, "manifest.json")

# OSS 配置，从环境变量读取
OSS_BUCKET = os.getenv("OSS_BUCKET")
OSS_ENDPOINT = os.getenv("OSS_ENDPOINT")
OSS_ACCESS_KEY_ID = os.getenv("OSS_ACCESS_KEY_ID")
OSS_ACCESS_KEY_SECRET = os.getenv("OSS_ACCESS_KEY_SECRET")


def file_hash(filepath, algo="md5"):
    h = hashlib.new(algo)
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def should_include_file(filepath):
    return filepath == "AchievementData.csv" or (filepath.startswith("Posters/") and filepath.lower().endswith(".jpg"))


def generate_manifest(root_dir):
    manifest = {
        "version": datetime.now().strftime("%Y%m%d-%H%M%S"),
        "files": {}
    }

    for root, _, files in os.walk(root_dir):
        for filename in files:
            filepath = os.path.join(root, filename)
            relpath = os.path.relpath(filepath, root_dir).replace("\\", "/")
            if should_include_file(relpath):
                manifest["files"][relpath] = {
                    "hash": file_hash(filepath, "md5"),
                    "size": os.path.getsize(filepath)
                }
    return manifest


def load_old_manifest():
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def get_changed_files(old_manifest, new_manifest):
    changed = []
    if not old_manifest:
        return list(new_manifest["files"].keys())  # 全量上传
    for path, info in new_manifest["files"].items():
        if path not in old_manifest["files"] or old_manifest["files"][path]["hash"] != info["hash"]:
            changed.append(path)
    return changed


def upload_to_oss(files):
    if not files:
        print("⚠️ 没有文件需要上传到 OSS")
        return
    for f in files:
        local_path = os.path.join(ROOT_DIR, f)
        oss_path = f"oss://{OSS_BUCKET}/{f}"
        cmd = [
            "ossutil",
            "cp",
            local_path,
            oss_path,
            "-f",
            "-e", OSS_ENDPOINT,
            "-i", OSS_ACCESS_KEY_ID,
            "-k", OSS_ACCESS_KEY_SECRET
        ]
        subprocess.run(cmd, check=True)
        print(f"✅ 已上传 {f} 到 OSS")


if __name__ == "__main__":
    new_manifest = generate_manifest(ROOT_DIR)
    old_manifest = load_old_manifest()
    changed_files = get_changed_files(old_manifest, new_manifest)

    if changed_files:
        # 保存最新 manifest.json
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(new_manifest, f, indent=2, ensure_ascii=False)

        # 把 manifest.json 本身也加入上传列表
        changed_files.append("manifest.json")
        upload_to_oss(changed_files)

        print(f"✅ manifest.json 已更新并上传，共 {len(changed_files)} 个文件变化")
    else:
        print("⚠️ 没有文件变化，跳过上传")

