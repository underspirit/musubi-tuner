#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import subprocess
import sys
from pathlib import Path
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

def check_ffmpeg():
    """检查系统是否安装了ffmpeg"""
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        return False

def get_video_info(video_path):
    """获取视频信息"""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json', 
            '-show_format', '-show_streams', video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            import json
            info = json.loads(result.stdout)
            for stream in info['streams']:
                if stream['codec_type'] == 'video':
                    bit_rate = stream.get('bit_rate')
                    if not bit_rate and 'format' in info:
                        # 如果视频流没有比特率信息，尝试从整体格式获取
                        total_bit_rate = info['format'].get('bit_rate')
                        if total_bit_rate:
                            bit_rate = str(int(int(total_bit_rate) * 0.9))  # 估算视频比特率为总比特率的90%
                    
                    return {
                        'width': stream.get('width'),
                        'height': stream.get('height'),
                        'codec': stream.get('codec_name'),
                        'duration': float(stream.get('duration', 0)),
                        'bit_rate': bit_rate
                    }
    except Exception as e:
        print(f"获取视频信息失败: {e}")
    return None

def resize_video(input_path, output_path, target_width, target_height, quality='original', original_bitrate=None):
    """调整视频分辨率"""
    
    # 质量设置
    quality_settings = {
        'high': ['-crf', '18'],
        'medium': ['-crf', '23'], 
        'low': ['-crf', '28'],
        'original': [],  # 保持原有质量
        'keep_bitrate': []  # 保持原有比特率
    }
    
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-vf', f'scale={target_width}:{target_height}',
        '-c:v', 'libx264',  # 保持H.264编码
        '-c:a', 'copy',     # 音频直接复制，不重新编码
        '-movflags', '+faststart',  # 优化网络播放
        '-y'  # 覆盖输出文件
    ]
    
    # 添加质量设置
    if quality == 'keep_bitrate' and original_bitrate:
        # 强制使用原始比特率
        bitrate_mbps = f"{int(int(original_bitrate) / 1000)}k"
        cmd.extend(['-b:v', bitrate_mbps])
        thread_id = threading.current_thread().name
        print(f"[{thread_id}] 保持比特率: {bitrate_mbps} - {os.path.basename(input_path)}")
    else:
        quality_params = quality_settings.get(quality, quality_settings['original'])
        if quality_params:  # 只有在非original模式下才添加CRF参数
            cmd.extend(quality_params)
    
    cmd.append(output_path)
    
    try:
        thread_id = threading.current_thread().name
        print(f"[{thread_id}] 开始处理: {os.path.basename(input_path)}")
        start_time = time.time()
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"[{thread_id}] ✅ 完成: {os.path.basename(output_path)} (耗时: {duration:.1f}s)")
            return True, input_path, duration
        else:
            print(f"[{thread_id}] ❌ 失败: {os.path.basename(input_path)}")
            print(f"[{thread_id}] 错误信息: {result.stderr}")
            return False, input_path, duration
            
    except Exception as e:
        print(f"[{threading.current_thread().name}] ❌ 处理异常: {input_path}, 错误: {e}")
        return False, input_path, 0

def process_single_video(args):
    """处理单个视频的包装函数"""
    video_file, output_path, width, height, quality = args
    
    # 获取原始视频信息
    info = get_video_info(str(video_file))
    original_bitrate = None
    if info:
        original_bitrate = info.get('bit_rate')
        bitrate_info = f", 比特率: {int(original_bitrate)/1000:.0f}kbps" if original_bitrate else ""
        thread_id = threading.current_thread().name
        print(f"[{thread_id}] 原分辨率: {info['width']}x{info['height']}{bitrate_info} - {video_file.name}")
    
    # 输出文件路径
    output_file = output_path / f"{video_file.name}"
    
    # 处理视频
    return resize_video(str(video_file), str(output_file), width, height, quality, original_bitrate)

