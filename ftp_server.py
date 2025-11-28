
import argparse
import os
import logging
import socket
import select
import traceback
from OpenSSL import SSL
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import TLS_FTPHandler
from pyftpdlib.servers import ThreadedFTPServer
from pyftpdlib import log

def get_lan_ip():
    """Retrieves the local IP address of the machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

class ConfiguredFTPHandler(TLS_FTPHandler):
    """
    A handler that manually performs a blocking TLS handshake to work around
    issues in the underlying library's handshake loop.
    """
    lan_ip = None

    def __init__(self, conn, server, ioloop=None):
        print("="*70)
        print(f"[HANDLER __init__] START: New connection from {conn.getpeername()}.")
        
        if self.implicit_tls:
            print("[HANDLER __init__] Implicit TLS: Starting robust manual handshake...")
            try:
                ctx = self.get_ssl_context()
                if not ctx:
                    raise RuntimeError("get_ssl_context() returned None.")

                ssl_conn = SSL.Connection(ctx, conn)
                ssl_conn.set_accept_state()

                # The timeout is a class attribute on the handler.
                timeout = self.__class__.timeout
                while True:
                    try:
                        print("[HANDLER __init__] Performing ssl_conn.do_handshake()...")
                        ssl_conn.do_handshake()
                        break  # Handshake successful
                    except SSL.WantReadError:
                        print(f"[HANDLER __init__] Got WantReadError. Waiting for socket to be readable (timeout: {timeout}s)...")
                        readable, _, _ = select.select([ssl_conn], [], [], timeout)
                        if not readable:
                            raise TimeoutError("Timeout during TLS handshake while waiting for client.")
                        print("[HANDLER __init__] Socket is readable. Retrying handshake.")

                print("[HANDLER __init__] >>> SUCCESS: Manual handshake complete.")
                conn = ssl_conn
                
            except Exception as e:
                print("\n[HANDLER __init__] >>>>> FATAL: MANUAL TLS HANDSHAKE FAILED <<<<<")
                print(f"[HANDLER __init__]   - {e.__class__.__name__}: {e}")
                traceback.print_exc()
                conn.close()
                return

        print("[HANDLER __init__] Calling super().__init__()...")
        super().__init__(conn, server, ioloop)
        print("[HANDLER __init__] super().__init__() completed.")
        print(f"[HANDLER __init__] Final state: tls_on={getattr(self, 'tls_on', 'Not Set')}")
        print("="*70)

    @classmethod
    def get_ssl_context(cls):
        """
        Overrides the base method to create a pyOpenSSL context, which is
        required for pyftpdlib's FTPS implementation.
        """
        if not hasattr(cls, '_ssl_context'):
            print("[get_ssl_context] Creating new pyOpenSSL Context.")
            try:
                ctx = SSL.Context(SSL.SSLv23_METHOD)
                ctx.set_options(SSL.OP_NO_SSLv2 | SSL.OP_NO_SSLv3 | SSL.OP_NO_TLSv1 | SSL.OP_NO_TLSv1_1)
                ctx.use_privatekey_file(cls.keyfile)
                ctx.use_certificate_file(cls.certfile)
                ctx.check_privatekey()
                cls._ssl_context = ctx
                print("[get_ssl_context] New pyOpenSSL context created successfully.")
            except Exception as e:
                print(f"[get_ssl_context] CRITICAL ERROR creating SSL context: {e}")
                return None
        return cls._ssl_context

def main():
    log.config_logging(level=logging.DEBUG)
    parser = argparse.ArgumentParser(description="FTP/FTPS server that maps to a network drive.")
    parser.add_argument('--drive', required=True, help="The absolute path to the network drive or directory to serve.")
    parser.add_argument('--host', default='0.0.0.0', help="The host IP address to bind to.")
    parser.add_argument('--port', type=int, default=21, help="The port to listen on.")
    parser.add_argument('--user', help="Username for authenticated access.")
    parser.add_argument('--password', help="Password for authenticated access.")
    parser.add_argument('--allow-anonymous', action='store_true', help="Allow anonymous access.")
    parser.add_argument('--ftps-mode', choices=['explicit', 'implicit'], help="Set the FTPS mode.")
    parser.add_argument('--certfile', help="Path to the SSL certificate file for FTPS.")
    parser.add_argument('--keyfile', help="Path to the SSL key file for FTPS.")
    args = parser.parse_args()

    if not os.path.isdir(args.drive):
        print(f"Error: The specified drive path '{args.drive}' does not exist or is not accessible.")
        return

    handler = ConfiguredFTPHandler
    handler.implicit_tls = False
    handler.tls_control_required = False
    handler.tls_data_required = False
    
    if args.certfile and args.keyfile:
        handler.certfile = args.certfile
        handler.keyfile = args.keyfile
        if args.ftps_mode == 'implicit':
            handler.implicit_tls = True
        else: # Default to explicit if certs are provided
            handler.tls_control_required = True
            handler.tls_data_required = True

    authorizer = DummyAuthorizer()
    if args.user and args.password:
        authorizer.add_user(args.user, args.password, args.drive, perm="elradfmw")
    if args.allow_anonymous:
        authorizer.add_anonymous(args.drive, perm="elradfmw")
    handler.authorizer = authorizer
    handler.banner = "pyftpdlib based ftpd ready."
    handler.lan_ip = get_lan_ip()

    address = (args.host, args.port)
    
    server = ThreadedFTPServer(address, handler)
    server.max_cons = 256
    server.max_cons_per_ip = 5
    
    if handler.implicit_tls or handler.tls_control_required:
        if not handler.get_ssl_context():
            print("[Main] CRITICAL: Could not start server due to an error in SSL context creation.")
            return

    print(f"Starting FTP server on {args.host}:{args.port}, serving directory '{args.drive}'...")
    server.serve_forever()

if __name__ == "__main__":
    main()
