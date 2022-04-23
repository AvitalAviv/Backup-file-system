import os
import socket
import sys
import time
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

IP = 0
PORT = 0
client = None


def create_new_dir_and_copy(user_path, socket, Client):
    size = str(len(Client.path))
    socket.send(bytes(size.zfill(100), encoding='utf8'))
    seperator1 = "AVITAL"
    seperator2 = "NOA"
    for (path, dirs, files) in os.walk(user_path, topdown=True):
        s_for_dir = path + seperator1
        for dir in dirs:
            s_for_dir = s_for_dir + dir + seperator2
        size_s_dir = str(len(s_for_dir))
        if size_s_dir != '' and s_for_dir != '':
            socket.send(bytes(size_s_dir.zfill(8), encoding='utf8'))
            socket.send(bytes(s_for_dir, encoding='utf8'))
        s_for_file = ''
        for file in files:
            if file == files[0]:
                s_for_file = file + seperator2 + str(os.path.getsize(path + os.sep + file))
            else:
                s_for_file = s_for_file + seperator1 + file + seperator2 + str(os.path.getsize(path + os.sep + file))
        size_s_file = str(len(s_for_file))
        socket.send(bytes(size_s_file.zfill(8), encoding='utf8'))
        socket.send(bytes(s_for_file, encoding='utf8'))
        for file in files:
            client_file_path = path + os.sep + file
            with open(client_file_path, 'rb') as my_file:
                data = my_file.read()
                my_file.close()
            socket.send(data)


def start_copying_c_to_s(user_path, socket, Client):
    create_new_dir_and_copy(user_path, socket, Client)


def files_from_server(socket_s, client_path):
    seperator1 = "AVITAL"
    seperator2 = "NOA"
    rec = socket_s.recv(8)
    size_file = int(rec.decode())
    files_str = socket_s.recv(size_file).decode()
    all_files = files_str.split(seperator1)
    if files_str == '':
        return
    file_and_size_map = {}
    for d in all_files:
        file_and_size_map[d.split(seperator2)[0]] = d.split(seperator2)[1]
    for key in file_and_size_map:
        p = client_path + os.sep + key
        size_str = int(file_and_size_map[key])
        with open(client_path + os.sep + key, 'wb') as file:
            while size_str > 0:
                data = socket_s.recv(size_str)
                file.write(data)
                size_str = size_str - len(data)
        file.close()


def dir_from_server(path, socket_s, id_client):
    seperator1 = "AVITAL"
    seperator2 = "NOA"
    path_main = path
    os.makedirs(path_main + os.sep + id_client)
    size_user_path = int(socket_s.recv(1000).decode())
    while True:
        size_path = int(socket_s.recv(8).decode())
        if size_path == '':
            break
        path_and_dirs = socket_s.recv(size_path)
        path_and_dirs_str = path_and_dirs.decode('utf8')
        client_path = path_and_dirs_str.split(seperator1)[0]
        folder_path = client_path[size_user_path:]
        current_path = path_main + folder_path
        if path_and_dirs_str == "":
            continue
        dirs = path_and_dirs_str.split(seperator1)[1].split(seperator2)
        dirs.remove('')
        files_from_server(socket_s, current_path)
        for dir in dirs:
            path = os.path.join(current_path, dir)
            if dir == '':
                break
            os.makedirs(path)
        continue


class Client:
    def __init__(self, server_ip, server_port, path, timer, id_client, computer_name, sign):
        self.id_client = id_client
        self.server_ip = server_ip
        self.server_port = int(server_port)
        self.path = path
        self.timer = int(timer)
        self.computer_name = "noa"
        self.sign = 0


def event_notifier_to_server(path_to_operation, what_happend, s, client):
    size_of_computer = str(len(client.computer_name))
    s.send(bytes(size_of_computer.zfill(10), encoding='utf8'))
    s.send(bytes(client.computer_name, encoding='utf8'))
    s.send(bytes(what_happend.zfill(10), encoding='utf8'))
    s.send(bytes(client.id_client, encoding='utf8'))
    client_path_size = str(len(client.path))
    s.send(bytes(client_path_size.zfill(8), encoding='utf8'))
    s.send(bytes(client.path, encoding='utf8'))
    size_path_to_operation = str(len(path_to_operation))
    s.send(bytes(size_path_to_operation.zfill(8), encoding='utf8'))
    s.send(bytes(path_to_operation, encoding='utf8'))


def on_created(event):
    if client.sign == 1:
        return
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((IP, PORT))
    if os.path.isfile(event.src_path):
        with open(event.src_path, 'rb') as file:
            event_notifier_to_server(event.src_path, '4', s, client)
            data = file.read()
            size_of_data = str(len(data))
            s.send(bytes(size_of_data.zfill(8), encoding='utf8'))
            s.send(data)
    else:
        event_notifier_to_server(event.src_path, '5', s, client)
    s.close()


def on_deleted(event):
    if client.sign == 1:
        return
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((IP, PORT))
    event_notifier_to_server(event.src_path, '3', s, client)
    s.close()


def on_modified(event):
    return


