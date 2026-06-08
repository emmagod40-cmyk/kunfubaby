#!/usr/bin/env python3
import json
import sys
from pathlib import Path

DATA_FILE = Path.home() / ".todo_tasks.json"


def load_tasks():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text())
    return []


def save_tasks(tasks):
    DATA_FILE.write_text(json.dumps(tasks, ensure_ascii=False, indent=2))


def add_task(title):
    tasks = load_tasks()
    task_id = max((t["id"] for t in tasks), default=0) + 1
    tasks.append({"id": task_id, "title": title})
    save_tasks(tasks)
    print(f"追加しました: [{task_id}] {title}")


def list_tasks():
    tasks = load_tasks()
    if not tasks:
        print("タスクはありません。")
        return
    for t in tasks:
        print(f"[{t['id']}] {t['title']}")


def delete_task(task_id):
    tasks = load_tasks()
    new_tasks = [t for t in tasks if t["id"] != task_id]
    if len(new_tasks) == len(tasks):
        print(f"ID {task_id} のタスクが見つかりません。")
        return
    save_tasks(new_tasks)
    print(f"削除しました: ID {task_id}")


def print_usage():
    print("使い方:")
    print("  python todo.py add <タスク名>   タスクを追加")
    print("  python todo.py list             タスク一覧を表示")
    print("  python todo.py delete <ID>      タスクを削除")


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]

    if command == "add":
        if len(sys.argv) < 3:
            print("エラー: タスク名を指定してください。")
            sys.exit(1)
        add_task(" ".join(sys.argv[2:]))
    elif command == "list":
        list_tasks()
    elif command == "delete":
        if len(sys.argv) < 3:
            print("エラー: IDを指定してください。")
            sys.exit(1)
        try:
            delete_task(int(sys.argv[2]))
        except ValueError:
            print("エラー: IDは数値で指定してください。")
            sys.exit(1)
    else:
        print(f"不明なコマンド: {command}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
