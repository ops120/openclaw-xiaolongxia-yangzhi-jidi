"""
Word智能水印溯源系统 - 主入口
支持GUI和CLI两种模式
"""

import sys
import argparse
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))


def run_gui():
    """运行GUI模式"""
    try:
        from src.ui.main_window import main
        main()
    except Exception as e:
        print(f"GUI启动失败: {e}")
        print("请确保已安装所有依赖: pip install -r requirements.txt")
        sys.exit(1)


def run_cli(args):
    """运行CLI模式"""
    from src.core.watermark import DocxWatermarkTool, DEFAULT_PASSWORD
    from src.db.models import KeyManager

    # 嵌入水印
    if args.command == 'embed':
        print(f"正在为文档 {args.input} 嵌入水印...")

        # 获取密钥
        key_manager = KeyManager()
        if args.key:
            key_data = key_manager.get_key(args.key)
            if not key_data:
                print(f"错误: 找不到密钥 '{args.key}'")
                sys.exit(1)
            password = key_data['password']
            salt = key_data['salt']
        else:
            password = DEFAULT_PASSWORD
            salt = None

        # 创建工具
        tool = DocxWatermarkTool(master_password=password, salt=salt)

        # 嵌入水印
        result = tool.embed_watermark(
            args.input,
            args.output,
            args.user_info,
            args.department or '',
            args.project or ''
        )

        if result['success']:
            print(f"✓ 水印嵌入成功！")
            print(f"  - 处理段落数: {result['paragraphs_processed']}")
            print(f"  - 备份层数: {len(result['backup_written'])}")
            print(f"  - 输出文件: {args.output}")
        else:
            print(f"✗ 水印嵌入失败: {result.get('error', '未知错误')}")
            sys.exit(1)

    # 分析水印
    elif args.command == 'analyze':
        print(f"正在分析文档 {args.input}...")

        # 获取密钥
        key_manager = KeyManager()
        if args.key:
            key_data = key_manager.get_key(args.key)
            if not key_data:
                print(f"错误: 找不到密钥 '{args.key}'")
                sys.exit(1)
            password = key_data['password']
            salt = key_data['salt']
        else:
            password = DEFAULT_PASSWORD
            salt = None

        # 创建工具
        tool = DocxWatermarkTool(master_password=password, salt=salt)

        # 分析水印
        result = tool.analyze_docx(args.input)

        if result['success'] and result['has_watermark']:
            print(f"✓ 水印提取成功！")
            print(f"  - 完整度: {result['integrity']}%")
            print(f"  - 提取来源: {result.get('extracted_from', '未知')}")

            if result['watermark_data']:
                data = result['watermark_data']
                print(f"\n溯源信息:")
                print(f"  - 用户标识: {data.get('uid', '未知')}")
                print(f"  - 部门: {data.get('department', '未知')}")
                print(f"  - 项目: {data.get('project', '未知')}")
                print(f"  - 时间戳: {data.get('timestamp', '未知')}")
        else:
            print(f"✗ 水印提取失败: {result.get('error', '未发现水印')}")
            sys.exit(1)

    # 密钥管理
    elif args.command == 'key':
        key_manager = KeyManager()

        # 列出所有密钥
        if args.key_action == 'list':
            keys = key_manager.list_keys()
            if keys:
                print("现有密钥:")
                for key in keys:
                    print(f"  - {key['key_name']} (创建时间: {key['created_at']})")
            else:
                print("没有密钥")

        # 新建密钥
        elif args.key_action == 'create':
            if not args.key_name or not args.password:
                print("错误: 新建密钥需要指定 --name 和 --password")
                sys.exit(1)

            success = key_manager.create_key(args.key_name, args.password)
            if success:
                print(f"✓ 密钥 '{args.key_name}' 创建成功")
            else:
                print(f"✗ 密钥创建失败")
                sys.exit(1)

        # 导出密钥
        elif args.key_action == 'export':
            output = args.output or 'keys_backup.json'
            success = key_manager.export_keys(output)
            if success:
                print(f"✓ 密钥已导出到: {output}")
            else:
                print(f"✗ 密钥导出失败")
                sys.exit(1)

        # 导入密钥
        elif args.key_action == 'import':
            if not args.import_file:
                print("错误: 导入密钥需要指定 --import-file")
                sys.exit(1)

            success = key_manager.import_keys(args.import_file)
            if success:
                print(f"✓ 密钥导入成功")
            else:
                print(f"✗ 密钥导入失败")
                sys.exit(1)

        # 删除密钥
        elif args.key_action == 'delete':
            if not args.key_name:
                print("错误: 删除密钥需要指定 --name")
                sys.exit(1)

            success = key_manager.delete_key(args.key_name)
            if success:
                print(f"✓ 密钥 '{args.key_name}' 已删除")
            else:
                print(f"✗ 密钥删除失败")
                sys.exit(1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Word智能水印溯源系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # GUI模式（默认）
  python main.py

  # CLI模式 - 嵌入水印
  python main.py embed document.docx -o output.docx -u "张三-123"

  # CLI模式 - 分析水印
  python main.py analyze watermarked.docx

  # CLI模式 - 密钥管理
  python main.py key list
  python main.py key create --name mykey --password mypassword
        '''
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 嵌入命令
    embed_parser = subparsers.add_parser('embed', help='嵌入水印')
    embed_parser.add_argument('input', help='输入文档路径')
    embed_parser.add_argument('-o', '--output', required=True, help='输出文档路径')
    embed_parser.add_argument('-u', '--user-info', required=True, help='用户信息（如：张三-123）')
    embed_parser.add_argument('-d', '--department', help='部门名称')
    embed_parser.add_argument('-p', '--project', help='项目名称')
    embed_parser.add_argument('-k', '--key', help='使用的密钥名称（默认使用默认密钥）')

    # 分析命令
    analyze_parser = subparsers.add_parser('analyze', help='分析水印')
    analyze_parser.add_argument('input', help='输入文档路径')
    analyze_parser.add_argument('-k', '--key', help='使用的密钥名称（默认使用默认密钥）')

    # 密钥管理命令
    key_parser = subparsers.add_parser('key', help='密钥管理')
    key_subparsers = key_parser.add_subparsers(dest='key_action', help='密钥操作')

    # 列出密钥
    key_subparsers.add_parser('list', help='列出所有密钥')

    # 创建密钥
    create_parser = key_subparsers.add_parser('create', help='创建新密钥')
    create_parser.add_argument('--name', required=True, dest='key_name', help='密钥名称')
    create_parser.add_argument('--password', required=True, help='密钥密码')

    # 导出密钥
    export_parser = key_subparsers.add_parser('export', help='导出密钥')
    export_parser.add_argument('-o', '--output', help='输出文件路径（默认: keys_backup.json）')

    # 导入密钥
    import_parser = key_subparsers.add_parser('import', help='导入密钥')
    import_parser.add_argument('-f', '--file', required=True, dest='import_file', help='密钥文件路径')

    # 删除密钥
    delete_parser = key_subparsers.add_parser('delete', help='删除密钥')
    delete_parser.add_argument('--name', required=True, dest='key_name', help='密钥名称')

    args = parser.parse_args()

    # 如果没有指定命令，运行GUI
    if not args.command:
        run_gui()
    else:
        run_cli(args)


if __name__ == '__main__':
    main()
