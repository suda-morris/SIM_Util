# encoding: utf-8
import time
import queue
import logging

from simdev.at_protocol import ATProtocol, ATException


class Sim7100C(ATProtocol):
    """
    Communication with SIM7100C GPRS module.
    """

    def __init__(self):
        super(Sim7100C, self).__init__()
        self.event_responses = queue.Queue()
        self._awaiting_response_for = None
        self._send_length = 0
        self.transparent_mode = True

    def connection_made(self, transport):
        super(Sim7100C, self).connection_made(transport)
        time.sleep(0.3)
        self.transport.serial.reset_input_buffer()

    def handle_event(self, event):
        """
        Handle events and command responses starting with '+...'
        """
        if not event:
            return
        if event.startswith("+CGMR") and self._awaiting_response_for.startswith("AT+CGMR"):
            rev = event.split(':')[1]
            rev = rev.strip()
            self.event_responses.put(rev)
        elif event.startswith("+CSPN") and self._awaiting_response_for.startswith("AT+CSPN?"):
            rev = event.split(':')[1]
            rev = rev.split(',')[0]
            rev = rev.strip()
            self.event_responses.put(rev)
        elif event.startswith("+CSQ") and self._awaiting_response_for.startswith("AT+CSQ"):
            rev = event.split(':')[1]
            rev = rev.split(',')[0]
            rev = rev.strip()
            self.event_responses.put(rev)
        elif event.startswith("+SIMEI") and self._awaiting_response_for.startswith("AT+SIMEI?"):
            rev = event.split(':')[1]
            rev = rev.strip()
            self.event_responses.put(rev)
        elif event.startswith("+CBC") and self._awaiting_response_for.startswith("AT+CBC"):
            rev = event.split(':')[1]
            rev = rev.strip()
            self.event_responses.put(rev)
        elif event.startswith("+CPMUTEMP") and self._awaiting_response_for.startswith("AT+CPMUTEMP"):
            rev = event.split(':')[1]
            rev = rev.strip()
            self.event_responses.put(rev)
        elif event.startswith("+CDNSGIP") and self._awaiting_response_for.startswith("AT+CDNSGIP"):
            rev = event.split(':')[1]  # +CDNSGIP: 1,"www.google.com","203.208.39.99"
            rev = rev.split(',')[2]
            rev = rev.strip()
            self.event_responses.put(rev)
        elif event.startswith("+CDNSGHNAME") and self._awaiting_response_for.startswith("AT+CDNSGHNAME"):
            rev = event.split(':')[1]  # +CDNSGHNAME: 1,"mail.sim.com","58.32.231.148"
            rev = rev.split(',')[1]
            rev = rev.strip()
            self.event_responses.put(rev)
        elif event.startswith("+IPADDR") and self._awaiting_response_for.startswith("AT+IPADDR"):
            rev = event.split(':')[1]  # +IPADDR: 10.71.155.118
            rev = rev.strip()
            self.event_responses.put(rev)
        elif event.startswith("+NETOPEN") or event.startswith("+NETCLOSE"):
            rev = event.split(':')[1]
            rev = int(rev)
            rev = "Success" if rev == 0 else "Fail"
            self.event_responses.put(rev)
        elif event.startswith("+CIPOPEN") and self._awaiting_response_for.startswith("AT+CIPOPEN"):
            rev = event.split(':')[1]
            rev = rev.split(',')[1]
            rev = int(rev)
            rev = "Success" if rev == 0 else "Fail"
            self.event_responses.put(rev)
        elif event.startswith("+CIPCLOSE") and self._awaiting_response_for.startswith("AT+CIPCLOSE"):
            rev = event.split(':')[1]
            rev = rev.split(',')[1]
            rev = int(rev)
            rev = "Success" if rev == 0 else "Fail"
            self.event_responses.put(rev)
        elif event.startswith("+CIPSEND") and self._awaiting_response_for.startswith("AT+CIPSEND"):
            rev = event.split(':')[1]  # +CIPSEND: 0,5,5
            rev = rev.split(",")
            rev = "Success" if int(rev[1]) == int(rev[2]) else "Fail"
            self.event_responses.put(rev)
        else:
            logging.warning("unhandle event: {event}".format(event=event))

    def command_with_event_response(self, command, response_ok="OK", response_no="ERROR", timeout=5):
        """
        Send a command that responds with '+...' line
        """
        with self.lock:  # ensure that just one thread is sending commands at once
            self._awaiting_response_for = command
            self.write_line(command)
            info = self.event_responses.get()
            self._awaiting_response_for = None
            while True:
                try:
                    line = self.response_queue.get(timeout=timeout)
                    if line == response_ok:
                        return info
                    elif line == response_no:
                        return None
                except queue.Empty:
                    raise ATException("AT command timeout {command}".format(command=command))

    def enable_echo(self, enable=True):
        if enable:
            return self.command("ATE1")
        else:
            return self.command("ATE0")

    def power_off(self):
        ret = self.command("AT+CPOF")
        return ret if ret else None

    def reset(self):
        ret = self.command("AT+CRESET")
        return ret if ret else None

    def synchronize(self):
        ret = self.command("AT")
        return ret if ret else None

    def get_manufacturer_identification(self):
        id_list = self.command("AT+CGMI")
        return id_list[1] if id_list else None

    def get_model_identification(self):
        id_list = self.command("AT+CGMM")
        return id_list[1] if id_list else None

    def get_revision_identification(self):
        return self.command_with_event_response("AT+CGMR")

    def get_serial_number(self):
        id_list = self.command("AT+CGSN")
        return id_list[1] if id_list else None

    def get_service_provider(self):
        return self.command_with_event_response("AT+CSPN?")

    def get_signal_quality(self):
        return self.command_with_event_response("AT+CSQ")

    def get_imei(self):
        return self.command_with_event_response("AT+SIMEI?")

    def get_power_voltage(self):
        return self.command_with_event_response("AT+CBC")

    def get_temperature(self):
        return self.command_with_event_response("AT+CPMUTEMP")

    def url2ip(self, url):
        return self.command_with_event_response('AT+CDNSGIP="{url}"'.format(url=url))

    def ip2url(self, ip):
        return self.command_with_event_response('AT+CDNSGHNAME="{ip}"'.format(ip=ip))

    def select_transparent_mode(self, transparent=True):
        self.transparent_mode = True if transparent else False
        return self.command("AT+CIPMODE={md}".format(md=1 if transparent else 0))

    def open_network(self):
        return self.command_with_event_response("AT+NETOPEN")

    def close_network(self):
        return self.command_with_event_response("AT+NETCLOSE")

    def get_ip_address(self):
        return self.command_with_event_response("AT+IPADDR")

    def establish_tcp_socket(self, link_num, server_ipaddr, server_port):
        cmd = 'AT+CIPOPEN={link_num},"TCP","{ipaddr}",{port}'.format(link_num=link_num, ipaddr=server_ipaddr,
                                                                     port=server_port)
        if self.transparent_mode:
            with self.lock:  # ensure that just one thread is sending commands at once
                self.write_line(cmd)
                while True:
                    try:
                        line = self.response_queue.get(timeout=5)
                        if line.startswith("CONNECT"):
                            return "Success"
                    except queue.Empty:
                        raise ATException("AT command timeout {command}".format(command=cmd))
        else:
            return self.command_with_event_response(cmd)

    def close_socket(self, link_num):
        if self.transparent_mode:
            with self.lock:  # ensure that just one thread is sending commands at once
                time.sleep(1)
                self.transport.write("+++".encode(self.ENCODING, self.UNICODE_HANDLING))
                while True:
                    try:
                        line = self.response_queue.get(timeout=1)
                        if line.startswith("OK"):
                            break
                    except queue.Empty:
                        raise ATException("AT command timeout {command}".format(command="+++"))
        return self.command_with_event_response("AT+CIPCLOSE={link_num}".format(link_num=link_num))

    def transparent_content(self, content):
        with self.lock:  # ensure that just one thread is sending commands at once
            self.write_line(str(content))

    def tcp_send(self, link_num, content):
        content = str(content)
        cmd = "AT+CIPSEND={link_num},{length}".format(link_num=link_num, length=len(content))
        self._awaiting_response_for = cmd
        self._send_length = len(content)
        with self.lock:  # ensure that just one thread is sending commands at once
            self.write_line(cmd)
            time.sleep(0.1)
            self.transport.write(content.encode(self.ENCODING, self.UNICODE_HANDLING))
            while True:
                try:
                    line = self.response_queue.get(timeout=5)
                    if line.startswith("OK"):
                        info = self.event_responses.get()
                        self._awaiting_response_for = None
                        self._send_length = 0
                        return info
                except queue.Empty:
                    raise ATException("AT command timeout {command}".format(command=cmd))