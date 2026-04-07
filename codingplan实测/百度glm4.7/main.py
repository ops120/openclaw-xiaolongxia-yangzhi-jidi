#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Word 智能水印溯源系统 - 主入口

用法:
    python main.py              # 启动 GUI
    python main.py --cli        # 命令行模式
    python main.py --help       # 显示帮助
"""

import sys
import os
import argparse
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))


def run_gui():
    """启动 GUI 应用"""
    from src.ui.main_window import run_gui
    run_gui()


def run_cli():
    """命令行模式"""
    from src.core.watermark import DocxWatermarkTool
    from src.db.models import Database, KeyManager

    print("=" * 50)
    print("Word 智能水印溯源系统 v1.1.0 - 命令行模式")
    print("=" * 50)

    while True:
        print("\n请选择操作:")
        print("1. 嵌入水印")
        print("2. 分析水印")
        print("3. 管理密钥")
        print("0. 退出")

        choice = input("\n请输入选项 (0-3): ").strip()

        if choice == '0':
            print("再见！")
            break
        elif choice == '1':
            embed_watermark_cli()
        elif choice == '2':
            analyze_watermark_cli()
        elif choice == '3':
            manage_keys_cli()
        else:
            print("无效选项，请重新输入")


def embed_watermark_cli():
    """命令行嵌入水印"""
    from src.core.watermark import DocxWatermarkTool
    from src.db.models import Database, KeyManager

    print("\n--- 嵌入水印 ---")

    # 输入文件路径
    input_path = input("输入原始文档路径: ").strip().strip('"\'')
    if not os.path.exists(input_path):
        print("错误: 文件不存在")
        return

    # 输入用户信息
    user_info = input("输入用户标识 (如: 张三-工号123): ").strip()
    if not user_info:
        print("错误: 用户标识不能为空")
        return

    department = input("输入部门 (可选): ").strip()
    project = input("输入项目 (可选): ").strip()

    # 选择密钥
    db = Database()
    key_manager = KeyManager(db)
    keys = key_manager.get_all_keys()

    if not keys:
        print("没有可用密钥，正在创建默认密钥...")
        key_manager.create_key('默认密钥', 'default_password_2024')
        keys = key_manager.get_all_keys()

    print("\n可用密钥:")
    for i, key in enumerate(keys, 1):
        print(f"  {i}. {key['key_name']}")

    key_index = input("选择密钥编号 (默认1): ").strip()
    try:
        key_index = int(key_index) - 1 if key_index else 0
        selected_key = keys[key_index]
    except (ValueError, IndexError):
        print("错误: 无效选择")
        return

    # 获取密钥密码
    key = key_manager.get_key(selected_key['key_name'])
    if not key:
        print("错误: 无法获取密钥")
        return

    # 生成输出路径
    input_file = Path(input_path)
    output_dir = input_file.parent / 'watermarked'
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = input_file.stem
    output_path = output_dir / f'{timestamp}_watermarked.docx'

    # 嵌入水印
    print(f"\n正在嵌入水印...")
    tool = DocxWatermarkTool(password=key['password'])
    result = tool.embed_watermark(
        input_path, str(output_path),
        user_info, department, project
    )

    if result['success']:
        print(f"\n[成功] 水印嵌入完成!")
        print(f"  - 处理段落数: {result['paragraphs_processed']}")
        print(f"  - 备份层: {', '.join(result['backup_layers'])}")
        print(f"  - 输出文件: {output_path}")
    else:
        print(f"\n[失败] {result.get('error', '未知错误')}")


def analyze_watermark_cli():
    """命令行分析水印"""
    from src.core.watermark import DocxWatermarkTool
    from src.db.models import Database, KeyManager

    print("\n--- 分析水印 ---")

    # 输入文件路径
    input_path = input("输入待分析文档路径: ").strip().strip('"\'')
    if not os.path.exists(input_path):
        print("错误: 文件不存在")
        return

    # 选择密钥
    db = Database()
    key_manager = KeyManager(db)
    keys = key_manager.get_all_keys()

    if not keys:
        print("没有可用密钥，使用默认密钥...")
        password = None
    else:
        print("\n可用密钥:")
        for i, key in enumerate(keys, 1):
            print(f"  {i}. {key['key_name']}")

        key_index = input("选择密钥编号 (默认1，留空使用默认密钥): ").strip()
        if key_index:
            try:
                key_index = int(key_index) - 1
                key = key_manager.get_key(keys[key_index]['key_name'])
                password = key['password'] if key else None
            except (ValueError, IndexError):
                print("无效选择，使用默认密钥")
                password = None
        else:
            password = None

    # 分析水印
    print(f"\n正在分析文档...")
    tool = DocxWatermarkTool(password=password)
    result = tool.analyze_docx(input_path)

    print("\n" + "=" * 50)
    if result['success'] and result['has_watermark']:
        data = result['watermark_data']
        print("[发现水印]")
        print(f"  完整度: {result['integrity']}%")
        print(f"  来源: {result['source']}")
        print(f"  用户标识: {data.get('uid', '未知')}")
        print(f"  部门: {data.get('department', '-')}")
        print(f"  项目: {data.get('project', '-')}")
        print(f"  时间戳: {data.get('timestamp', '未知')}")
    else:
        print("[未发现水印]")
        print(f"  原因: {result.get('error', '未知')}")

    print("\n分析日志:")
    for log in result.get('log', []):
        print(f"  {log}")


def manage_keys_cli():
    """命令行管理密钥"""
    from src.db.models import Database, KeyManager

    db = Database()
    key_manager = KeyManager(db)

    while True:
        print("\n--- 密钥管理 ---")
        print("1. 查看所有密钥")
        print("2. 创建新密钥")
        print("3. 导出密钥")
        print("4. 导入密钥")
        print("5. 删除密钥")
        print("0. 返回")

        choice = input("\n请输入选项 (0-5): ").strip()

        if choice == '0':
            break
        elif choice == '1':
            keys = key_manager.get_all_keys()
            if keys:
                print("\n密钥列表:")
                for key in keys:
                    print(f"  - {key['key_name']} (创建于: {key['created_at']})")
            else:
                print("\n暂无密钥")
        elif choice == '2':
            name = input("输入密钥名称: ").strip()
            if not name:
                print("错误: 名称不能为空")
                continue
            password = input("输入密码: ").strip()
            if not password:
                print("错误: 密码不能为空")
                continue
            try:
                key_manager.create_key(name, password)
                print(f"[成功] 密钥 '{name}' 创建成功")
            except ValueError as e:
                print(f"[失败] {e}")
        elif choice == '3':
            keys = key_manager.get_all_keys()
            if not keys:
                print("暂无密钥")
                continue
            name = input("输入要导出的密钥名称: ").strip()
            json_data = key_manager.export_key(name)
            if json_data:
                output_path = f"{name}.json"
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(json_data)
                print(f"[成功] 密钥已导出到: {output_path}")
            else:
                print("[失败] 密钥不存在")
        elif choice == '4':
            path = input("输入密钥文件路径: ").strip().strip('"\'')
            if not os.path.exists(path):
                print("错误: 文件不存在")
                continue
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    json_data = f.read()
                key_manager.import_key(json_data)
                print("[成功] 密钥导入成功")
            except Exception as e:
                print(f"[失败] {e}")
        elif choice == '5':
            name = input("输入要删除的密钥名称: ").strip()
            confirm = input(f"确定删除密钥 '{name}'? (y/n): ").strip().lower()
            if confirm == 'y':
                if key_manager.delete_key(name):
                    print("[成功] 密钥已删除")
                else:
                    print("[失败] 密钥不存在")
            else:
                print("已取消")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Word 智能水印溯源系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
    python main.py              # 启动 GUI
    python main.py --cli        # 命令行模式
    python main.py --version    # 显示版本
        '''
    )

    parser.add_argument(
        '--cli',
        action='store_true',
        help='使用命令行模式'
    )

    parser.add_argument(
        '--version', '-v',
        action='version',
        version='Word 智能水印溯源系统 v1.1.0'
    )

    args = parser.parse_args()

    if args.cli:
        run_cli()
    else:
        run_gui()


if __name__ == '__main__':
    main()
