import schedule
import time
import subprocess # 用于执行其他 Python 脚本
import sys
import os

# 获取 Python 解释器的路径 (建议用绝对路径)
python_executable = sys.executable
rootPath = '/Users/mini4chaos/Developer/weibo-crawler/'
# 定义要执行的脚本的绝对路径
script1_path = os.path.abspath(rootPath+"weibo2memos.py")
script2_path = os.path.abspath(rootPath+"resources_bind.py")
script3_path = os.path.abspath(rootPath+"memo_relation.py")

script4_path = os.path.abspath(rootPath+"retweet_user.py")
script5_path = os.path.abspath(rootPath+"update_tags.py")

def run_script(script_path):
    """执行指定的 Python 脚本"""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Running script: {script_path}")
    try:
        # 使用 subprocess.run 来执行脚本，并捕获输出
        # cwd 参数设置脚本的工作目录，有助于处理相对路径
        script_dir = os.path.dirname(script_path)
        result = subprocess.run(
            [python_executable, script_path],
            capture_output=True,
            text=True,
            check=True, # 如果脚本出错（返回非零退出码），则抛出 CalledProcessError
            cwd=script_dir # 设置工作目录为脚本所在目录
        )
        print(f"Output of {os.path.basename(script_path)}:\n{result.stdout}")
        if result.stderr:
            print(f"Error output of {os.path.basename(script_path)}:\n{result.stderr}", file=sys.stderr)
    except FileNotFoundError:
        print(f"Error: Python executable or script not found at {script_path}", file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Error running script {script_path}. Return code: {e.returncode}", file=sys.stderr)
        print(f"Stdout:\n{e.stdout}", file=sys.stderr)
        print(f"Stderr:\n{e.stderr}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred while running {script_path}: {e}", file=sys.stderr)

# --- 定义你的调度任务 ---
# 每天 10:30 执行 script1.py
# schedule.every().day.at("10:30").do(run_script, script_path=script1_path)

# 每周一 下午 1:00 执行 script2.py
# schedule.every().monday.at("13:00").do(run_script, script_path=script2_path)

# 每小时的 30 分、35 分、40 分分别执行 script1.py、script2.py、script3.py
schedule.every().hour.at(":30").do(run_script, script_path=script1_path)
schedule.every().hour.at(":35").do(run_script, script_path=script2_path)
schedule.every().hour.at(":40").do(run_script, script_path=script3_path)

schedule.every(12).hours.at(":45").do(run_script, script_path=script4_path)
schedule.every(12).hours.at(":50").do(run_script, script_path=script5_path)

# 也可以设置更复杂的间隔
# schedule.every(5).to(10).minutes.do(job)
# schedule.every().wednesday.at("13:15").do(job)

print("Scheduler started. Press Ctrl+C to exit.")

# --- 运行调度循环 ---
while True:
    schedule.run_pending() # 检查是否有任务需要运行
    time.sleep(1)       # 等待 1 秒，避免 CPU 空转