#!/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'rublog'

import os
import time
import shutil
import re
import zipfile


def clear():
    os.system('cls || clear')
    

def make_html():
    all_folders = os.listdir('./')
    find_bak_folder = 0
    for folders in all_folders:
        if folders.startswith(('1', '2', '3', '4', '5', '6', '7', '8', '9')) and folders.endswith(('1', '2', '3', '4', '5', '6', '7', '8', '9', '0')):
            find_bak_folder = 1
            html_folder_name = folders + '_html'
            folders = os.path.join(os.path.abspath('./'), folders)
            html_folder_name = os.path.join(os.path.abspath('./'), html_folder_name)
            merge('/html', html_folder_name)
            make_blog_html(folders, html_folder_name)
            make_photo_html(folders, html_folder_name)
            make_shuoshuo_html(folders, html_folder_name)
            make_msg_board_html(folders, html_folder_name)
        else:
            continue
    if find_bak_folder == 1:
        print('已生成html文件')
    else:
        print("Warning: 好像没有找到备份的文件夹！请先进行备份！")

    pass


def zip_all_files():
    all_folders = os.listdir('./')
    for folders in all_folders:
        if folders.startswith(('1', '2', '3', '4', '5', '6', '7', '8', '9')):
            source_dir = os.path.join(os.path.abspath('./'), folders)
            output_filename = source_dir + '.zip'
            zip_f = zipfile.ZipFile(output_filename, 'w')
            pre_len = len(os.path.dirname(source_dir))
            for root, dir_names, file_names in os.walk(source_dir):
                for file_name in file_names:
                    path_file = os.path.join(root, file_name)
                    arc_name = path_file[pre_len:].strip(os.path.sep)   #相对路径
                    zip_f.write(path_file, arc_name)
            zip_f.close()


# 生成blog的html索引页面和优化博客文章页面
# To-do 替换博客文字页面的图片引用链接，图片保存为本地文件
def make_blog_html(folders, html_folder_name):
    blog_folder = os.path.join(folders, 'blog')
    with open(os.path.join(blog_folder, 'header.html'), 'r') as f:
        header = f.read()
    with open(os.path.join(blog_folder, 'footer.html'), 'r') as f:
        footer = f.read()
    if os.path.isdir(blog_folder):
        for root, dir, files in os.walk(blog_folder):
            for name in files:
                if not name.endswith('.html'):
                    continue
                full_path = os.path.join(root, name)
                split_full_path = full_path.split('\\')
                end_path = '\\'.join(split_full_path[1:])
                with open(full_path, 'r') as f, open((html_folder_name + '\\' + end_path), 'wb+') as html_file, \
                        open((html_folder_name + '\\' + 'index.html')) as index_html:
                    html_file.write(header.encode())
                    content = f.read()
                    content_group = re.search('class="blog_title">([\S\s]*)<div\sclass="blog_footer', content)
                    if content_group:
                        content = content_group.group()
                    html_file.write(content.encode())
                    html_file.write(footer.encode())
                    blog_link_templete = """
                            \n<br>
        <a href="./{0}/{1}">{2}</a>\n
                    """
                    index_html.write(blog_link_templete.format(split_full_path[1], split_full_path[-1],
                                                               split_full_path[-1].rstrip('.html')))




def make_photo_html(folders, html_folder_name):
    pass


def make_shuoshuo_html(folders, html_folder_name):
    pass


def make_msg_board_html(folders, html_folder_name):
    pass


def merge(a_path, b_path):  # 合并两个目录
    b_paths = os.listdir(b_path)  # 获取当前B中的目录结构
    for fp in os.listdir(a_path):  # 遍历当前A目录中的文件或文件夹
        a_new_path = os.path.join(a_path, fp)  # A中的文件或目录
        b_new_path = os.path.join(b_path, fp)  # B中对应的文件或路径，不一定存在
        if os.path.isdir(a_new_path):  # A中的目录
            if os.path.exists(b_new_path):  # 如果在B中存在
                merge(a_new_path, b_new_path)  # 继续合并下一级目录
            else:  # 如果在B中不存在
                # print('[目录]\t%s ===> %s' % (a_new_path, b_new_path))
                shutil.copytree(a_new_path, b_new_path)  # 完全复制目录到B
        elif os.path.isfile(a_new_path):  # A中的文件
            if os.path.exists(b_new_path):  # 如果在B中存在
                # print('[文件]\t%s ===> %s' % (a_new_path, b_new_path))
                # shutil.copy2(a_new_path, b_new_path)
                pass
            else:  # 如果在B中不存在
                # 将该文件复制过去
                # print('[文件]\t%s ===> %s' % (a_new_path, b_new_path))
                shutil.copy2(a_new_path, b_new_path)


def pack_up():
    choice_tips = """备份文件打包脚本

    生成可以浏览的html文件备份版本、打包为单独文件夹和压缩包。

    (0)、生成可以浏览的html文件
    (1)、创建压缩包备份
    (2)、生成tml文件并建立压缩包
    (3)、退出

    请输入选项数字0~3并按回车："""
    end = 1
    while end:
        kk = input(choice_tips)
        print(kk)
        try:
            kk = int(kk)
        except ImportError:
            kk = 10
        if kk == 0:
            clear()
            print('*************************************************************')
            print('    *****正在生成可以浏览的html文件，请稍候.......*****     ')
            print('*************************************************************\n\n')
            make_html()
            clear()
            print('*************************************************************')
            print('    *******已生成可以浏览的html文件，请输入3退出*******     ')
            print('*************************************************************\n\n')
        elif kk == 1:
            clear()
            print('***********************************************************')
            print('     **********正在创建压缩包，请稍候.......**********     ')
            print('***********************************************************\n\n')
            zip_all_files()
            clear()
            print('*************************************************************')
            print('     **************已打包文件，请输入3退出**************     ')
            print('*************************************************************\n\n')
        elif kk == 2:
            clear()
            print('***********************************************************')
            print('  ******正在生成tml文件并建立压缩包，请稍候.......******  ')
            print('***********************************************************\n\n')
            print(' ')
            print(' ')
            make_html()
            zip_all_files()
            clear()
            print('*************************************************************')
            print('   ***********已生成html文件并压缩，请输入3退出***********   ')
            print('*************************************************************\n\n')
        elif kk == 3:
            clear()
            print('正在退出，请稍候.......')
            time.sleep(2)
            end = 0
        else:
            clear()
            print('************************************************')
            print('   **********输入有误，请重新输入！**********   ')
            print('************************************************\n\n')
            continue


if __name__ == '__main__':
    pack_up()
