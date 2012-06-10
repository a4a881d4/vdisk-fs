#!/usr/bin/env python
#-*- coding:utf-8 -*-
## 
#  Copyright (C) 
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation.
# 本程序是免费软件，基于GPL许可发布。
# 
##
# @文件名(file): vdisk.py
# @作者(author): 龙昌锦(LongChangjin)
# @博客(blog): http://www.xefan.com
# @邮箱(mail): admin@xefan.com
# @QQ: 346202141
# @时间(date): 2012-06-06
# 
# 新浪微盘文件系统
# 

import os
import sys
import stat
import time
import errno
import vdisk_api
import thread
from fuse import FUSE, Operations, LoggingMixIn, FuseOSError


class Vdisk_fs(LoggingMixIn, Operations):
    def __init__(self, account, password, app_type):
        print(u"获取文件列表...")
        self.vdisk = vdisk_api.VDisk(account, password, app_type)
        self.now = time.time()
        self.all_dir = {}
        self.get_ok = False
        thread.start_new_thread(self.walk, ())
        while not self.get_ok:
            time.sleep(1)

    #5分钟遍历一次列表
    def walk(self):
        while True:
            data_list = self.walk_recursion(0)
            self.all_dir.clear()
            self.all_dir['list'] = data_list
            if not self.get_ok:
                self.get_ok = True
            print(u"文件列表获取成功")
            time.sleep(300)

    def get_list(self, did):
        page = 1
        data_list = []
        while True:
            dir_list = self.vdisk.getlist(did, page)
            for l in dir_list['data']['list']:
                data = {}
                data['id'] = int(l['id'])
                data['name'] = l['name'].encode('utf-8')
                data['time'] = int(l['ctime'])
                #文件
                if l.has_key('byte'):
                    data['size'] = int(l['byte'])
                if l.has_key('type'):
                    data['type'] = l['type'].encode('utf-8')
                if l.has_key('dir_id'):
                    data['p_id'] = int(l['dir_id'])
                else:
                    data['p_id'] = int(l['pid'])
                if l.has_key('url'):
                    data['url'] = l['url'].encode('utf-8')
                #目录
                if l.has_key('file_num'):
                    data['file_num'] = int(l['file_num'])
                if l.has_key('dir_num'):
                    data['dir_num'] = int(l['dir_num'])
                data_list.append(data)
            if page >= dir_list['data']['pageinfo']['pageTotal']:
                break
            page += 1
        return data_list

    def walk_recursion(self, did):
        data_list = self.get_list(did)
        for d_list in data_list:
            if d_list.has_key('type'):
                continue
            if d_list['dir_num'] != 0 or d_list['file_num'] != 0:
                d_list['list'] = self.walk_recursion(d_list['id'])
        return data_list
    #文件属性
    def getattr(self, path, fh=None):
        print("getattr path:%s" % path)
        if path == '/':
            st = dict(st_mode=(stat.S_IFDIR | 0644), st_nlink=2)
            st['st_ctime'] = st['st_mtime'] = st['st_atime'] = self.now
            return st
        
        path = os.path.normpath(path)
        dirname = os.path.dirname(path)
        basename = os.path.basename(path)
        path_list = dirname.split('/')
        deep = len(path_list)
        i = 1
        c_list = self.all_dir['list']
        while i < deep:
            for d_list in c_list:
                if path_list[i] == d_list['name']:
                    c_list = d_list['list'] if d_list.has_key('list') else []
                    break
            i += 1
        for d_list in c_list:
            if basename == d_list['name']:
                if d_list.has_key('type'):  #文件
                    st = dict(st_mode=(stat.S_IFREG | 0444), st_size=d_list['size'])
                else:                     #目录
                    st = dict(st_mode=(stat.S_IFDIR | 0644), st_nlink=2)
                st['st_ctime'] = st['st_mtime'] = st['st_atime'] = d_list['time']
                return st
        print("getattr:path not!")
        raise FuseOSError(errno.ENOENT)
    #文件列表
    def readdir(self, path, fh):
        print("readdir path:%s" % path)
        data = ['.', '..']
        if path == '/':
            for d_list in self.all_dir['list']:
                data.append(d_list['name'])
            return data
        path_list = path.split('/')
        deep = len(path_list)
        i = 1
        c_list = self.all_dir['list']
        while i < deep:
            for d_list in c_list:
                if path_list[i] == d_list['name']:
                    c_list = d_list['list'] if d_list.has_key('list') else []
                    break
            i += 1
        for d_list in c_list:
            data.append(d_list['name'])
        return data


    #重命名/移动文件
    def rename(self, old, new):
        print("rename old:%s  new:%s" % (old, new))
        path = os.path.normpath(old)
        dirname = os.path.dirname(path)
        basename = os.path.basename(path)
        path_list = dirname.split('/')
        deep = len(path_list)
        i = 1
        c_list = self.all_dir['list']
        while i < deep:
            for d_list in c_list:
                if path_list[i] == d_list['name']:
                    c_list = d_list['list'] if d_list.has_key('list') else []
                    break
            i += 1
        path = os.path.normpath(new)
        dirname_new = os.path.dirname(path)
        basename_new = os.path.basename(path)
        for d1_list in c_list:
            if basename == d1_list['name']:
                break
        parent_list = c_list
        if dirname == dirname_new:  #重命名
            if d1_list.has_key('type'):  #文件
                js = self.vdisk.rename_file(d1_list['id'], basename_new, False)
            else:                     #目录
                js = self.vdisk.rename_file(d1_list['id'], basename_new, True)
            if js['err_code'] == 0:
                d1_list['name'] = basename_new
            return
        #移动
        path_list = dirname_new.split('/')
        print(path_list)
        deep = len(path_list)
        i = 1
        c_list = self.all_dir['list']
        p_list = self.all_dir
        parent_id = 0
        while i < deep:
            for d_list in c_list:
                if path_list[i] == d_list['name']:
                    parent_id = d_list['id']
                    p_list = d_list
                    c_list = d_list['list'] if d_list.has_key('list') else []
                    break
            i += 1
        if d1_list.has_key('type'):  #文件
            js = self.vdisk.move_file(d1_list['id'], basename_new, parent_id, False)
        else:                     #目录
            js = self.vdisk.move_file(d1_list['id'], basename_new, parent_id, True)
        print js
        if js['err_code'] == 0:
            d1_list['name'] = basename_new
            d1_list['p_id'] = js['data']['dir_id'] if js['data'].has_key('dir_id') else js['data']['parent_id']
            if not p_list.has_key('list'):
                p_list['list'] = []
            p_list['list'].append(d1_list)
            parent_list.remove(d1_list)
    #创建目录
    def mkdir(self, path, mode=0644):
        print("mkdir path:%s" % path)
        path = os.path.normpath(path)
        dirname = os.path.dirname(path)
        basename = os.path.basename(path)
        path_list = dirname.split('/')
        deep = len(path_list)
        i = 1
        c_list = self.all_dir['list']
        parent_id = 0
        p_list = self.all_dir
        while i < deep:
            for d_list in c_list:
                if path_list[i] == d_list['name']:
                    parent_id = d_list['id']
                    p_list = d_list
                    c_list = d_list['list'] if d_list.has_key('list') else []
                    break
            i += 1
        
        js = self.vdisk.create_dir(basename, parent_id)
        if js['err_code'] == 0:
            l = js['data']
            data = {}
            data['id'] = int(l['dir_id'])
            data['name'] = l['name'].encode('utf-8')
            data['time'] = int(l['ctime'])
            data['p_id'] = int(l['pid'])
            if not p_list.has_key('list'):
                p_list['list'] = []
            p_list['list'].append(data)
            
    #删除目录
    def rmdir(self, path):
        print("rmdir path:%s" % path)
        path = os.path.normpath(path)
        dirname = os.path.dirname(path)
        basename = os.path.basename(path)
        path_list = dirname.split('/')
        deep = len(path_list)
        i = 1
        c_list = self.all_dir['list']
        while i < deep:
            for d_list in c_list:
                if path_list[i] == d_list['name']:
                    c_list = d_list['list'] if d_list.has_key('list') else []
                    break
            i += 1
        for d_list in c_list:
            if basename == d_list['name']:
                js = self.vdisk.delete_file(d_list['id'], True)
                if js['err_code'] == 0:
                    c_list.remove(d_list)

    #删除文件
    def unlink(self, path):
        print("rm path:%s" % path)
        path = os.path.normpath(path)
        dirname = os.path.dirname(path)
        basename = os.path.basename(path)
        path_list = dirname.split('/')
        deep = len(path_list)
        i = 1
        c_list = self.all_dir['list']
        while i < deep:
            for d_list in c_list:
                if path_list[i] == d_list['name']:
                    c_list = d_list['list'] if d_list.has_key('list') else []
                    break
            i += 1
        for d_list in c_list:
            if basename == d_list['name']:
                js = self.vdisk.delete_file(d_list['id'], False)
                if js['err_code'] == 0:
                    c_list.remove(d_list)

    #读文件 目前还没有实现
    def read(self, path, size, offset, fh):
        print("read: %s %d %d" % (path, size, offset))
    #写文件 目前还没有实现
    def write(self, path, data, offset, fh):
        print("read: %s %s %d" % (path, data, offset))
    
    create = None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: %s <point>" % sys.argv[0])
        exit(1)
    print(u"|--------------------------------------------------")
    print(u"|\t\t\t新浪微盘文件系统             ")
    print(u"|\t作者：龙昌                          ")
    print(u"|\t博客：http://www.xefan.com             ")
    print(u"|\t邮箱：admin@xefan.com                   ")
    print(u"|--------------------------------------------------")
    app_type = ['sinat', 'local']
    i = raw_input("请选择登陆帐号类型：[1]微博帐号 [2]微盘帐号 >")
    if i!='1' and i!='2':
        print("输入的帐号类型有误！")
        exit(1)
    user = raw_input("请输入登陆帐号 >")
    pswd = raw_input("请输入登陆密码 >")
    fuse = FUSE(Vdisk_fs(user, pswd, app_type[int(i)-1]), sys.argv[1], foreground=True)


