"""
Word 智能水印溯源系统 - 主入口

支持 GUI 模式（默认）和 CLI 模式
"""

import sys
import argparse
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.core.watermark import DocxWatermarkTool
from src.db.models import Database, KeyManager


def cli_mode():
    """命令行模式"""
    parser = argparse.ArgumentParser(description='Word 智能水印溯源系统')
    subparsers = parser.add_subparsers(dest='command', help='命令')

    # 嵌入命令
    embed_parser = subparsers.add_parser('embed', help='嵌入水印')
    embed_parser.add_argument('-i', '--input', required=True, help='输入文件路径')
    embed_parser.add_argument('-o', '--output', required=True, help='输出文件路径')
    embed_parser.add_argument('-u', '--user', required=True, help='用户标识')
    embed_parser.add_argument('-d', '--department', default='', help='部门名称')
    embed_parser.add_argument('-p', '--project', default='', help='项目名称')
    embed_parser.add_argument('-k', '--key', default='默认密钥', help='密钥名称')
    embed_parser.add_argument('--password', default='docx_watermark_default_key_2024', help='密钥密码')

    # 分析命令
    analyze_parser = subparsers.add_parser('analyze', help='分析水印')
    analyze_parser.add_argument('-f', '--file', required=True, help='待分析文件路径')
    analyze_parser.add_argument('-k', '--key', default='默认密钥', help='密钥名称')
    analyze_parser.add_argument('--password', default='docx_watermark_default_key_2024', help='密钥密码')

    args = parser.parse_args()

    if args.command == 'embed':
        print(f'正在嵌入水印到 {args.input}...')
        tool = DocxWatermarkTool(args.password)
        result = tool.embed_watermark(
            args.input, args.output,
            args.user, args.department, args.project
        )

        if result['success']:
            print(f'[+] 成功在 {result["positions_processed"]} 个位置嵌入水印')
            print(f'[+] 备份层写入: {"是" if result["backup_written"] else "否"}')
            print(f'[+] 输出文件: {args.output}')
        else:
            print(f'[-] 嵌入失败: {result.get("error", "未知错误")}')
            sys.exit(1)

    elif args.command == 'analyze':
        print(f'正在分析 {args.file}...')
        tool = DocxWatermarkTool(args.password)
        result = tool.analyze_docx(args.file)

        if result['success']:
            data = result['watermark_data']
            print('[+] 分析成功！')
            print(f'[+] 提取来源: {result.get("extraction_source", "未知")}')
            print(f'[+] 水印完整度: {result["integrity"]}%')
            print(f'[+] 溯源信息: {data["uid"]}')
            if data.get('department'):
                print(f'[+] 部门: {data["department"]}')
            if data.get('project'):
                print(f'[+] 项目: {data["project"]}')
            print(f'[+] 时间戳: {data["timestamp"]}')
        else:
            print(f'[-] 分析失败: {result.get("error", "未知错误")}')
            sys.exit(1)

    else:
        parser.print_help()


def gui_mode():
    """图形界面模式"""
    from src.ui.main_window import main as gui_main
    gui_main()


if __name__ == '__main__':
    # 检查是否有命令行参数
    if len(sys.argv) > 1:
        cli_mode()
    else:
        gui_mode()
