import os
import random
import socket
import string
import sys


server_path = os.getcwd()
D1 = {}


class Client:
     def __init__(self, id_client):
         self.id = id_client


port = int(sys.argv[1])
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', port))
server.listen(5)


def get_random_id():
    key = ""
    letters = string.ascii_letters
    for i in range(10):
        letters += str(i)
    for i in range(128):
        index = random.randint(0, len(letters) - 1)
        key = key + letters[index]
    return key


def create_files(current_path, client_socket, id_client):
    seperator1 = "AVITAL"
    seperator2 = "NOA"
    size_file = int(client_socket.recv(8).decode())
    files_str = client_socket.recv(size_file).decode()
    all_files = files_str.split(seperator1)
    if files_str == '':
        return
    file_and_size_map = {}
    for d in all_files:
        file_and_size_map[d.split(seperator2)[0]] = d.split(seperator2)[1]
    for key in file_and_size_map:
        size_str = int(file_and_size_map[key])
        with open(current_path + os.sep + key, 'wb') as file:
            while size_str > 0:
                data = client_socket.recv(size_str)
                size_data = len(data)
                file.write(data)
                size_str = size_str - size_data
        file.close()


def copy_dir_from_client_to_server(server_path, client_socket, id_client):
    seperator1 = "AVITAL"
    seperator2 = "NOA"
    path_main = os.path.join(server_path, id_client)
    os.makedirs(path_main)
    size_user_path = int(client_socket.recv(100).decode())
    while True:
        size_path = (client_socket.recv(8).decode())
        if size_path == '':
            break
        path_and_dirs = client_socket.recv(int(size_path))
        path_and_dirs_str = path_and_dirs.decode('utf8')
        client_path = path_and_dirs_str.split(seperator1)[0]
        folder_path = client_path[size_user_path:]
        current_path = path_main + folder_path
        if path_and_dirs_str == "":
            continue
        dirs = path_and_dirs_str.split(seperator1)[1].split(seperator2)
        dirs.remove('')
        create_files(current_path, client_socket, id_client)
        for dir in dirs:
            path = os.path.join(current_path, dir)
            if dir == '':
                break
            os.makedirs(path)
        continue


def send_dir_from_sever_to_client(server_path_to_copy, client_socket_to_copy, id_client):
    size = str(len(server_path_to_copy))
    client_socket_to_copy.send(bytes(size.zfill(8), encoding='utf8'))
    seperator1 = "AVITAL"
    seperator2 = "NOA"
    path_with_id = server_path_to_copy + os.sep + id_client
    for (path, dirs, files) in os.walk(path_with_id, topdown=True):
        s_for_dir = path + seperator1
        for dir in dirs:
            s_for_dir = s_for_dir + dir + seperator2
        size_s_dir = str(len(s_for_dir))
        if size_s_dir != '' and s_for_dir != '':
            client_socket_to_copy.send(bytes(size_s_dir.zfill(8), encoding='utf8'))
            client_socket_to_copy.send(bytes(s_for_dir, encoding='utf8'))
        s_for_file = ''
        for file in files:
            if file == files[0]:
                s_for_file = file + seperator2 + str(os.path.getsize(path + os.sep + file))
            else:
                s_for_file = s_for_file + seperator1 + file + seperator2 + str(os.path.getsize(path + os.sep + file))
        size_s_file = str(len(s_for_file))
        client_socket.send(bytes(size_s_file.zfill(8), encoding='utf8'))
        client_socket.send(bytes(s_for_file, encoding='utf8'))
        for file in files:
            server_file_path = path + os.sep + file
            with open(server_file_path, 'rb') as my_file:
                data = my_file.read()
                my_file.close()
            client_socket_to_copy.send(data)
    client_socket_to_copy.send(bytes('0', encoding='utf8'))


