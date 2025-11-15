import asyncio
import os
import pty
import fcntl
import struct
import termios
import logging

logger = logging.getLogger(__name__)

class PtyProcess:
    def __init__(self, websocket, loop):
        self.websocket = websocket
        self.loop = loop
        self.master_fd = None
        self.pid = None
        self.pty_read_task = None
        self.closed = False

    async def spawn(self, cmd=["bash"]):
        self.master_fd, slave_fd = pty.openpty()
        self.pid = os.fork()

        if self.pid == 0:  # Child process
            os.setsid()
            os.dup2(slave_fd, 0)  # stdin
            os.dup2(slave_fd, 1)  # stdout
            os.dup2(slave_fd, 2)  # stderr
            os.close(self.master_fd)
            os.environ['TERM'] = 'xterm-256color'
            try:
                os.execlp(cmd[0], *cmd)
            except Exception as e:
                logger.error(f"Failed to execute {cmd[0]} in child process: {e}")
                os._exit(1)  # Exit child process on error
        else:  # Parent process
            os.close(slave_fd)
            logger.info(f"PTY process spawned with PID: {self.pid}, master_fd: {self.master_fd}")
            self.loop.add_reader(self.master_fd, self._read_from_pty)
            self.pty_read_task = self.loop.create_task(self._wait_for_pty_exit())

    def _read_from_pty(self):
        try:
            output = os.read(self.master_fd, 1024)
            if output:
                self.loop.create_task(self.websocket.send_text(output.decode(errors="ignore")))
            else:
                logger.info(f"PTY master_fd {self.master_fd} returned empty bytes, assuming process exited.")
                self.close()
        except (IOError, OSError) as e:
            if not self.closed:
                logger.error(f"Error reading from PTY {self.master_fd}: {e}")
                self.close()
        except Exception as e:
            if not self.closed:
                logger.error(f"Unexpected error in _read_from_pty for PTY {self.master_fd}: {e}")
                self.close()

    async def _wait_for_pty_exit(self):
        try:
            # Wait for the child process to exit
            await self.loop.run_in_executor(None, os.waitpid, self.pid, 0)
            logger.info(f"PTY process {self.pid} exited.")
        except Exception as e:
            logger.error(f"Error waiting for PTY process {self.pid} to exit: {e}")
        finally:
            if not self.closed:
                self.close()

    def write(self, data: bytes):
        if self.master_fd and not self.closed:
            try:
                os.write(self.master_fd, data)
            except OSError as e:
                logger.error(f"Error writing to PTY {self.master_fd}: {e}")
                self.close()

    def set_winsize(self, row, col, xpix=0, ypix=0):
        if self.master_fd and not self.closed:
            winsize = struct.pack("HHHH", row, col, xpix, ypix)
            try:
                fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, winsize)
                logger.debug(f"Set window size for PTY {self.master_fd} to {row}x{col}")
            except OSError as e:
                logger.error(f"Failed to set window size for PTY {self.master_fd}: {e}")

    def close(self):
        if not self.closed:
            self.closed = True
            logger.info(f"Closing PTY process {self.pid}, master_fd: {self.master_fd}")
            if self.master_fd:
                self.loop.remove_reader(self.master_fd)
                os.close(self.master_fd)
                self.master_fd = None
            
            if self.pid:
                try:
                    # Attempt to terminate the child process gracefully
                    os.kill(self.pid, 15) # SIGTERM
                    # Give it a moment to exit, but don't block the event loop
                    # The _wait_for_pty_exit task should handle the actual waitpid
                except ProcessLookupError:
                    logger.info(f"PTY process {self.pid} already exited.")
                except Exception as e:
                    logger.error(f"Error during PTY process {self.pid} termination: {e}")
                self.pid = None

            if self.pty_read_task:
                self.pty_read_task.cancel()
                self.pty_read_task = None
