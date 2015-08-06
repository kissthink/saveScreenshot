# -*- coding:  utf-8 -*-
#!/usr/bin/python
# author: wangxiaogang02@baidu.com
'''
代理IP维护策略：
----与城市设定解耦，只与维护的IP列表文件的IP值有关，此脚本只管IP可用性，不管城市
每一个小时从各种代理IP网站抓取对应城市的代理IP，这些IP是逐渐累积的，按时间保存在ProxyList文件夹下：
每15分钟，从cityIp.cfg中读取验证维护两个可用的IP：
1. 如果都可用，则不变
2. 如果只有一个IP可用，则使可用的IP为ip1，更新ip2(从维护的IP文件中读取并验证)
3. 如果两个IP都不可用，则从维护的IP列表中找出两个IP(这里需要知道来自IP列表的行数)，并验证
4. 如果列表中找不出可用的IP，则循环驱动例行的grapCityIp.py提前执行，直到找到可用IP
5. 如果驱动grapCityIp.py执行超过五次，则暂停循环，todo: 并发送邮件给我
'''

import ConfigParser
import ipProxy
import urllib2
import time
import config
import datetime
import os

CONFIGFILE="cityIp.cfg"

def checkProxy(proxy):
    testUrl = "http://www.baidu.com/"
    testStr = "030173"
    timeout = 5
    cookies = urllib2.HTTPCookieProcessor()
    proxyHandler = urllib2.ProxyHandler({"http" : r'http://%s' %(proxy)})
    opener = urllib2.build_opener(cookies,proxyHandler)
    opener.addheaders =[('User-Agent','Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36')]
    t1 = time.time()
    try:
        req = opener.open(testUrl,timeout=timeout)
        result = req.read()
        timeused = time.time() - t1
        pos = result.find(testStr)

        if pos > 1:
            print("ip ok: " + proxy)
            return True
        else:
            print("ip not use: " + proxy)
            return False
    except Exception,e:
        return False

def getIpfromProxyList(exceptIp):
    print("getIpfromProxyList start")
    try:
        TIME_FORMAT = '%Y%m%d_%H'
        currentHour = datetime.datetime.now()
        lastHour = currentHour - datetime.timedelta(hours = 1)
        fileAfterPath = "proxyList/" + config.REGION + "/proxyListAfter." \
                + currentHour.strftime(TIME_FORMAT)
        if not os.path.exists(fileAfterPath):
            print("Use last hour proxy list")
            fileAfterPath = "proxyList/" + config.REGION + "/proxyListAfter." \
                    + lastHour.strftime(TIME_FORMAT)
        
        readFile = open(fileAfterPath,"r")
        
        for eachLine in readFile:
            lineArray = eachLine.split('\t')
            if (lineArray[0] != exceptIp) and checkProxy(lineArray[0]):
                print(lineArray[0])
                return lineArray[0]

        return "0"
    except Exception as e:
        print("ERROR: " + str(e.args))
        return "0"
    finally:
        readFile.close()

def main():
    config = ConfigParser.ConfigParser()
    config.read(CONFIGFILE)

    ip1 = config.get("info", "ip1")
    ip2 = config.get("info", "ip2")
    print ip1
    if checkProxy(ip1):
        if checkProxy(ip2):
            print("ip1 and ip2 ok")
            return
        else:
            # 从IP列表中找到IP不是ip1的IP并验证
            selectedIp = getIpfromProxyList(ip1)
            config.set("info", "ip2", selectedIp)
            config.write(open(CONFIGFILE, "w"))
            return
    else:
        if checkProxy(ip2):
            ipProxy.setProxy(ip2)
            selectedIp = getIpfromProxyList(ip2)
            config.set("info", "ip1", ip2)
            config.set("info", "ip2", selectedIp)
            config.write(open(CONFIGFILE, "w"))
            return

        # 如果两个IP都不可用，查找之后的ip仍然不可用，则驱动例行的grapCityIp.py提前执行
        else:
            selectedIp1 = getIpfromProxyList("0")
            # 一直循环驱动直到找到正确IP
            loopVar = 0
            while selectedIp1 == "0":
                if loopVar > 5:
                    break
                else:
                    loopVar += 1

                grapCityIpScript = "python grapCityIp.py"
                scriptResult = subprocess.call(grapCityIpScript.encode(\
                            sys.getfilesystemencoding()))
                print(scriptResult)
                selectedIp1 = getIpfromProxyList("0")

            selectedIp2 = getIpfromProxyList(selectedIp1)
            config.set("info", "ip1", selectedIp1)
            config.set("info", "ip2", selectedIp2)
            config.write(open(CONFIGFILE, "w"))
            return


if __name__ == "__main__":
    main()