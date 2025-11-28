# FTP to Network Drive Gateway

This project provides a simple yet powerful Python script that creates an FTP/FTPS server. Its primary purpose is to act as a gateway, allowing any standard FTP client to connect and interact with a specified local or network-mounted drive on the host machine.

This is useful for legacy devices (like security NVRs) that can only back up to an FTP server, allowing them to save files directly to a modern storage solution like a network drive.

## Features

- **FTP and FTPS:** Supports standard unencrypted FTP and secure FTP over SSL/TLS (FTPS) with both explicit and implicit modes.
- **Flexible Authentication:** Allows for a single authenticated user, anonymous access, or both.
- **Direct File Access:** Files are read from and written directly to the target directory. No temporary storage is used.
- **Configurable:** All major settings (directory, host, port, credentials) can be configured via command-line arguments.
- **Cross-Platform:** Runs on any operating system with Python and a network connection.

## Prerequisites

- Python 3.6+
- `pyftpdlib` library
- **For FTPS Support:** `pyOpenSSL` is required to enable the TLS/SSL features.

## Installation

1.  Clone this repository or download the `ftp_server.py` script.
2.  Install the required Python libraries.

    **For standard FTP:**
    ```sh
    pip install pyftpdlib
    ```

    **For secure FTPS:**
    The `pyOpenSSL` library is required for FTPS functionality. Install it first, then reinstall `pyftpdlib` to ensure it builds with the necessary TLS/SSL support.
    ```sh
    pip install pyOpenSSL
    pip install --upgrade --force-reinstall pyftpdlib
    ```

## Usage

Run the server from your terminal, providing the path to the directory you want to serve.

### Command-Line Arguments

- `--drive` (Required): The absolute path to the network drive or directory to serve.
- `--host`: The host IP address to bind to. (Default: `0.0.0.0`, listens on all interfaces)
- `--port`: The port to listen on. (Default: `21` for FTP/Explicit FTPS, `990` for Implicit FTPS)
- `--user`: Username for authenticated access.
- `--password`: Password for authenticated access.
- `--allow-anonymous`: If present, allows anonymous read and write access.
- `--ftps-mode`: Enables FTPS and sets the mode. Can be `explicit` or `implicit`. If a certfile is provided without this argument, it defaults to `explicit`.
- `--certfile`: Path to the SSL certificate file (required for FTPS).
- `--keyfile`: Path to the SSL private key file (required for FTPS).

### Examples

**1. Basic FTP with a User**

Serve the `Z:\backups` directory on the default port `21` for `myuser`.

```sh
python ftp_server.py --drive "Z:\backups" --user myuser --password mysecretpassword
```

**2. FTP with Anonymous Access**

Serve the `C:\public` directory, allowing anonymous users to connect, read, and write files.

```sh
python ftp_server.py --drive "C:\public" --allow-anonymous
```

**3. Secure FTPS Server (Explicit Mode)**

Serve the `Z:\secure-storage` directory using Explicit FTPS on port `21`. The client must initiate the TLS handshake.

```sh
python ftp_server.py --drive "Z:\secure-storage" --user myuser --password mysecretpassword --ftps-mode explicit --certfile "cert.pem" --keyfile "key.pem"
```
*Note: If you provide a certfile and keyfile without the `--ftps-mode` argument, the server will default to explicit mode.*

**4. Secure FTPS Server (Implicit Mode)**

Serve the `Z:\secure-storage` directory using Implicit FTPS. It is recommended to use the standard port `990` for this mode.

```sh
python ftp_server.py --drive "Z:\secure-storage" --port 990 --user myuser --password mysecretpassword --ftps-mode implicit --certfile "cert.pem" --keyfile "key.pem"
```

---

### Generating a Self-Signed Certificate for FTPS

For testing or internal use, you can generate a self-signed SSL certificate using `openssl`.

```sh
openssl req -new -x509 -nodes -out cert.pem -keyout key.pem -days 365
```

This command will prompt you for some information and generate `cert.pem` and `key.pem` files in your current directory, valid for 365 days. You can then use these files with the FTPS arguments.