def delete_folder(path):
    for (root,dirs,files) in os.walk(path, topdown=False):
        for f in files:
            file_to_remove = os.path.join(root, f)
            os.remove(file_to_remove)
        for f in dirs:
            dir_to_remove = os.path.join(root, f)
            os.rmdir(dir_to_remove)
    os.rmdir(path)


def create_new_file(server_path, socket):
    str_data = ''
    size_of_data = int(socket.recv(8).decode('utf-8'))
    with open(server_path, 'wb') as file:
        while size_of_data > 0:
            data = socket.recv(size_of_data)
            accepted_size = len(data)
            size_of_data = size_of_data - accepted_size
            file.write(data)
            str_data += data.decode('utf-8')
    file.close()
    return str_data


def update_dict1(current_computer_name, the_change, id):
    global D1
    for name_computer in D1[id].keys():
        if not current_computer_name == name_computer:
            D1[id][name_computer].append(the_change)


def listen_to_changes(socket, id, server_path, what_happened, computer_name):
    if what_happened == 9:
        return
    size_path = int(socket.recv(8).decode())
    path_client = socket.recv(size_path).decode()
    size_inner_path = int(socket.recv(8).decode())
    inner_path = socket.recv(size_inner_path).decode()
    client_folder = inner_path[len(path_client):]
    current_server_path = os.path.join(server_path, id)
    current_server_path = current_server_path + client_folder
    # remove folder or file
    if what_happened == 3:
        make_change = str(3) + '$' + current_server_path[len(server_path):] + '$' + 'empty_data'
        update_dict1(computer_name, make_change, id)
        if os.path.isdir(current_server_path):
            delete_folder(current_server_path)
        if os.path.isfile(current_server_path):
            os.remove(current_server_path)
    if what_happened == 4:
        data_from_file = create_new_file(current_server_path, socket)
        make_change = str(4) + '$' + current_server_path[len(server_path):] + '$' + data_from_file
        update_dict1(computer_name, make_change, id)
    if what_happened == 5:
        os.mkdir(current_server_path)
        make_change = str(5) + '$' + current_server_path[len(server_path):] + '$' + 'empty_data'
        update_dict1(computer_name, make_change, id)


# the main dictionary - contains
while True:
    client_socket, client_address = server.accept()
    size_name_computer = int(client_socket.recv(10).decode())
    computer_name_from_client = client_socket.recv(size_name_computer)
    computer_name = str(computer_name_from_client.decode())
    what_happened = client_socket.recv(10)
    what_happened = int(what_happened.decode())
    id = client_socket.recv(128)
    id_client = str(id.decode())
    random_id = 0
    client = Client(0)
    if what_happened == 1:
        random_id = get_random_id()
        client.id = random_id
        D2 = {computer_name: []}
        D1[client.id] = D2
        client_socket.send(bytes(random_id, encoding='utf8'))
        copy_dir_from_client_to_server(server_path, client_socket, random_id)
    # need to continue this!!!!
    else:
        flag = 0
        for computer_name_in_dict in D1[id_client].keys():
            if computer_name_in_dict == computer_name:
                flag = 1 # if the computer name is appear in dict = need to update, no need to send all the files.
                break
        # known client, new computer
        if flag == 0:
            client_socket.send(bytes('0', encoding='utf8'))
            D1[id_client][computer_name] = []
            send_dir_from_sever_to_client(server_path, client_socket, id_client)
        # known client, known computer
        if flag == 1:
            # running all the changes
            for change_in_computers in D1[id_client].get(computer_name):
                client_socket.send(bytes(str(len(change_in_computers)).zfill(8), encoding='utf8'))
                client_socket.send(bytes(change_in_computers, encoding='utf8'))
            client_socket.send(bytes(str(len(str(0))).zfill(8), encoding='utf8'))
            client_socket.send(bytes("0", encoding='utf8'))
            listen_to_changes(client_socket, id_client, server_path, what_happened, computer_name)
            D1[id_client][computer_name].clear()
    client_socket.close()
