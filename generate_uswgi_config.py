import os

template = """
[uwsgi]
master = 1
vacuum = true
socket = 127.0.0.1:8082
enable-threads = true
die-on-term = true
thunder-lock = true
threads = {threads}
processes = {processes}
virtualenv = {venv}
wsgi-file = {wsgi_file}
chdir = {project_dir}
uid = {user}
gid = {group}"""[1:]

project_dir = os.path.dirname(os.path.abspath(__file__))  # current dir
venv_path = os.path.join(project_dir, 'venv')
wsgi_file = os.path.join(project_dir, 'web.py')

cpu_count = os.cpu_count()
process_count = cpu_count

user = 'user2'
group = user

config = template.format(threads=cpu_count,
                         processes=process_count,
                         venv=venv_path,
                         wsgi_file=wsgi_file,
                         project_dir=project_dir,
                         user=user,
                         group=group)

with open('uwsgi.ini', 'w') as file:
    file.write(config)