def on_moved(event):
    if client.sign == 1:
        return
    on_deleted(event)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((IP, PORT))
    path_to_copy = event.dest_path
    if os.path.isfile(path_to_copy):
        with open(path_to_copy, 'rb') as file:
            event_notifier_to_server(event.dest_path, '4', s, client)
            data = file.read()
            size_of_data = str(len(data))
            s.send(bytes(size_of_data.zfill(8), encoding='utf8'))
            s.send(data)
    else:
        event_notifier_to_server(event.dest_path, '5', s, client)
    s.close()


def delete_folder_or_dir_from_client(path):
    if os.path.isfile(path):
        os.remove(path)
    else:
        for (root, dirs, files) in os.walk(path, topdown=False):
            for f in files:
                file_to_remove = os.path.join(root, f)
                os.remove(file_to_remove)
            for f in dirs:
                dir_to_remove = os.path.join(root, f)
                os.rmdir(dir_to_remove)
        os.rmdir(path)


def create_file(path_client, path_file, data):
    path_to_create_file = path_client + path_file
    with open(path_to_create_file, 'wb') as file:
        data_to_file = bytes(data, encoding='utf8')
        file.write(data_to_file)
    file.close()


def create_folder(path):
    os.makedirs(path)


def get_changes_from_server(client, what_happend, s):
    size_of_computer = str(len(client.computer_name))
    s.send(bytes(size_of_computer.zfill(10), encoding='utf8'))
    s.send(bytes(client.computer_name, encoding='utf8'))
    s.send(bytes(what_happend.zfill(10), encoding='utf8'))
    s.send(bytes(client.id_client, encoding='utf8'))
    size_str = int(s.recv(8).decode('utf-8'))
    change_str = s.recv(size_str).decode('utf-8')
    size_str = size_str - len(change_str)
    while size_str > 0:
        data_to_change = s.recv(size_str).decode('utf8')
        size_str = size_str - len(data_to_change)
        change_str = change_str + data_to_change
    while True:
        if change_str == "0":
            break
        data = change_str.split('$')
        operation = data[0]
        path = data[1]
        data_to_file = data[2]
        if operation == '3':
            delete_folder_or_dir_from_client(path)
        if operation == '4':
            create_file(client.path, path, data_to_file)
        if operation == '5':
            create_folder(path)
        size_str = int(s.recv(8).decode('utf-8'))
        change_str = s.recv(size_str).decode('utf-8')
        size_str = size_str - len(change_str)
        while size_str > 0:
            data_to_change = s.recv(size_str).decode('utf8')
            size_str = size_str - len(data_to_change)
            change_str = change_str + data_to_change


def call_WD():
    counter = client.timer
    patterns = ["*"]  # all the files
    ignore_patterns = None
    ignore_directories = False
    case_sensitive = True
    my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)  #
    # creating event handler
    my_event_handler.on_created = on_created  # specify to handler that we want the function to be called when event
    # is raised
    my_event_handler.on_deleted = on_deleted  # like pointer to function
    my_event_handler.on_modified = on_modified  # like pointer to function
    my_event_handler.on_moved = on_moved  # like pointer to function
    path = client.path
    go_recursively = True
    my_observer = Observer()
    my_observer.schedule(my_event_handler, path, recursive=go_recursively)  # the event handler, the path, for
    my_observer.start()
    counter = client.timer
    try:
        while True:
            time.sleep(1)
            counter = counter - 1
            print(counter, client.sign)
            if counter == 0:
                client.sign = 1
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((IP, PORT))
                print("I CONNECTED!!", client.sign)
                get_changes_from_server(client, '9', s)
                #s.send(bytes('0', encoding='utf8'))
                s.close()
                client.sign = 0
                counter = client.timer
    except KeyboardInterrupt:
        my_observer.stop()
        my_observer.join()


if len(sys.argv) == 6:
    client = Client(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], -1, 0)
    IP = sys.argv[1]
    PORT = int(sys.argv[2])
else:
    client = Client(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], -1, 0, 0)
    IP = sys.argv[1]
    PORT = int(sys.argv[2])
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((client.server_ip, client.server_port))
if client.id_client == -1:
    size_of_computer = str(len(client.computer_name))
    s.send(bytes(size_of_computer.zfill(10), encoding='utf8'))
    s.send(bytes(client.computer_name, encoding='utf8'))
    status = str(1)
    s.send(bytes(status.zfill(10), encoding='utf8'))
    s.send(bytes(status.zfill(10), encoding='utf8'))
    data = s.recv(128)
    client.id_client = data.decode('utf8')
    start_copying_c_to_s(client.path, s, client)
    s.close()
    call_WD()
else:  # 2
    size_of_computer = str(len(client.computer_name))
    s.send(bytes(size_of_computer.zfill(10), encoding='utf8'))
    s.send(bytes(client.computer_name, encoding='utf8'))
    status = str(2)
    s.send(bytes(status.zfill(10), encoding='utf8'))
    s.send(bytes(client.id_client, encoding='utf8'))
    is_computer_in_dict = s.recv(1)
    if str(is_computer_in_dict.decode()) == "0":
        dir_from_server(client.path, s, client.id_client)
        s.close()
        call_WD()

