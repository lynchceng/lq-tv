import requests
import os

def filter_m3u_playlist():
    # 读取需要保留的频道组
    with open('filter/KulaoGroupsConfig.txt', 'r', encoding='utf-8') as f:
       saveChannelGroups = [line.strip() for line in f if line.strip()]
    
    # 从URL获取M3U播放列表(过滤裤佬中不需要的频道)
    url = 'https://gh-proxy.org/https://raw.githubusercontent.com/Jsnzkpg/Jsnzkpg/Jsnzkpg/Jsnzkpg1.m3u'
    response = requests.get(url, timeout=30)
    response.encoding = 'utf-8'
    m3u_content = response.text
    
    # 解析并过滤M3U内容
    lines = m3u_content.split('\n')
    filterResultContent = []
    saveCurrentChannel = False
    
    for line in lines:
        # 处理EXTM3U头部
        if line.startswith('#EXTM3U'):
            filterResultContent.append(line)
            continue
        
        # 处理EXTINF行
        if line.startswith('#EXTINF:'):
            # 提取group-title
            channelGroup = None
            if 'group-title=' in line:
                start = line.find('group-title=') + len('group-title=')
                end = line.find('"', start + 1)
                if end != -1:
                    channelGroup = line[start:end].strip('"')
            
            # 检查是否在saveChannelGroups中
            if channelGroup in saveChannelGroups:
                saveCurrentChannel = True
                filterResultContent.append(line)
            else:
                saveCurrentChannel = False
        else:
            # 处理URL行
            if saveCurrentChannel and line.strip():
                filterResultContent.append(line)
    
    # ========== 新增：自动创建 output 目录 ==========
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)  # 不存在就创建
    # ==============================================
    
    # 保存过滤后的内容
    with open('output/kulaoResult.m3u', 'w', encoding='utf-8') as f:
        f.write('\n'.join(filterResultContent))
    
    print(f'过滤完成！共保留 {len([l for l in filterResultContent if l.startswith("http")])} 个频道')

if __name__ == '__main__':
    filter_m3u_playlist()
