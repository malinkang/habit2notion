#!/usr/bin/python
# -*- coding: UTF-8 -*-
import argparse
import json
import os
import time

import pendulum
from habit2notion.notion_helper import NotionHelper
import requests
from habit2notion import utils
import random
from dotenv import load_dotenv
from bson import ObjectId

load_dotenv()

habit_icon_dict = {
    "habit_exercising": "https://www.notion.so/icons/gym_gray.svg",
    "habit_drink_water": "https://www.notion.so/icons/drink_gray.svg",
}


headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "hl": "zh_CN",
    "origin": "https://dida365.com",
    "priority": "u=1, i",
    "referer": "https://dida365.com/",
    "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "traceid": "6721a893b8de3a0431a1548c",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "x-csrftoken": "GpesKselqEa9oKJQRM3bj8tkdT2kJVNSNaZ9eM0i3Q-1730258339",
    "x-device": '{"platform":"web","os":"macOS 10.15.7","device":"Chrome 130.0.0.0","name":"","version":6101,"id":"6721a59761bd871d7ba24b96","channel":"website","campaign":"","websocket":"6721a7eab8de3a0431a153ae"}',
    "x-tz": "Asia/Shanghai",
}


def is_habit_modified(habit_dict, item):
    id = item.get("id")
    modified_time = utils.parse_date(item.get("modifiedTime"))
    habit = habit_dict.get(id)
    if habit:
        last_modified_time = utils.get_property_value(
            habit.get("properties").get("最后修改时间")
        )
        if last_modified_time == modified_time:
            return False
    return True


def is_habit_records_modified(habit_record_dict, item):
    id = item.get("id")
    modified_time = utils.parse_date(item.get("opTime"))
    habit_record = habit_record_dict.get(id)
    if habit_record:
        last_modified_time = utils.get_property_value(
            habit_record.get("properties").get("最后修改时间")
        )
        if last_modified_time == modified_time:
            return False
    return True


def get_habits(session):
    url = "https://api.dida365.com/api/v2/habits"
    r = session.get(
        url=url,
        headers=headers,
    )
    if r.ok:
        return r.json()


