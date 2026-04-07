#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Word智能水印溯源系统 - 主入口文件

这是一个用于 Word 文档水印嵌入和溯源的工具，支持：
- 为文档嵌入唯一标识水印
- 从文档中提取水印信息进行溯源
- 多层冗余备份策略，增强鲁棒性
- 图形化界面，操作简便
"""
import sys
import argparse
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.db.models import Database
from src.utils.config import config
from src.utils.logger import logger


def init_system():
    """初始化系统"""
    try:
        # 初始化数据库
        Database.initialize()

        # 创建必要的目录
        config.output_dir.mkdir(parents=True, exist_ok=True)
        config.log_dir.mkdir(parents=True, exist_ok=True)
        config.backup_dir.mkdir(parents=True, exist_ok=True)

        logger.info("系统初始化成功")
        return True
    except Exception as e:
        print(f"系统初始化失败: {e}")
        return False


def run_gui():
    """运行图形界面"""
    try:
        from src.ui.main_window import main
        main()
    except ImportError as e:
        print(f"导入GUI模块失败: {e}")
        print("请确保已安装所有依赖包: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.exception("GUI启动失败")
        print(f"GUI启动失败: {e}")
        sys.exit(1)


def run_cli_embed(args):
    """命令行模式 - 嵌入水印"""
    try:
        from src.core.watermark import WatermarkEngine
        from src.db.models import Database

        # 验证输入
        if not Path(args.input).exists():
            print(f"错误: 输入文件不存在: {args.input}")
            return 1

        # 获取密钥
        key_data = Database.get_key(args.key)
        if not key_data:
            print(f"错误: 密钥不存在: {args.key}")
            return 1

        # 创建水印引擎
        engine = WatermarkEngine(password=key_data['password'], salt=key_data['salt'])

        # 确定输出路径
        input_file = Path(args.input)
        if args.output:
            output_path = args.output
        else:
            output_dir = input_file.parent / "watermarked"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"{input_file.stem}_watermarked{input_file.suffix}")

        # 嵌入水印
        print(f"正在嵌入水印...")
        print(f"  输入文件: {args.input}")
        print(f"  输出文件: {output_path}")
        print(f"  用户信息: {args.user}")
        print(f"  部门: {args.department or 'N/A'}")
        print(f"  项目: {args.project or 'N/A'}")

        result = engine.embed_watermark(
            args.input,
            output_path,
            args.user,
            args.department or '',
            args.project or ''
        )

        if result['success']:
            print(f"\\n成功! 在 {result['paragraphs_processed']} 个位置嵌入水印")
            print(f"备份层: {', '.join(result['backup_written'])}")

            # 记录到数据库
            Database.add_trace_log(
                uid=args.user,
                user_info=args.user,
                department=args.department or '',
                project=args.project or '',
                original_filename=input_file.name
            )

            return 0
        else:
            print(f"\\n失败: {result['error']}")
            return 1

    except Exception as e:
        print(f"错误: {e}")
        return 1


def run_cli_analyze(args):
    """命令行模式 - 分析水印"""
    try:
        from src.core.watermark import WatermarkEngine
        from src.db.models import Database
        import json

        # 验证输入
        if not Path(args.file).exists():
            print(f"错误: 文件不存在: {args.file}")
            return 1

        # 获取密钥
        key_data = Database.get_key(args.key)
        if not key_data:
            print(f"错误: 密钥不存在: {args.key}")
            return 1

        # 创建水印引擎
        engine = WatermarkEngine(password=key_data['password'], salt=key_data['salt'])

        # 分析水印
        print(f"正在分析水印...")
        print(f"  文件: {args.file}")
        print(f"  密钥: {args.key}")

        result = engine.extract_watermark(args.file)

        if result['success'] and result['has_watermark']:
            print(f"\\n发现水印!")
            print(f"  完整度: {result['integrity']}%")
            print(f"  数据源: {result['source']}")

            data = result['watermark_data']
            print(f"\\n溯源信息:")
            print(f"  用户标识: {data.get('uid', 'N/A')}")
            print(f"  部门: {data.get('department', 'N/A')}")
            print(f"  项目: {data.get('project', 'N/A')}")
            print(f"  时间戳: {data.get('timestamp', 'N/A')}")

            if args.json:
                print(f"\\nJSON 输出:")
                print(json.dumps(data, ensure_ascii=False, indent=2))

            return 0
        else:
            print(f"\\n未发现水印: {result.get('error', '未知错误')}")
            return 1

    except Exception as e:
        print(f"错误: {e}")
        return 1


def run_cli_key(args):
    """命令行模式 - 密钥管理"""
    try:
        from src.db.models import Database, KeyManager

        if args.list:
            # 列出所有密钥
            keys = Database.list_keys()
            if keys:
                print("现有密钥:")
                for key in keys:
                    print(f"  - {key['key_name']} (ID: {key['id']}, 创建于: {key['created_at']})")
            else:
                print("暂无密钥")

        elif args.create:
            # 创建新密钥
            if KeyManager.create_new_key(args.create, args.password):
                print(f"成功创建密钥: {args.create}")
            else:
                print(f"创建密钥失败: {args.create}")

        elif args.delete:
            # 删除密钥
            if Database.delete_key(args.delete):
                print(f"成功删除密钥: {args.delete}")
            else:
                print(f"删除密钥失败: {args.delete}")

        elif args.export:
            # 导出密钥
            export_path = Path(args.export)
            if export_path.is_dir():
                files = KeyManager.export_all_keys(str(export_path))
                print(f"成功导出 {len(files)} 个密钥到: {export_path}")
            else:
                key_name = Path(args.export).stem
                if Database.export_key(key_name, str(export_path)):
                    print(f"成功导出密钥到: {export_path}")
                else:
                    print(f"导出密钥失败: {args.export}")

        elif args.import_key:
            # 导入密钥
            if Database.import_key(args.import_key):
                print(f"成功导入密钥: {args.import_key}")
            else:
                print(f"导入密钥失败: {args.import_key}")

        else:
            print("请指定操作: --list, --create, --delete, --export, --import")

        return 0

    except Exception as e:
        print(f"错误: {e}")
        return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Word智能水印溯源系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # GUI 模式 (默认)
  python main.py

  # CLI 模式 - 嵌入水印
  python main.py embed -i document.docx -u "张三-123" -d "销售部" -p "Project_Alpha" -k default

  # CLI 模式 - 分析水印
  python main.py analyze -f document_watermarked.docx -k default

  # CLI 模式 - 密钥管理
  python main.py key --list
  python main.py key --create mykey
  python main.py key --export ./keys
        '''
    )

    parser.add_argument('--version', action='version', version=f'{config.app_name} v{config.version}')

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # GUI 子命令 (默认)
    gui_parser = subparsers.add_parser('gui', help='启动图形界面 (默认)')

    # Embed 子命令
    embed_parser = subparsers.add_parser('embed', help='嵌入水印')
    embed_parser.add_argument('-i', '--input', required=True, help='输入文档路径')
    embed_parser.add_argument('-o', '--output', help='输出文档路径 (默认: watermarked/)')
    embed_parser.add_argument('-u', '--user', required=True, help='用户标识信息')
    embed_parser.add_argument('-d', '--department', help='部门名称')
    embed_parser.add_argument('-p', '--project', help='项目名称')
    embed_parser.add_argument('-k', '--key', default='default', help='密钥名称 (默认: default)')

    # Analyze 子命令
    analyze_parser = subparsers.add_parser('analyze', help='分析水印')
    analyze_parser.add_argument('-f', '--file', required=True, help='待分析文档路径')
    analyze_parser.add_argument('-k', '--key', default='default', help='密钥名称 (默认: default)')
    analyze_parser.add_argument('--json', action='store_true', help='以JSON格式输出结果')

    # Key 子命令
    key_parser = subparsers.add_parser('key', help='密钥管理')
    key_parser.add_argument('--list', action='store_true', help='列出所有密钥')
    key_parser.add_argument('--create', metavar='NAME', help='创建新密钥')
    key_parser.add_argument('--delete', metavar='NAME', help='删除密钥')
    key_parser.add_argument('--export', metavar='PATH', help='导出密钥 (文件或目录)')
    key_parser.add_argument('--import-key', metavar='PATH', help='导入密钥')
    key_parser.add_argument('--password', metavar='PASSWORD', help='密钥密码 (创建时使用)')

    args = parser.parse_args()

    # 初始化系统
    if not init_system():
        sys.exit(1)

    # 如果没有指定命令，默认运行 GUI
    if args.command is None or args.command == 'gui':
        run_gui()
    elif args.command == 'embed':
        sys.exit(run_cli_embed(args))
    elif args.command == 'analyze':
        sys.exit(run_cli_analyze(args))
    elif args.command == 'key':
        sys.exit(run_cli_key(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()