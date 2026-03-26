import requests
import os

def parse_rihou_playlist(url):
    """解析rihou.cc的播放列表"""
    try:
        # 获取内容
        response = requests.get(url, timeout=30)
        response.encoding = 'utf-8'
        content = response.text
        
        # 解析频道列表
        channels = []
        current_group = ""
        
        lines = content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if ',#genre#' in line:
                # 频道组
                current_group = line.replace(',#genre#', '').strip()
            else:
                # 频道
                parts = line.split(',', 1)
                if len(parts) == 2:
                    name = parts[0].strip()
                    url = parts[1].strip()
                    channels.append({'name': name, 'url': url, 'group': current_group})
        
        return channels
    except Exception as e:
        print(f"解析错误: {e}")
        return []

def generate_m3u(channels, output_file):
    """生成m3u格式的播放列表"""
    # 生成m3u内容
    output_lines = ['#EXTM3U']
    
    # 添加频道
    for channel in channels:
        group = channel.get('group', '')
        if group:
            output_lines.append(f'#EXTINF:-1 group-title="{group}",{channel["name"]}')
        else:
            output_lines.append(f'#EXTINF:-1,{channel["name"]}')
        output_lines.append(channel["url"])
    
    # 确保output目录存在
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 保存文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    
    print(f'生成完成！共包含 {len(channels)} 个频道')

def main():
    url = 'http://rihou.cc:555/gggg.nzk'
    output_file = 'output/rihou.m3u'
    
    # 解析播放列表
    channels = parse_rihou_playlist(url)
    
    if channels:
        # 生成m3u文件
        generate_m3u(channels, output_file)
    else:
        print("解析失败，没有获取到频道数据")

if __name__ == '__main__':
    main()
