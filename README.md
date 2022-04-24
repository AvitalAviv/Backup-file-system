# Backup File System
Backup file system in Linux written in Python using **Watchdog** library.

## Abstract
* *client.py* - client running with args:

      1. server's IP address
      2. server's port
      3. the directory to monitor and back-up
      4. user's ID (optional) - only if its an existing user (if no input, it creates new dir on server and copy 
         all data from client's dir).
    If client enter with user ID, it means that he has an directory created on server(no need to copy directory to server). 
    
    If there is no last argument, the server randomize ID for the client, and copy all client's dir and start to monitor it.
    Client sends all the data to the server after registration as a new client.
    
    After the data transferring in each option, the client code is monitoring changes in the directory registered to the service    
    Every change in client's dir appear in client's clone directory on the server.

* *server.py* - server running with args - server's port.

  Server accept client by client and listen to changes. When change happend on client's directory, it gets all the data about the change from the client. The server need to update not only the 
