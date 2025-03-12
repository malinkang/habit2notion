import os
from habit2notion.notion_helper import NotionHelper
import subprocess 
import json
import habit2notion.utils as utils
import uuid
import shutil
import hashlib
def run_command(command):
    """执行命令行命令并返回结果"""
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        print(f"错误输出: {e.stderr}")
        return None


def get_file(dir):
    dir =f"./{dir}"
    if os.path.exists(dir) and os.path.isdir(dir):
        entries = os.listdir(dir)
        file_name = entries[0] if entries else None
        return file_name
    else:
        print("OUT_FOLDER does not exist.")
        return None


def update_heatmap(dir, block_id):
    image_file = get_file(dir)
    if image_file:
        image_url = f"https://raw.githubusercontent.com/{os.getenv('REPOSITORY')}/{os.getenv('REF').split('/')[-1]}/{dir}/{image_file}"
        heatmap_url = f"https://heatmap.malinkang.com/?image={image_url}"
        if block_id:
            notion_helper.update_heatmap(block_id=block_id, url=heatmap_url)

def main():
    habits = notion_helper.query_all(notion_helper.habit_database_id)
    for habit in habits:
        page_id = habit.get("id")
        notion_token = os.getenv("NOTION_TOKEN")
        title = utils.get_property_value(habit.get("properties").get("标题"))
        unit = utils.get_property_value(habit.get("properties").get("单位"))
        database_filter = f'{{"property": "习惯", "relation": {{"contains": "{page_id}"}}}}'
        command = f'github_heatmap notion --notion_token {notion_token} --database_id {notion_helper.habit_record_database_id} --database_filter \'{database_filter}\' --date_prop_name 日期 --value_prop_name 值 --unit {unit} --year 2025 --me {title} --without-type-name --background-color=#FFFFFF --track-color=#ACE7AE --special-color1=#69C16E --special-color2=#549F57 --dom-color=#EBEDF0 --text-color=#000000'
        run_command(command)
        # 创建以title命名的文件夹
        hash_object = hashlib.sha256(title.encode('utf-8'))
        hashed_name = hash_object.hexdigest()[:10]  # 使用前10个字符以减少长度
        title_dir = f"heatmap/{hashed_name}"
        # 如果目录存在则删除
        if os.path.exists(title_dir):
            shutil.rmtree(title_dir)
        os.makedirs(title_dir)
        # 将OUT_FOLDER中的notion.svg移动到title文件夹
        source_file = "OUT_FOLDER/notion.svg"
        if os.path.exists(source_file):
            destination_file = f"{title_dir}/{uuid.uuid4()}.svg"
            os.rename(source_file, destination_file)
            heatmap_block_id=notion_helper.search_heatmap(page_id)
            if heatmap_block_id:
                update_heatmap(title_dir, heatmap_block_id)
notion_helper = NotionHelper()
if __name__ == "__main__":
    # main()
    encoded_path = quote("https://raw.githubusercontent.com/malinkang/habit2notion/main/heatmap/阅读/da947494-4760-4a00-9f92-e9abad3ee85c.svg")
    print(encoded_path) 