def get_habit_records(session, habit_id):
    """习惯记录"""
    data = {
        "habitIds": [habit_id],
        "afterStamp": 20240320,
    }
    r = session.post(
        "https://api.dida365.com/api/v2/habitCheckins/query", headers=headers, json=data
    )
    if r.ok:
        records = r.json().get("checkins").get(habit_id)
        with open("records.json", "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=4)
        return records


def insert_habit_records(session, habit_dict, habit_record_dict, habit_id):
    d = notion_helper.get_property_type(notion_helper.habit_record_database_id)
    items = get_habit_records(session, habit_id)
    if items:
        items = list(
            filter(
                lambda item: is_habit_records_modified(
                    habit_record_dict, item), items
            )
        )
        for index, item in enumerate(items):
            print(f"一共{len(items)}个，当前是第{index+1}个")
            id = item.get("id")
            habit_id = item.get("habitId")
            habit_name = utils.get_property_value(
                habit_dict.get(habit_id).get("properties").get("标题")
            )
            habit_re_id = habit_dict.get(habit_id).get("id")
            habit = {
                "标题": habit_name,
                "id": id,
                "最后修改时间": utils.parse_date(item.get("opTime")),
                "日期": utils.parse_date(str(item.get("checkinStamp"))),
                "值": item.get("value"),
                "习惯": [habit_re_id],
            }
            parent = {
                "database_id": notion_helper.habit_record_database_id,
                "type": "database_id",
            }
            if item.get("checkinTime"):
                habit["完成时间"] = utils.parse_date(item.get("checkinTime"))
            parent = {
                "database_id": notion_helper.habit_record_database_id,
                "type": "database_id",
            }
            icon = habit_dict.get(habit_id).get("icon")
            properties = utils.get_properties(habit, d)
            if id in habit_record_dict:
                notion_helper.update_page(
                    page_id=habit_record_dict.get(id).get("id"),
                    properties=properties
                )
            else:
                properties = utils.get_properties(habit, d)
                notion_helper.create_page(
                    parent=parent, properties=properties, icon=icon
                )


def insert_habits(habit_dict, habits):
    d = notion_helper.get_property_type(notion_helper.habit_database_id)
    if habits:
        items = list(
            filter(lambda item: is_habit_modified(habit_dict, item), habits))
        for index, item in enumerate(items):
            print(f"一共{len(items)}个，当前是第{index+1}个")
            id = item.get("id")
            habit = {
                "标题": item.get("name"),
                "id": id,
                "最后修改时间": utils.parse_date(item.get("modifiedTime")),
                "单位": item.get("unit"),
                "目标": item.get("goal"),
                "目标天数": item.get("targetDays"),
                "提示语": item.get("encouragement"),
            }
            parent = {
                "database_id": notion_helper.habit_database_id,
                "type": "database_id",
            }
            icon = habit_icon_dict.get(item.get("iconRes"))
            if icon is None:
                icon = "https://www.notion.so/icons/alarm_clock_gray.svg"
            if id in habit_dict:
                properties = utils.get_properties(habit, d)
                notion_helper.update_page(
                    page_id=habit_dict.get(id).get("id"),
                    properties=properties
                )
            else:
                habit["状态"] = random.choice(["★", "✔︎", "♥︎"])
                habit["颜色"] = random.choice(["Red", "Green", "Blue"])
                properties = utils.get_properties(habit, d)
                result = notion_helper.create_page(
                    parent=parent,
                    properties=properties,
                    icon=utils.get_icon(icon),
                )
                block_id = result.get("id")
                notion_helper.append_blocks(
                    block_id=block_id,
                    children=[utils.get_embed()],
                )
                habit_dict[id] = result


def login(username, password):
    session = requests.Session()
    login_url = "https://api.dida365.com/api/v2/user/signon?wc=true&remember=true"
    payload = {"username": username, "password": password}
    response = session.post(login_url, json=payload, headers=headers)

    if response.status_code == 200:
        print("登录成功")
        return session
    else:
        print(f"登录失败，状态码: {response.status_code}")
        return None


def habit_check(session, habit_id, record_id, date, value, goal):
    is_add = False
    if not record_id:
        is_add = True
        record_id = str(ObjectId())
    data = {
        "add": [],
        "update": [],
        "delete": [],
    }
    item = {
        "checkinStamp": date,
        "checkinTime": pendulum.now().format("YYYY-MM-DDTHH:mm:ss.000+0000"),
        "opTime": pendulum.now().format("YYYY-MM-DDTHH:mm:ss.000+0000"),
        "goal": goal,
        "habitId": habit_id,
        "id": record_id,
        "status": 0 if (value < goal) else 2,
        "value": value,
    }
    if is_add:
        data["add"].append(item)
    else:
        data["update"].append(item)
    response = session.post(
        "https://api.dida365.com/api/v2/habitCheckins/batch", headers=headers, json=data
    )
    if response.ok:
        return record_id
    


def get_modified_time(record):
    return utils.get_property_value(record.get("properties").get("最后修改时间"))


def get_id(item):
    return utils.get_property_value(item.get("properties").get("id"))


def insert_to_dida(session, habit_record_dict2, habit_dict2):
    for habit,item in habit_record_dict2.items():
        for date, records in item.items():
            dida_records = [record for record in records if utils.get_property_value(
                record.get("properties").get("id"))]
            notion_records = [record for record in records if not utils.get_property_value(
                record.get("properties").get("id"))]
            dida_records.sort(
                key=lambda record: get_modified_time(record), reverse=True)
            notion_records.sort(
                key=lambda record: get_modified_time(record), reverse=True)
            if dida_records and notion_records:
                if get_modified_time(notion_records[0]) > get_modified_time(dida_records[0]):
                    # 更新，更新成功后更新notion数据库
                    date_str = pendulum.from_timestamp(date).format("YYYYMMDD")
                    habit_page_id = [x.get("id") for x in utils.get_property_value(
                        notion_records[0].get("properties").get("习惯"))][0]
                    habit_id = habit_dict2[habit_page_id]
                    record_id = get_id(dida_records[0])
                    value = utils.get_property_value(
                        notion_records[0].get("properties").get("值"))
                    goal = utils.get_property_value(
                        notion_records[0].get("properties").get("目标"))
                    habit_check(session, habit_id, record_id,
                                date_str, value, goal)
                    notion_helper.update_page(dida_records[0].get("id"), properties={"值": {"number": value}})
            elif notion_records:
                # 插入到滴答清单，并更新数据库，
                date_str = pendulum.from_timestamp(date).format("YYYYMMDD")
                habit_page_id = [x.get("id") for x in utils.get_property_value(
                    notion_records[0].get("properties").get("习惯"))][0]
                habit_id = habit_dict2[habit_page_id]
                value = utils.get_property_value(
                    notion_records[0].get("properties").get("值"))
                goal = utils.get_property_value(
                    notion_records[0].get("properties").get("目标"))
                record_id = habit_check(session, habit_id, None, date_str, value, goal)
                if record_id:
                    notion_helper.update_page(notion_records[0].get("id"), properties={"id": utils.get_rich_text(record_id)})
                notion_records.remove(notion_records[0])
            # 将当前页面从notion_records中移除
        for record in notion_records:
            notion_helper.delete_block(record.get("id"))

def main():
    config = notion_helper.config
    username = config.get("滴答清单账号")
    password = config.get("滴答清单密码")
    session = login(username, password)
    habits = notion_helper.query_all(notion_helper.habit_database_id)
    habit_dict = {}
    habit_dict2 = {}
    for habit in habits:
        habit_dict[utils.get_property_value(
            habit.get("properties").get("id"))] = habit
        habit_dict2[habit.get("id")] = utils.get_property_value(
            habit.get("properties").get("id"))
    habits = get_habits(session)
    insert_habits(habit_dict, habits)
    habit_records = notion_helper.query_all(
        notion_helper.habit_record_database_id)
    habit_record_dict = {}
    habit_record_dict2 = {}
    for record in habit_records:
        record_id = utils.get_property_value(
            record.get("properties").get("id"))
        if record_id:
            habit_record_dict[record_id] = record
        date = utils.get_property_value(record.get("properties").get("日期"))
        habit_relation_id = [x.get("id") for x in utils.get_property_value(
                    record.get("properties").get("习惯"))][0]
        if habit_relation_id not in habit_record_dict2:
            habit_record_dict2[habit_relation_id] = {date:[]}
        habit_record_dict2[habit_relation_id][date].append(record)

    for habit in habits:
        insert_habit_records(session, habit_dict, habit_record_dict, habit.get("id"))
    insert_to_dida(session, habit_record_dict2, habit_dict2)



notion_helper = NotionHelper()
if __name__ == "__main__":
    main()
