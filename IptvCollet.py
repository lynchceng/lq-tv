import re
import requests
import os
from datetime import datetime

def load_alias_map():
    """加载频道别名映射"""
    alias_map = {}
    try:
        with open('config/alias.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split(',')
                main_name = parts[0].strip()
                aliases = [alias.strip() for alias in parts[1:]]
                for alias in aliases:
                    if alias.startswith('re:'):
                        pattern = alias[3:]
                        alias_map[pattern] = (main_name, True)  # True表示是正则表达式
                    else:
                        alias_map[alias] = (main_name, False)
    except FileNotFoundError:
        pass
    return alias_map

def load_channels():
    """加载最终要保存的频道和频道组"""
    channels = {}
    current_genre = None
    
    # 直接打印当前工作目录
    print(f"当前工作目录: {os.getcwd()}")
    
    # 检查channels.txt文件是否存在
    file_path = 'config/channels.txt'
    print(f"检查文件是否存在: {file_path}")
    print(f"文件存在: {os.path.exists(file_path)}")
    
    try:
        print("尝试打开channels.txt文件")
        with open(file_path, 'r', encoding='utf-8') as f:
            print("成功打开channels.txt文件")
            # 读取所有内容
            content = f.read()
            print(f"文件内容长度: {len(content)}")
            print("文件内容前500字符:")
            print(content[:500])
            
            # 重新读取并解析
            f.seek(0)
            line_count = 0
            for line in f:
                line_count += 1
                line = line.strip()
                print(f"第{line_count}行: {line}")
                if not line:
                    continue
                if '#genre#' in line:
                    current_genre = line.replace('#genre#', '').strip().rstrip(',')
                    print(f"找到频道组: {current_genre}")
                    channels[current_genre] = []
                else:
                    if current_genre:
                        channels[current_genre].append(line.strip())
                        print(f"添加频道: {line.strip()} 到频道组: {current_genre}")
        print(f"加载完成，共 {len(channels)} 个频道组")
    except Exception as e:
        print(f"加载channels.txt失败: {type(e).__name__}: {e}")
    return channels

def load_channel_icon():
    """加载频道logo规则"""
    try:
        with open('config/channel_icon.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    return line.strip()
    except FileNotFoundError:
        pass
    return ''

def load_subscribe_sources():
    """加载订阅源"""
    sources = []
    with open('config/subscribe.txt', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('file:'):
                path = line[5:].strip()
                sources.append(('file', path))
            elif line.startswith('url:'):
                url = line[4:].strip()
                sources.append(('url', url))
    return sources

def get_channel_name(alias_map, channel_name):
    """根据别名映射获取标准频道名称"""
    # 直接匹配
    if channel_name in alias_map:
        main_name, is_regex = alias_map[channel_name]
        if not is_regex:
            return main_name
    
    # 正则表达式匹配
    for pattern, (main_name, is_regex) in alias_map.items():
        if is_regex:
            try:
                if re.match(pattern, channel_name):
                    return main_name
            except:
                pass
    
    return channel_name

def parse_m3u_content(content):
    """解析m3u格式的内容"""
    channels = []
    lines = content.split('\n')
    current_info = {}
    
    for line in lines:
        line = line.strip()
        if line.startswith('#EXTINF:'):
            # 提取频道信息
            info = {}
            # 提取频道组
            if 'group-title=' in line:
                start = line.find('group-title=') + len('group-title=')
                end = line.find('"', start + 1)
                if end != -1:
                    info['group'] = line[start:end].strip('"')
            # 提取频道名称
            comma_index = line.rfind(',')
            if comma_index != -1:
                info['name'] = line[comma_index + 1:].strip()
            # 提取tvg-name
            if 'tvg-name=' in line:
                start = line.find('tvg-name=') + len('tvg-name=')
                end = line.find('"', start + 1)
                if end != -1:
                    info['tvg_name'] = line[start:end].strip('"')
            # 提取tvg-logo
            if 'tvg-logo=' in line:
                start = line.find('tvg-logo=') + len('tvg-logo=')
                end = line.find('"', start + 1)
                if end != -1:
                    info['tvg_logo'] = line[start:end].strip('"')
            current_info = info
        elif line and not line.startswith('#'):
            # 提取URL
            if current_info:
                current_info['url'] = line
                channels.append(current_info.copy())
                current_info = {}
    
    return channels

def parse_txt_content(content):
    """解析txt格式的内容"""
    channels = []
    lines = content.split('\n')
    current_group = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if '#genre#' in line:
            current_group = line.replace('#genre#', '').strip()
        else:
            parts = line.split(',', 1)
            if len(parts) == 2:
                name = parts[0].strip()
                url = parts[1].strip()
                channels.append({'name': name, 'url': url, 'group': current_group})
    
    return channels

def load_source_content(source_type, source):
    """加载订阅源内容"""
    if source_type == 'file':
        if os.path.exists(source):
            with open(source, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        else:
            print(f"文件不存在: {source}")
            return ''
    elif source_type == 'url':
        try:
            response = requests.get(source, timeout=30)
            response.encoding = 'utf-8'
            return response.text
        except Exception as e:
            print(f"获取URL内容失败: {source}, 错误: {e}")
            return ''
    return ''

def main():
    # 加载配置
    alias_map = load_alias_map()
    channels_config = load_channels()
    channel_icon_base = load_channel_icon()
    sources = load_subscribe_sources()
    
    # 构建频道到频道组的映射，同时记录每个频道组中频道的顺序
    channel_to_genre = {}  # 频道到频道组列表的映射
    genre_channel_order = {}
    for genre, channels in channels_config.items():
        genre_channel_order[genre] = channels
        for channel in channels:
            if channel not in channel_to_genre:
                channel_to_genre[channel] = []
            channel_to_genre[channel].append(genre)
    
    # 打印频道配置信息
    print("频道配置信息:")
    print(f"总共配置了 {len(channel_to_genre)} 个频道")
    print(f"频道组数量: {len(channels_config)}")
    
    # 收集所有频道数据
    all_channels = []
    
    for source_type, source in sources:
        content = load_source_content(source_type, source)
        if not content:
            continue
        
        # 根据文件类型解析
        if source.endswith('.m3u') or source.endswith('.m3u8'):
            channels = parse_m3u_content(content)
        else:
            channels = parse_txt_content(content)
        
        print(f"\n从 {source} 解析到 {len(channels)} 个频道")
        # 打印前5个解析到的频道
        for i, channel in enumerate(channels[:5]):
            name = channel.get('name', '') or channel.get('tvg_name', '')
            print(f"  {name}")
        if len(channels) > 5:
            print(f"  ... 等{len(channels) - 5}个频道")
        all_channels.extend(channels)
    
    print(f"\n总共解析到 {len(all_channels)} 个频道")
    
    # 处理频道数据
    processed_channels = {}
    
    for channel in all_channels:
        name = channel.get('name', '') or channel.get('tvg_name', '')
        if not name:
            continue
        
        # 获取标准频道名称
        standard_name = get_channel_name(alias_map, name)
        
        # 检查是否在配置的频道列表中
        if standard_name in channel_to_genre:
            genres = channel_to_genre[standard_name]
            # 去重：同一频道组下同一URL不重复
            url = channel.get('url', '')
            if url:
                for genre in genres:
                    key = f"{genre}-{standard_name}-{url}"
                    if key not in processed_channels:
                        processed_channels[key] = {
                            'name': standard_name,
                            'url': url,
                            'genre': genre,
                            'logo': channel_icon_base + standard_name + '.png' if channel_icon_base else ''
                        }
                        print(f"添加频道: {standard_name} (频道组: {genre})")
        else:
            # 检查频道所属的组是否在channels.txt中定义
            channel_group = channel.get('group', '')
            # 尝试匹配频道组名称（忽略emoji等特殊字符）
            matched_genre = None
            for genre in channels_config:
                # 去除emoji和特殊字符后比较
                clean_genre = ''.join([c for c in genre if c.isalnum() or c in '-_ 中文'])
                clean_channel_group = ''.join([c for c in channel_group if c.isalnum() or c in '-_ 中文'])
                if clean_genre == clean_channel_group:
                    matched_genre = genre
                    break
            if matched_genre:
                # 去重：同一频道组下同一URL不重复
                url = channel.get('url', '')
                if url:
                    key = f"{matched_genre}-{standard_name}-{url}"
                    if key not in processed_channels:
                        processed_channels[key] = {
                            'name': standard_name,
                            'url': url,
                            'genre': matched_genre,
                            'logo': channel_icon_base + standard_name + '.png' if channel_icon_base else ''
                        }
                        print(f"添加频道: {standard_name} (频道组: {matched_genre}, 动态频道)")
            else:
                print(f"跳过频道: {name} (标准名称: {standard_name})")
    
    # 生成m3u文件
    # 获取当前日期，格式为 YYYY.M.D（月份和日期不带前导零）
    now = datetime.now()
    current_date = f'{now.year}.{now.month}.{now.day}'
    update_time = f'更新时间{current_date}'
    
    # 添加固定头部内容
    output_lines = [
        '#EXTM3U x-tvg-url="https://gitee.com/gsls200808/xmltvepg/raw/master/e9.xml.gz"',
        f'#EXTINF:-1 group-title="洛奇TV" tvg-name="{update_time}" tvg-logo="https://gh-proxy.org/https://raw.githubusercontent.com/lynchceng/lq-tv/main/logo/洛奇TV.png" epg-url="https://gitee.com/gsls200808/xmltvepg/raw/master/e9.xml.gz",{update_time}',
        'http://xxxxxx.mp4'
    ]
    
    # 按照channels.txt中的顺序排序频道组
    genre_channels = {}
    for channel in processed_channels.values():
        genre = channel['genre']
        if genre not in genre_channels:
            genre_channels[genre] = []
        genre_channels[genre].append(channel)
    
    # 获取channels.txt中的频道组顺序
    channel_order = []
    with open('config/channels.txt', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if '#genre#' in line:
                genre = line.replace('#genre#', '').strip().rstrip(',')
                channel_order.append(genre)
    
    # 生成频道信息，按照channels.txt中的顺序
    for genre in channel_order:
        if genre in genre_channels:
            # 按照channels.txt中定义的顺序排序频道
            # 首先按照channels.txt中的顺序对频道名称排序
            channel_order_in_genre = genre_channel_order.get(genre, [])
            
            # 定义排序键函数
            def get_channel_order(channel_info):
                channel_name = channel_info['name']
                if channel_name in channel_order_in_genre:
                    return channel_order_in_genre.index(channel_name)
                return len(channel_order_in_genre)  # 不在列表中的频道放在最后
            
            # 排序频道
            sorted_channels = sorted(genre_channels[genre], key=get_channel_order)
            
            for channel in sorted_channels:
                logo = channel['logo']
                logo_attr = f' tvg-logo="{logo}"' if logo else ''
                output_lines.append(f"#EXTINF:-1 group-title=\"{genre}\" tvg-name=\"{channel['name']}\"{logo_attr},{channel['name']}")
                output_lines.append(channel['url'])
    
    # ========== 新增：自动创建 output 目录 ==========
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)  # 不存在就创建
    # ==============================================

    # 保存文件
    with open('output/result.m3u', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    
    print(f'\n生成完成！共包含 {len(processed_channels)} 个频道')

if __name__ == '__main__':
    main()