def batch_resize_videos(mp4_files, output_dir, width, height, quality='original', max_workers=2):
    """批量处理视频"""
    
    output_path = Path(output_dir)
    
    # 创建输出目录
    output_path.mkdir(parents=True, exist_ok=True)
    
    if not mp4_files:
        print("在指定目录中没有找到MP4文件")
        return
    
    print(f"找到 {len(mp4_files)} 个MP4文件")
    print(f"目标分辨率: {width}x{height}")
    print(f"质量设置: {quality}")
    print(f"并行处理数: {max_workers}")
    print("-" * 50)
    
    success_count = 0
    total_time = 0
    start_time = time.time()
    
    # 准备任务参数
    tasks = [(video_file, output_path, width, height, quality) for video_file in mp4_files]
    
    # 使用线程池执行并行处理
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="Worker") as executor:
        # 提交所有任务
        future_to_video = {executor.submit(process_single_video, task): task[0] for task in tasks}
        
        # 处理完成的任务
        for future in as_completed(future_to_video):
            video_file = future_to_video[future]
            try:
                success, processed_file, duration = future.result()
                if success:
                    success_count += 1
                total_time += duration
            except Exception as exc:
                print(f"视频 {video_file.name} 处理时发生异常: {exc}")
    
    end_time = time.time()
    total_elapsed = end_time - start_time
    
    print(f"\n{'='*50}")
    print(f"批量处理完成！")
    print(f"成功: {success_count}/{len(mp4_files)}")
    print(f"总耗时: {total_elapsed:.1f}秒")
    print(f"平均每个视频: {total_elapsed/len(mp4_files):.1f}秒")
    if max_workers > 1:
        efficiency = (total_time / total_elapsed) if total_elapsed > 0 else 0
        print(f"并行效率: {efficiency:.1f}x (理论最大: {max_workers}x)")

def main():
    parser = argparse.ArgumentParser(description='批量调整MP4视频分辨率')
    parser.add_argument('input_jsonl', help='输入视频文件夹路径')
    parser.add_argument('output_dir', help='输出视频文件夹路径')
    parser.add_argument('width', type=int, help='目标宽度')
    parser.add_argument('height', type=int, help='目标高度')
    parser.add_argument('--quality', choices=['high', 'medium', 'low', 'original', 'keep_bitrate'], 
                       default='original', help='视频质量 (默认: original，保持原有质量)')
    parser.add_argument('--workers', '-w', type=int, default=2, 
                       help='并行处理线程数 (默认: 2, 建议不超过CPU核心数)')
    parser.add_argument('--show-bitrate', action='store_true', 
                       help='显示原始和输出视频的比特率对比')
    
    # 如果没有参数，显示使用说明
    if len(sys.argv) == 1:
        print("MP4视频批量分辨率调整工具")
        print("=" * 40)
        print("\n使用方法:")
        print("python video_resizer.py <输入文件夹> <输出文件夹> <宽度> <高度> [选项]")
        print("\n基本用法:")
        print("python video_resizer.py ./input ./output 1920 1080")
        print("python video_resizer.py ./videos ./resized 1280 720 --quality keep_bitrate --workers 4")
        print("\n选项:")
        print("--quality: 质量模式 (original/keep_bitrate/high/medium/low, 默认: original)")
        print("--workers: 并行线程数 (默认: 2)")
        print("\n质量选项说明:")
        print("- original: 让ffmpeg自动调整质量（可能降低比特率）")
        print("- keep_bitrate: 强制保持原始比特率")
        print("- high/medium/low: 使用CRF重新编码")
        print("\n并行处理说明:")
        print("- 默认使用2个线程并行处理")
        print("- 建议不超过CPU核心数，避免系统过载")
        print("- 单个视频处理时会占用大量CPU和内存")
        print("\n注意:")
        print("- 需要安装ffmpeg")
        print("- 并行处理会增加系统负载")
        print("- 输出文件名会添加'resized_'前缀")
        return
    
    args = parser.parse_args()
    
    # 检查ffmpeg
    if not check_ffmpeg():
        print("❌ 错误: 未找到ffmpeg，请先安装ffmpeg")
        print("安装方法:")
        print("- Windows: 下载ffmpeg并添加到PATH")
        print("- macOS: brew install ffmpeg")
        print("- Ubuntu: sudo apt install ffmpeg")
        return
    
    # 检查输入目录
    if not os.path.exists(args.input_jsonl):
        print(f"❌ 错误: 输入目录不存在: {args.input_jsonl}")
        return
    mp4_files = []
    with open(args.input_jsonl) as f:
        for line in f:
            data = json.loads(line)
            mp4_files.append(Path(data['video_path']))
        print(f"总视频数量: {len(mp4_files)}")
    
    # 执行批量处理
    batch_resize_videos(mp4_files, args.output_dir, 
                       args.width, args.height, args.quality, args.workers)

if __name__ == "__main__":
    main()