import paramiko

def get():
    ssh_client =paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(
        hostname="192.168.0.103",
        username="artyomshutoff",
        password="5722"
    )
    
    ftp_client=ssh_client.open_sftp()
    remote_path = "/home/artyomshutoff/footprint_charts_pyqtgraph/"
    local_path = "C:/Users/artyomshutoff/Documents/GitHub/footprint_charts_pyqtgraph/"
    
    files = ["delta.db", "footprint.db", "heatmap.db"]
    
    for i in files:
        ftp_client.get(remote_path + i, local_path + i)
    
    ftp_client.close()