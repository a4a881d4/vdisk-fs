#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## 
#  Copyright (C) 
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation.
# 本程序是免费软件，基于GPL许可发布。
# 
# @文件名(file): vdisk_api.py
# @作者(author): 龙昌锦(LongChangjin)
# @博客(blog): http://www.xefan.com
# @邮箱(mail): admin@xefan.com
# @QQ: 346202141
# @时间(date): 2012-06-05
# 
#
# 新浪微盘API

import urllib, urllib2
import MultipartPostHandler
import json
import hashlib, hmac
import time
import thread

App_Key = "2375169550"
App_Secret = "657d018b5b50b7f4419ef1d2d6e71ac1"

class VDisk:
    def __init__(self, account, password, app_type="local"):
        self.opener = urllib2.build_opener(MultipartPostHandler.MultipartPostHandler)
        urllib2.install_opener(self.opener)
        self.token = ''
        self.dologid = None
        self.dologdir = []
        self.get_token(account, password, app_type)
        thread.start_new_thread(self.keep_thread, ())

    def log(self, msg):
        print(msg.encode('utf-8'))

    #获取token
    def get_token(self, account, password, app_type):
        t = int(time.time())
        signature = hmac.new(App_Secret, "account=" + account + "&appkey=" +
            App_Key + "&password=" + password + "&time=" + `t`, hashlib.sha256).hexdigest()
        data = urllib.urlencode({"account":account, "password":password,
                    "appkey":App_Key, "time":t,
                    "signature":signature, "app_type":app_type})
        url = "http://openapi.vdisk.me/?m=auth&a=get_token"
        req = urllib2.Request(url, data)
        fd = self.opener.open(req)
        js = json.loads(fd.read())
        fd.close()
        if js['err_code'] != 0:
            self.log(js['err_msg'])
        else:
            self.token = js['data']['token']

    #保持同步
    def keep(self):
        url = "http://openapi.vdisk.me/?a=keep"
        data = urllib.urlencode({"token":self.token})
        req = urllib2.Request(url, data)
        fd = self.opener.open(req)
        js = json.loads(fd.read())
        fd.close()
        if js['err_code'] != 0:
            self.log(js['err_msg'])
        else:
            if self.dologid != js['dologid']: self.dologid = js['dologid']
            if self.dologdir != js['dologdir']: self.dologdir = js['dologdir']

    #保持token的线程
    def keep_thread(self):
        while True:
            self.keep_token()
            time.sleep(600)
    #保持token，10-15分钟执行一次
    def keep_token(self):
        url = "http://openapi.vdisk.me/?m=user&a=keep_token"
        data = urllib.urlencode({"token":self.token})
        req = urllib2.Request(url, data)
        fd = self.opener.open(req)
        js = json.loads(fd.read())
        fd.close()
        if js['err_code'] != 0:
            self.log(js['err_msg'])
        else:
            if self.dologid != js['dologid']: self.dologid = js['dologid']
            if self.dologdir != js['dologdir']: self.dologdir = js['dologdir']


    #文件上传（10M以内）
    def upload_file(self, name, is_cover="yes", is_share=False):
        if is_share: 
            url = "http://openapi.vdisk.me/?m=file&a=upload_share_file"
        else: 
            url = "http://openapi.vdisk.me/?m=file&a=upload_file"
        data = {"token":self.token, "dir":"/test2",
                    "cover":is_cover, "file":open(name,"rb")}
        req = urllib2.Request(url, data)
        fd = self.opener.open(req)
        js = json.loads(fd.read())
        fd.close()
        if js['err_code'] != 0:
            self.log(js['err_msg'])
        else:
            if self.dologid != js['dologid']: self.dologid = js['dologid']
            if self.dologdir != js['dologdir']: self.dologdir = js['dologdir']
        return js

    #创建目录
    def create_dir(self, dir_name, parent=0):
        url = "http://openapi.vdisk.me/?m=dir&a=create_dir"
        data = urllib.urlencode({"token":self.token, "create_name":dir_name, "parent_id":parent})
        req = urllib2.Request(url, data)
        fd = self.opener.open(req)
        js = json.loads(fd.read())
        fd.close()
        if js['err_code'] != 0:
            self.log(js['err_msg'])
        else:
            if self.dologid != js['dologid']: self.dologid = js['dologid']
            if self.dologdir != js['dologdir']: self.dologdir = js['dologdir']
        return js

    #获得列表
    def getlist(self, dir_id=0, page=1, pagesize=1024):
        url = "http://openapi.vdisk.me/?m=dir&a=getlist"
        data = urllib.urlencode({"token":self.token, "dir_id":dir_id,
            "page":page, "pageSize":pagesize})
        req = urllib2.Request(url, data)
        fd = self.opener.open(req)
        js = json.loads(fd.read())
        fd.close()
        if js['err_code'] != 0:
            self.log(js['err_msg'])
        else:
            if self.dologid != js['dologid']: self.dologid = js['dologid']
            if self.dologdir != js['dologdir']: self.dologdir = js['dologdir']
        return js

    #获得容量信息
    def get_quota(self):
        url = "http://openapi.vdisk.me/?m=file&a=get_quota"
        data = urllib.urlencode({"token":self.token})
        req = urllib2.Request(url, data)
        fd = self.opener.open(req)
        js = json.loads(fd.read())
        fd.close()
        if js['err_code'] != 0:
            self.log(js['err_msg'])
        else:
            if self.dologid != js['dologid']: self.dologid = js['dologid']
            if self.dologdir != js['dologdir']: self.dologdir = js['dologdir']
        return js

    #无文件上传(sha1)
    def upload_with_sha1(self, name, sha1, dir_id=0):
        url = "http://openapi.vdisk.me/?m=file&a=upload_with_sha1"
        data = urllib.urlencode({"token":self.token, "dir_id":dir_id,
                "sha1":sha1, "file_name":name})
        req = urllib2.Request(url, data)
        fd = self.opener.open(req)
        js = json.loads(fd.read())
        fd.close()
        if js['err_code'] != 0:
            self.log(js['err_msg'])
        else:
            if self.dologid != js['dologid']: self.dologid = js['dologid']
            if self.dologdir != js['dologdir']: self.dologdir = js['dologdir']
        return js

    #获得单个文件信息
    def get_file_info(self, fid):
        url = "http://openapi.vdisk.me/?m=file&a=get_file_info"
        data = urllib.urlencode({"token":self.token, "fid":fid})
        req = urllib2.Request(url, data)
        fd = self.opener.open(req)
        js = json.loads(fd.read())
        fd.close()
        if js['err_code'] != 0:
            self.log(js['err_msg'])
        else:
            if self.dologid != js['dologid']: self.dologid = js['dologid']
            if self.dologdir != js['dologdir']: self.dologdir = js['dologdir']
        return js

    #删除目录/文件
    def delete_file(self, fid, is_dir=True):
        if is_dir:
            url = "http://openapi.vdisk.me/?m=dir&a=delete_dir"
            data = urllib.urlencode({"token":self.token, "dir_id":fid})
        else:
            url = "http://openapi.vdisk.me/?m=file&a=delete_file"
            data = urllib.urlencode({"token":self.token, "fid":fid})
        req = urllib2.Request(url, data)
        fd = self.opener.open(req)
        js = json.loads(fd.read())
        fd.close()
        if js['err_code'] != 0:
            self.log(js['err_msg'])
        else:
            if self.dologid != js['dologid']: self.dologid = js['dologid']
            if self.dologdir != js['dologdir']: self.dologdir = js['dologdir']
        return js

    #复制文件
    def copy_file(self, fid, new_name, to_dir_id=0):
        url = "http://openapi.vdisk.me/?m=file&a=copy_file"
        data = urllib.urlencode({"token":self.token, "fid":fid,
            "new_name":new_name, "to_dir_id":to_dir_id})
        req = urllib2.Request(url, data)
        fd = self.opener.open(req)
        js = json.loads(fd.read())
        fd.close()
        if js['err_code'] != 0:
            self.log(js['err_msg'])
        else:
            if self.dologid != js['dologid']: self.dologid = js['dologid']
            if self.dologdir != js['dologdir']: self.dologdir = js['dologdir']
        return js

    #重命名
    def rename_file(self, fid, new_name, is_dir=True):
        if is_dir:
            url = "http://openapi.vdisk.me/?m=dir&a=rename_dir"
            data = urllib.urlencode({"token":self.token, "dir_id":fid, "new_name":new_name})
        else:
            url = "http://openapi.vdisk.me/?m=file&a=rename_file"
            data = urllib.urlencode({"token":self.token, "fid":fid, "new_name":new_name})
        req = urllib2.Request(url, data)
        fd = self.opener.open(req)
        js = json.loads(fd.read())
        fd.close()
        if js['err_code'] != 0:
            self.log(js['err_msg'])
        else:
            if self.dologid != js['dologid']: self.dologid = js['dologid']
            if self.dologdir != js['dologdir']: self.dologdir = js['dologdir']
        return js

    #移动目录/文件
    def move_file(self, fid, new_name, to_dir_id=0, is_dir=True):
        if is_dir:
            url = "http://openapi.vdisk.me/?m=dir&a=move_dir"
            data = urllib.urlencode({"token":self.token, "dir_id":fid,
                    "new_name":new_name, "to_parent_id":to_dir_id})
        else:
            url = "http://openapi.vdisk.me/?m=file&a=move_file"
            data = urllib.urlencode({"token":self.token, "fid":fid,
                "new_name":new_name, "to_dir_id":to_dir_id})
        req = urllib2.Request(url, data)
        fd = self.opener.open(req)
        js = json.loads(fd.read())
        fd.close()
        if js['err_code'] != 0:
            self.log(js['err_msg'])
        else:
            if self.dologid != js['dologid']: self.dologid = js['dologid']
            if self.dologdir != js['dologdir']: self.dologdir = js['dologdir']
        return js

    #分享文件/取消分享
    def share_file(self, fid, to_share=True):
        if to_share:
            url = "http://openapi.vdisk.me/?m=file&a=share_file"
        else:
            url = "http://openapi.vdisk.me/?m=file&a=cancel_share_file"
        data = urllib.urlencode({"token":self.token, "fid":fid})
        req = urllib2.Request(url, data)
        fd = self.opener.open(req)
        js = json.loads(fd.read())
        fd.close()
        if js['err_code'] != 0:
            self.log(js['err_msg'])
        else:
            if self.dologid != js['dologid']: self.dologid = js['dologid']
            if self.dologdir != js['dologdir']: self.dologdir = js['dologdir']
        return js

    #回收站列表
    def recycle_list(self, size=10, page=1):
        url = "http://openapi.vdisk.me/?m=recycle&a=get_list"
        data = urllib.urlencode({"token":self.token, "page":page, "page_size":size})
        req = urllib2.Request(url, data)
        fd = self.opener.open(req)
        js = json.loads(fd.read())
        fd.close()
        if js['err_code'] != 0:
            self.log(js['err_msg'])
        else:
            if self.dologid != js['dologid']: self.dologid = js['dologid']
            if self.dologdir != js['dologdir']: self.dologdir = js['dologdir']
        return js

    #清空回收站
    def recycle_clean(self):
        url = "http://openapi.vdisk.me/?m=recycle&a=truncate_recycle"
        data = urllib.urlencode({"token":self.token})
        req = urllib2.Request(url, data)
        fd = self.opener.open(req)
        js = json.loads(fd.read())
        fd.close()
        if js['err_code'] != 0:
            self.log(js['err_msg'])
        else:
            if self.dologid != js['dologid']: self.dologid = js['dologid']
            if self.dologdir != js['dologdir']: self.dologdir = js['dologdir']
        return js

    #从回收站删除文件
    def recycle_del(self, fid, is_dir=True):
        if is_dir:
            url = "http://openapi.vdisk.me/?m=recycle&a=delete_dir"
            data = urllib.urlencode({"token":self.token, "dir_id":fid})
        else:
            url = "http://openapi.vdisk.me/?m=recycle&a=delete_file"
            data = urllib.urlencode({"token":self.token, "fid":fid})
        req = urllib2.Request(url, data)
        fd = self.opener.open(req)
        js = json.loads(fd.read())
        fd.close()
        if js['err_code'] != 0:
            self.log(js['err_msg'])
        else:
            if self.dologid != js['dologid']: self.dologid = js['dologid']
            if self.dologdir != js['dologdir']: self.dologdir = js['dologdir']
        return js

    #从回收站还原文件
    def recycle_restore(self, fid, is_dir=True):
        if is_dir:
            url = "http://openapi.vdisk.me/?m=recycle&a=restore_dir"
            data = urllib.urlencode({"token":self.token, "dir_id":fid})
        else:
            url = "http://openapi.vdisk.me/?m=recycle&a=restore_file"
            data = urllib.urlencode({"token":self.token, "fid":fid})
        req = urllib2.Request(url, data)
        fd = self.opener.open(req)
        js = json.loads(fd.read())
        fd.close()
        if js['err_code'] != 0:
            self.log(js['err_msg'])
        else:
            if self.dologid != js['dologid']: self.dologid = js['dologid']
            if self.dologdir != js['dologdir']: self.dologdir = js['dologdir']
        return js

    #通过路径得到目录id
    def get_dirid_with_path(self, path="/"):
        url = "http://openapi.vdisk.me/?m=dir&a=get_dirid_with_path"
        data = urllib.urlencode({"token":self.token, "path":path})
        req = urllib2.Request(url, data)
        fd = self.opener.open(req)
        js = json.loads(fd.read())
        fd.close()
        if js['err_code'] != 0:
            self.log(js['err_msg'])
        else:
            if self.dologid != js['dologid']: self.dologid = js['dologid']
            if self.dologdir != js['dologdir']: self.dologdir = js['dologdir']
        return js

if __name__ == "__main__":
    app_type = ['sinat', 'local']
    i = raw_input("请选择登陆帐号类型：[1]微博帐号 [2]微盘帐号 >")
    if i!='1' and i!='2':
        print("输入的帐号类型有误！")
        exit(1)
    user = raw_input("请输入登陆帐号 >")
    pswd = raw_input("请输入登陆密码 >")
    v = VDisk(user, pswd, app_type[int(i)-1])
    print v.get_quota()
