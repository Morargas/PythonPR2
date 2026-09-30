import schedule
import time
import logging
import argparse
import os

TASKS_FILE = "tasks.txt"

class Task:
    def __init__(self, task_id, operation, filename, content=None, line_num=None, schedule=None):
        self.task_id = task_id
        self.operation = operation
        self.filename = filename
        self.content = content
        self.line_num = line_num
        self.schedule = schedule

    def to_line(self):
        content = self.content if self.content is not None else ""
        line_num = str(self.line_num) if self.line_num is not None else ""
        sched = self.schedule if self.schedule is not None else ""
        return f"{self.task_id}|{self.operation}|{self.filename}|{content}|{line_num}|{sched}"

    @classmethod
    def from_line(cls, line):
        parts = line.rstrip("\n").split("|")
        while len(parts) < 6:
            parts.append("")
        task_id = int(parts[0])
        operation = parts[1]
        filename = parts[2]
        content = parts[3] if parts[3] != "" else None
        line_num = int(parts[4]) if parts[4] != "" else None
        sched = parts[5] if parts[5] != "" else None
        return cls(task_id, operation, filename, content, line_num, sched)

    def __repr__(self):
        return f"<Task id={self.task_id}, operation={self.operation}, schedule={self.schedule}>"


class SimpleScheduler:
    def __init__(self):
        self.tasks = []
        self.next_id = 1
        self.load_tasks()

    def load_tasks(self):
        if not os.path.exists(TASKS_FILE):
            return
        with open(TASKS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    task = Task.from_line(line)
                    self.tasks.append(task)
                except Exception as e:
                    print(f"Ошибка чтения строки: {line} -> {e}")
        if self.tasks:
            self.next_id = max(t.task_id for t in self.tasks) + 1

    def save_tasks(self):
        with open(TASKS_FILE, 'w', encoding='utf-8') as f:
            for task in self.tasks:
                f.write(task.to_line() + "\n")

    def add_task(self, operation, filename, content=None, line_num=None, schedule_time=None):
        task = Task(self.next_id, operation, filename, content, line_num, schedule_time)
        self.tasks.append(task)
        self.next_id += 1
        self.save_tasks()
        print(f"Added task: {task}")

    def schedule_all(self):
        schedule.clear()
        for task in self.tasks:
            if task.schedule and "daily" in task.schedule:
                try:
                    time_str = task.schedule.split(':', 1)[1]  # '10:00'
                    schedule.every().day.at(time_str).do(self.run_task, task)
                    print(f"Scheduled task {task.task_id} daily at {time_str}")
                except Exception as e:
                    print(f"Failed to schedule task {task.task_id}: {e}")

    def run_task(self, task):
        try:
            if task.operation == 'create':
                with open(task.filename, 'w', encoding='utf-8') as f:
                    if task.content:
                        f.write(task.content)
                self.log_task(task, "Success")
            elif task.operation == 'append':
                with open(task.filename, 'a', encoding='utf-8') as f:
                    f.write((task.content or '') + '\n')
                self.log_task(task, "Success")
            elif task.operation == 'delete_line':
                if not os.path.exists(task.filename):
                    self.log_task(task, "Failed - File not found")
                    return
                with open(task.filename, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                if task.line_num and task.line_num <= len(lines):
                    del lines[task.line_num - 1]
                    with open(task.filename, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    self.log_task(task, "Success")
                else:
                    self.log_task(task, "Failed - Line number out of range")
            else:
                print("Unknown operation")
        except Exception as e:
            self.log_task(task, f"Failed - {str(e)}")

    def log_task(self, task, status):
        logging.info(f"Task ID {task.task_id}: {task.operation} on {task.filename} - Status: {status}")

    def start(self):
        self.schedule_all()
        print("Scheduler started. Press Ctrl+C to stop.")
        while True:
            schedule.run_pending()
            time.sleep(1)


logging.basicConfig(
    filename="simple_scheduler.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)


def main():
    scheduler = SimpleScheduler()

    parser = argparse.ArgumentParser(description="Simple Text Scheduler")
    parser.add_argument("command", help="Command to execute (add, view, start, run)")
    parser.add_argument("--operation", help="Task operation (create, append, delete_line)")
    parser.add_argument("--filename", help="Filename to operate on")
    parser.add_argument("--content", help="Content to write or append to the file")
    parser.add_argument("--line_num", type=int, help="Line number to delete (for delete_line)")
    parser.add_argument("--schedule", help="Schedule time (e.g., 'daily:10:00')")
    parser.add_argument("--task_id", type=int, help="Task ID to run immediately")

    args = parser.parse_args()

    if args.command == "add":
        if args.operation and args.filename:
            scheduler.add_task(
                operation=args.operation,
                filename=args.filename,
                content=args.content,
                line_num=args.line_num,
                schedule_time=args.schedule,
            )
        else:
            print("Missing required arguments for adding a task")

    elif args.command == "view":
        print("Scheduled tasks:")
        for task in scheduler.tasks:
            print(task)

    elif args.command == "run":
        if args.task_id is None:
            print("Specify --task_id")
            return
        for task in scheduler.tasks:
            if task.task_id == args.task_id:
                scheduler.run_task(task)
                print(f"Task {task.task_id} executed.")
                break
        else:
            print(f"Task {args.task_id} not found")

    elif args.command == "start":
        scheduler.start()

    else:
        print("Unknown command")


if __name__ == "__main__":
    main()