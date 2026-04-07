"""
系统测试脚本
用于快速测试水印系统的基本功能
"""

import sys
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.core.watermark import DocxWatermarkTool, DEFAULT_PASSWORD


def test_crypto():
    """测试加密功能"""
    print("测试加密功能...")

    from src.core.crypto import CryptoManager

    # 测试密钥派生
    password = "test_password"
    salt = b"test_salt"
    key = CryptoManager.derive_key(password, salt)

    assert key is not None, "密钥派生失败"
    assert len(key) == 44, f"密钥长度错误: {len(key)}"

    # 测试加密器
    cipher = CryptoManager.get_cipher(key)
    assert cipher is not None, "加密器创建失败"

    print("✓ 加密功能测试通过")


def test_watermark_tool():
    """测试水印工具"""
    print("\n测试水印工具...")

    tool = DocxWatermarkTool(master_password=DEFAULT_PASSWORD)

    # 测试工具初始化
    assert tool.master_key is not None, "主密钥初始化失败"
    assert tool.cipher is not None, "加密器初始化失败"

    # 测试CRC计算
    data = "test_data"
    crc = tool._calculate_crc(data)
    assert len(crc) == 4, f"CRC长度错误: {len(crc)}"

    # 测试数据构建
    watermark_data = tool._build_watermark_data("张三-123", "销售部", "ProjectA")
    assert 'version' in watermark_data, "水印数据缺少version字段"
    assert 'uid' in watermark_data, "水印数据缺少uid字段"
    assert 'crc' in watermark_data, "水印数据缺少crc字段"

    # 测试零宽字符转换
    text = "test_message"
    zw_string = tool._text_to_zw_string(text)
    assert all(c in '\u200b\u200c' for c in zw_string), "零宽字符转换失败"

    # 测试零宽字符还原
    recovered_text = tool._zw_string_to_text(zw_string)
    assert recovered_text == text, f"零宽字符还原失败: {recovered_text}"

    print("✓ 水印工具测试通过")


def test_database():
    """测试数据库功能"""
    print("\n测试数据库功能...")

    from src.db.models import Database, KeyManager

    # 创建测试数据库
    test_db = Database('test_watermark.db')

    # 创建密钥管理器
    key_manager = KeyManager(test_db)

    # 测试创建密钥
    success = key_manager.create_key('test_key', 'test_password')
    assert success, "创建密钥失败"

    # 测试获取密钥
    key_data = key_manager.get_key('test_key')
    assert key_data is not None, "获取密钥失败"
    assert key_data['password'] == 'test_password', "密码不匹配"

    # 测试列出密钥
    keys = key_manager.list_keys()
    assert len(keys) > 0, "没有找到密钥"

    # 测试删除密钥
    success = key_manager.delete_key('test_key')
    assert success, "删除密钥失败"

    # 删除测试数据库
    Path('test_watermark.db').unlink()

    print("✓ 数据库功能测试通过")


def main():
    """主测试函数"""
    print("=" * 50)
    print("Word智能水印溯源系统 - 系统测试")
    print("=" * 50)

    try:
        test_crypto()
        test_watermark_tool()
        test_database()

        print("\n" + "=" * 50)
        print("所有测试通过！")
        print("=" * 50)

    except AssertionError as e:
        print(f"\n测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
