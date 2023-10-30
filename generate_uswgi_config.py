import os

template = """
[uwsgi]
master = 1
vacuum = true
socket = 0.0.0.0:8082
enable-threads = true
die-on-term = true
thunder-lock = true
threads = {threads}
processes = {processes}
wsgi-file = {wsgi_file}
need-app = true
chdir = {project_dir}"""[1:]

project_dir = os.path.dirname(os.path.abspath(__file__))  # current dir
wsgi_file = os.path.join(project_dir, 'web.py')

cpu_count = os.cpu_count()
process_count = cpu_count

config = template.format(threads=cpu_count,
                         processes=process_count,
                         wsgi_file=wsgi_file,
                         project_dir=project_dir)

with open('/tmp/uwsgi.ini', 'w') as file:
    file.write(config)
