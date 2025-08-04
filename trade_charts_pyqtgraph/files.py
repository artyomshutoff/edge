import paramiko

def get():
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(
        hostname="192.168.0.103",
        username="artyomshutoff",
        password="5722"
    )

    ftp_client=ssh_client.open_sftp()
    remote_path = "/home/artyomshutoff/binance_parser/trades.db"
    local_path = "C:/Users/artyomshutoff/Documents/GitHub/binance_parser/trades.db"

    ftp_client.get(remote_path, local_path)

    ftp_client.close()

get()