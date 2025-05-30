import os
import sys
from pathlib import Path

def find_all_files(input_dir, output_file="file_paths.txt"):
    """
    遍历指定目录，找到所有文件并将其绝对路径保存到txt文件中

    参数:
    input_dir: 输入目录路径
    output_file: 输出txt文件名，默认为 "file_paths.txt"
    """

    # 检查输入目录是否存在
    if not os.path.exists(input_dir):
        print(f"错误: 目录 '{input_dir}' 不存在")
        return False

    if not os.path.isdir(input_dir):
        print(f"错误: '{input_dir}' 不是一个目录")
        return False

    # 收集所有文件的绝对路径
    file_paths = []

    try:
        # 使用os.walk遍历目录及其子目录
        for root, dirs, files in os.walk(input_dir):
            for file in files:
                # 获取文件的绝对路径
                file_path = os.path.abspath(os.path.join(root, file))
                file_paths.append(file_path)

        # 将路径写入txt文件
        with open(output_file, 'w', encoding='utf-8') as f:
            for path in sorted(file_paths):  # 排序以便更好地组织
                f.write(path + '\n')

        print(f"成功找到 {len(file_paths)} 个文件")
        print(f"文件路径已保存到: {os.path.abspath(output_file)}")
        return True

    except Exception as e:
        print(f"处理过程中出现错误: {e}")
        return False

def main():
    """主函数"""
    # 可以通过命令行参数指定目录，或者直接在代码中设置
    if len(sys.argv) > 1:
        input_dir = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else "file_paths.txt"
    else:
        # 在这里设置你的输入目录
        input_dir = input("请输入要扫描的目录路径: ").strip()
        if not input_dir:
            print("未提供目录路径，程序退出")
            return

        output_file = input("请输入输出文件名(直接回车使用默认名称 'file_paths.txt'): ").strip()
        if not output_file:
            output_file = "file_paths.txt"

    # 执行文件查找
    success = find_all_files(input_dir, output_file)

    if success:
        print("任务完成!")
    else:
        print("任务失败!")

if __name__ == "__main__":
    main()
