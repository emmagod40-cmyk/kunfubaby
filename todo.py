#!/usr/bin/env python3
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

DATA_FILE = Path.home() / ".todo_tasks.json"
DATE_FORMAT = "%Y-%m-%d"

# 改善3: Windows では ANSI カラーコードを無効化
if os.name == "nt":
    RED = DONE_COLOR = RESET = ""
else:
    RED = "\033[31m"
    DONE_COLOR = "\033[90m"
    RESET = "\033[0m"


def load_tasks():
    if not DATA_FILE.exists():
        return []
    # 改善1: 破損ファイルでクラッシュしないようにエラーハンドリング
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        err(f"データファイルの読み込みに失敗しました: {e}")
        err(f"ファイルを確認してください: {DATA_FILE}")
        sys.exit(1)


def save_tasks(tasks):
    # 改善2: 一時ファイル経由で書き込み（書き込み中クラッシュによるデータ破損を防ぐ）
    tmp = DATA_FILE.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(DATA_FILE)
    except OSError as e:
        err(f"データの保存に失敗しました: {e}")
        sys.exit(1)


# 改善4: エラーメッセージは標準エラー出力へ
def err(msg):
    print(msg, file=sys.stderr)


def parse_due(due_str):
    try:
        datetime.strptime(due_str, DATE_FORMAT)
        return due_str
    except ValueError:
        err(f"エラー: 期限は YYYY-MM-DD 形式で入力してください。（例: {date.today()}）")
        sys.exit(1)


def due_date(due_str):
    return datetime.strptime(due_str, DATE_FORMAT).date() if due_str else None


def format_due(due_str):
    if not due_str:
        return "期限なし"
    today = date.today()
    due = due_date(due_str)
    diff = (due - today).days
    if diff < 0:
        suffix = f"（{abs(diff)}日超過）"
    elif diff == 0:
        suffix = "（今日）"
    elif diff <= 3:
        suffix = f"（あと{diff}日）"
    else:
        suffix = ""
    return f"{due_str}{suffix}"


def is_overdue(due_str):
    d = due_date(due_str)
    return d is not None and d < date.today()


def is_due_today_or_overdue(due_str):
    d = due_date(due_str)
    return d is not None and d <= date.today()


def add_task(args):
    due = None
    if "--due" in args:
        idx = args.index("--due")
        if idx + 1 >= len(args):
            err("エラー: --due の後に日付を指定してください。")
            sys.exit(1)
        due = parse_due(args[idx + 1])
        title_parts = args[:idx] + args[idx + 2:]
    else:
        title_parts = args

    if not title_parts:
        err("エラー: タスク名を指定してください。")
        sys.exit(1)

    title = " ".join(title_parts)
    tasks = load_tasks()
    task_id = max((t["id"] for t in tasks), default=0) + 1
    # 改善5: done フィールドを初期値 False で追加
    tasks.append({"id": task_id, "title": title, "due": due, "done": False})
    save_tasks(tasks)

    due_label = f"  期限: {due}" if due else ""
    print(f"追加しました: [{task_id}] {title}{due_label}")


# 改善5: タスクを完了状態にするコマンド
def complete_task(task_id):
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            if t.get("done"):
                print(f"ID {task_id} はすでに完了済みです。")
                return
            t["done"] = True
            save_tasks(tasks)
            print(f"完了にしました: [{task_id}] {t['title']}")
            return
    err(f"ID {task_id} のタスクが見つかりません。")


def print_task(t):
    done = t.get("done", False)
    due_label = format_due(t.get("due"))
    status = "✓ " if done else "  "
    line = f"[{t['id']}] {status}{t['title']}  （{due_label}）"
    if done:
        print(f"{DONE_COLOR}{line}{RESET}")
    elif is_overdue(t.get("due")):
        print(f"{RED}{line}{RESET}")
    else:
        print(line)


def list_tasks():
    tasks = load_tasks()
    if not tasks:
        print("タスクはありません。")
        return
    for t in tasks:
        print_task(t)


def list_urgent_tasks():
    tasks = load_tasks()
    urgent = [t for t in tasks if not t.get("done") and is_due_today_or_overdue(t.get("due"))]
    if not urgent:
        print("今日までの期限のタスクはありません。")
        return
    print(f"今日までの期限のタスク（{len(urgent)}件）:")
    for t in urgent:
        print_task(t)


def delete_task(task_id):
    tasks = load_tasks()
    new_tasks = [t for t in tasks if t["id"] != task_id]
    if len(new_tasks) == len(tasks):
        err(f"ID {task_id} のタスクが見つかりません。")
        return
    save_tasks(new_tasks)
    print(f"削除しました: ID {task_id}")


def print_usage():
    today = date.today()
    print("使い方:")
    print(f"  python todo.py add <タスク名> [--due YYYY-MM-DD]   タスクを追加（例: --due {today}）")
    print("  python todo.py list                                  タスク一覧を表示")
    print("  python todo.py urgent                                今日までの期限のタスクを表示")
    print("  python todo.py done <ID>                             タスクを完了にする")
    print("  python todo.py delete <ID>                           タスクを削除")


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]

    if command == "add":
        if len(sys.argv) < 3:
            err("エラー: タスク名を指定してください。")
            sys.exit(1)
        add_task(sys.argv[2:])
    elif command == "list":
        list_tasks()
    elif command == "urgent":
        list_urgent_tasks()
    elif command == "done":
        if len(sys.argv) < 3:
            err("エラー: IDを指定してください。")
            sys.exit(1)
        try:
            complete_task(int(sys.argv[2]))
        except ValueError:
            err("エラー: IDは数値で指定してください。")
            sys.exit(1)
    elif command == "delete":
        if len(sys.argv) < 3:
            err("エラー: IDを指定してください。")
            sys.exit(1)
        try:
            delete_task(int(sys.argv[2]))
        except ValueError:
            err("エラー: IDは数値で指定してください。")
            sys.exit(1)
    else:
        err(f"不明なコマンド: {command}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
