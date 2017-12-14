# encoding: utf-8
import queue
import threading
import logging

import serial
import serial.threaded


class ATException(Exception):
    pass


class ATProtocol(serial.threaded.LineReader):
    def __init__(self):
        super(ATProtocol, self).__init__()
        self.alive = True
        self.response_queue = queue.Queue()
        self.event_queue = queue.Queue()
        self._event_thread = threading.Thread(target=self._run_event, daemon=True, name="at-event")
        self._event_thread.start()
        self.lock = threading.Lock()

    def stop(self):
        """
        Stop the event processing thread, abort pending commands
        """
        self.alive = False
        self.event_queue.put(None)
        self.response_queue.put("<exit>")

    def _run_event(self):
        """
        Process events in a separate thread so that input thread is not blocked.
        """
        while self.alive:
            try:
                self.handle_event(self.event_queue.get())
            except:
                logging.exception("_run_event")

    def handle_event(self, event):
        print("event received: {%event}".format(event=event))

    def handle_line(self, line):
        """
        Handle input from serial port, check for events.
        """
        if line.startswith('+'):
            self.event_queue.put(line)
        else:
            self.response_queue.put(line)

    def command(self, command, response_ok="OK", response_no="ERROR", timeout=5):
        """
         Set an AT command and wait for the response.
        """
        with self.lock:  # ensure that just one thread is sending commands at once
            self.write_line(command)
            lines = []
            while True:
                try:
                    line = self.response_queue.get(timeout=timeout)
                    if line == response_ok:
                        return lines
                    elif line == response_no:
                        return None
                    else:
                        lines.append(line)
                except queue.Empty:
                    raise ATException("AT command timeout {command}".format(command=command))