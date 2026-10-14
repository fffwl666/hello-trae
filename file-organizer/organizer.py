"""按文件后缀整理目录：把文件分类移动到 图片/文档/压缩包/视频/音频/其他 子文件夹。

用法：
    python organizer.py                      # 只预览，不实际移动
    python organizer.py --dry-run            # 同上，显式预览
    python organizer.py --run                # 真正执行移动
    python organizer.py --target D:\\test    # 整理指定目录（默认 ~/Downloads）
"""

import argparse
import shutil
from pathlib import Path

# 分类规则：子文件夹名 -> 后缀集合（后缀统一小写比较）
CATEGORIES = {
    "图片": {".jpg", ".png", ".gif", ".webp"},
    "文档": {".pdf", ".docx", ".txt", ".xlsx", ".pptx"},
    "压缩包": {".zip", ".rar", ".7z", ".tar", ".gz"},
    "视频": {".mp4", ".mkv", ".avi", ".mov"},
    "音频": {".mp3", ".wav", ".flac"},
}
DEFAULT_CATEGORY = "其他"


def get_category(path):
    """根据文件后缀返回所属分类文件夹名。"""
    suffix = path.suffix.lower()
    for category, suffixes in CATEGORIES.items():
        if suffix in suffixes:
            return category
    return DEFAULT_CATEGORY


def unique_path(dest_dir, filename):
    """目标已存在时追加 _1、_2... 后缀，返回不冲突的路径。"""
    dest = dest_dir / filename
    if not dest.exists():
        return dest
    stem, suffix = dest.stem, dest.suffix
    counter = 1
    while True:
        dest = dest_dir / f"{stem}_{counter}{suffix}"
        if not dest.exists():
            return dest
        counter += 1


def organize(target, run):
    """整理 target 目录；run=True 真正移动，否则只预览。返回 (整理数, 跳过数)。"""
    moved = skipped = 0
    for item in sorted(target.iterdir()):
        if not item.is_file():
            skipped += 1  # 跳过子文件夹
            continue
        category = get_category(item)
        dest_dir = target / category
        dest = unique_path(dest_dir, item.name)
        print(f"将 {item.name} 移动到 {category}/{dest.name if dest.name != item.name else ''}".rstrip())
        if run:
            dest_dir.mkdir(exist_ok=True)  # 目标文件夹不存在就创建
            shutil.move(str(item), str(dest))
        moved += 1
    return moved, skipped


def main():
    parser = argparse.ArgumentParser(description="按后缀整理目录中的文件")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--run", action="store_true", help="真正执行移动")
    mode.add_argument("--dry-run", action="store_true", help="只预览（默认行为）")
    parser.add_argument(
        "--target",
        default=str(Path.home() / "Downloads"),
        help="要整理的目录路径（默认 ~/Downloads）",
    )
    args = parser.parse_args()

    target = Path(args.target).expanduser()
    if not target.is_dir():
        parser.error(f"目录不存在：{target}")

    moved, skipped = organize(target, run=args.run)
    action = "已整理" if args.run else "待整理"
    print(f"\n{action} {moved} 个文件，跳过 {skipped} 个")
    if not args.run:
        print("（预览模式，加 --run 才会真正移动）")


if __name__ == "__main__":
    main()
