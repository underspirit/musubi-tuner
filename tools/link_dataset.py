#!/usr/bin/env python3
"""
根据JSONL文件中的name字段，并行查找文件并创建软链接
"""

import json
import os
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Set
import logging
from tqdm import tqdm

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_names_from_jsonl(jsonl_file: str) -> Set[str]:
    """从JSONL文件中读取所有name字段"""
    names = set()
    try:
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if 'video_path' in data and data['video_path']:
                        name = Path(data['video_path']).name.split('.mp4')[0]
                        names.add(name)
                except json.JSONDecodeError as e:
                    logger.warning(f"第{line_num}行JSON解析错误: {e}")
                    continue
    except FileNotFoundError:
        logger.error(f"JSONL文件不存在: {jsonl_file}")
        raise
    except Exception as e:
        logger.error(f"读取JSONL文件时发生错误: {e}")
        raise

    logger.info(f"从JSONL文件中读取到 {len(names)} 个唯一的name字段")
    return names


def find_files_containing_names(file_dict, names: Set[str]) -> List[Path]:
    """在输入目录中查找包含指定name的所有文件"""
    found_files = []

    # 遍历
    for name in names:
        if name in file_dict:
            found_files.extend(file_dict[name])

    logger.info(f"找到 {len(found_files)} 个匹配的文件")
    return found_files


def create_symlink(src_file: Path, output_dir: Path) -> tuple:
    """创建单个软链接"""
    try:
        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)

        # 目标链接路径
        dst_link = output_dir / src_file.name

        # 如果目标链接已存在，先删除
        if dst_link.exists() or dst_link.is_symlink():
            dst_link.unlink()

        # 创建软链接
        dst_link.symlink_to(src_file.absolute())

        return True, f"成功创建软链接: {src_file.name}"

    except Exception as e:
        return False, f"创建软链接失败 {src_file.name}: {str(e)}"


def create_symlinks_parallel(files: List[Path], output_dir: str, max_workers: int = 4):
    """并行创建软链接"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    success_count = 0
    failed_count = 0

    logger.info(f"开始并行创建软链接，使用 {max_workers} 个线程")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_file = {
            executor.submit(create_symlink, file_path, output_path): file_path
            for file_path in files
        }

        # 使用tqdm显示进度条
        with tqdm(total=len(files), desc="创建软链接") as pbar:
            for future in as_completed(future_to_file):
                success, message = future.result()
                if success:
                    success_count += 1
                    logger.debug(message)
                else:
                    failed_count += 1
                    logger.error(message)
                pbar.update(1)

    logger.info(f"软链接创建完成: 成功 {success_count}, 失败 {failed_count}")


def main():
    parser = argparse.ArgumentParser(description="根据JSONL文件批量创建文件软链接")
    parser.add_argument("--jsonl_file", help="包含name字段的JSONL文件路径")
    parser.add_argument("--cache_type", type=str, required=True, choices=['vae', 'text'], help="需要link的cache 类型")
    parser.add_argument("--file_list", help="文件路径列表")
    parser.add_argument("--output_dir", help="软链接目标目录")
    parser.add_argument("-j", "--jobs", type=int, default=4,
                       help="并行线程数 (默认: 4)")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="显示详细日志")

    args = parser.parse_args()

    logger.info(f"link 数据类型: {args.cache_type}")
    if args.cache_type == "vae":
        split_text = "_00000"
    elif args.cache_type == "text":
        split_text = "_fp_te"

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # 读取JSONL文件中的name字段
        logger.info("步骤1: 读取JSONL文件")
        names = read_names_from_jsonl(args.jsonl_file)

        if not names:
            logger.warning("未找到任何name字段，退出程序")
            return
        else:
            logger.info(f"jsonl 样本数: {len(names)}, key样例: {list(names)[0]}")

        # 查找匹配的文件
        logger.info("步骤2: 查找匹配的文件")
        file_dict = {}
        with open(args.file_list) as f:
            for line in f:
                path = Path(line.strip())
                name = path.name.split(split_text)[0]
                if name in file_dict:
                    file_dict[name].append(path)
                else:
                    file_dict[name] = [path]
        logger.info(f"file_dict 大小: {len(file_dict)}, key样例: {list(file_dict.keys())[0]}")
        for i in file_dict:
            if len(file_dict[i]) > 5:
                logger.warning(f"存在重复: {i}")

        matching_files = find_files_containing_names(file_dict, names)

        if not matching_files:
            logger.warning("未找到任何匹配的文件，退出程序")
            return

        # 并行创建软链接
        logger.info("步骤3: 创建软链接")
        create_symlinks_parallel(matching_files, args.output_dir, args.jobs)

        logger.info("程序执行完成!")

    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
        raise


if __name__ == "__main__":
    main()
