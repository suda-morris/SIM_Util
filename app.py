# encoding: utf-8

import random
import time

import serial
import serial.threaded

from simdev.sim7100c import Sim7100C


if __name__ == "__main__":
    ser = serial.Serial("COM7", baudrate=115200, timeout=1)
    with serial.threaded.ReaderThread(ser, Sim7100C) as gprs_module:
        gprs_module.enable_echo(False)
        gprs_module.synchronize()
        print(u"工厂ID:", gprs_module.get_manufacturer_identification())
        print(u"模组ID:", gprs_module.get_model_identification())
        print(u"版本ID:", gprs_module.get_revision_identification())
        print(u"产品序列号:", gprs_module.get_serial_number())
        print(u"运营商:", gprs_module.get_service_provider())
        print(u"信号强度:", gprs_module.get_signal_quality())
        print(u"IMEI号:", gprs_module.get_imei())
        print(u"电源电压:", gprs_module.get_power_voltage())
        print(u"模块温度:", gprs_module.get_temperature())
        print(u"www.baidu.com的IP地址:", gprs_module.url2ip("www.baidu.com"))
        print(u"58.211.251.178的URL地址:", gprs_module.ip2url("58.211.251.178"))

        print(u"设置TCP/IP应用模式:透传")
        gprs_module.select_transparent_mode()

        print(u"打开网络:", gprs_module.open_network())
        print(u"IP地址:", gprs_module.get_ip_address())
        print(u"建立TCP连接:", gprs_module.establish_tcp_socket(0, "119.28.87.186", 36295))
        count = 100
        while count:
            gprs_module.transparent_content(random.randint(1, 100))
            time.sleep(1)
            count -= 1

        # count = 200
        # while count:
        # gprs_module.tcp_send(0, random.randint(1, 100))
        # time.sleep(0.1)
        #     count -= 1
        # print(u"发送bye:", gprs_module.tcp_send(0, "bye"))

        print(u"关闭连接:", gprs_module.close_socket(0))
        print(u"关闭网络:", gprs_module.close_network())

        gprs_module.stop()
        # gprs_module.reset()
        # gprs_module.power_off()

