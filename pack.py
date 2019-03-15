#!/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'rublog'

import os
import time
import shutil
import re
import zipfile
import json


def clear():
    os.system('cls || clear')
    

def make_html():
    all_folders = os.listdir('./')
    find_bak_folder = 0
    for folders in all_folders:
        if folders.startswith(('1', '2', '3', '4', '5', '6', '7', '8', '9')) and\
                folders.endswith(('1', '2', '3', '4', '5', '6', '7', '8', '9', '0')):
            find_bak_folder = 1
            html_folder_name = folders + '_html'
            folders = os.path.join(os.path.abspath('./'), folders)
            html_folder_name = os.path.join(os.path.abspath('./'), html_folder_name)
            if not os.path.isdir(html_folder_name):
                os.makedirs(html_folder_name)
            merge('./html', html_folder_name)
            # 记得取消下面4行的注释  folders 是qq备份的文件夹，html_folder_name 是目标文件夹
            # make_blog_html(folders, html_folder_name)
            # make_photo_html(folders, html_folder_name)
            # make_shuoshuo_html(folders, html_folder_name)
            make_msg_board_html(folders, html_folder_name)
        else:
            continue
    if find_bak_folder == 1:
        print('已生成html文件')
    else:
        print("Warning: 好像没有找到备份的文件夹！请先进行备份！")


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
    if not os.path.isdir(blog_folder):
        return
    with open((html_folder_name + '/blog/' + 'header.html'), 'r', encoding='utf-8') as f:
        header = f.read()
    with open((html_folder_name + '/blog/' + 'footer.html'), 'r', encoding='utf-8') as f:
        footer = f.read()
    # print(blog_folder)
    # print(html_folder_name)
    # print(header)
    # print(footer)
    with open((html_folder_name + '\\blog\\' + 'index.html'), 'w+', encoding='utf-8') as index_html:
        header1 = header.replace('../index.html">博客', '../blog/index.html">博客')
        index_html.write(header1)
        for root, dir, files in os.walk(blog_folder):
            for name in files:
                if not name.endswith('.html'):
                    continue
                full_path = os.path.join(root, name)
                # print(full_path)
                split_full_path = full_path.split('\\')
                blog_folder_len = len(blog_folder.split('\\'))
                end_path = '\\'.join(split_full_path[(blog_folder_len-1):])
                html_file_name = html_folder_name + '\\' + end_path
                html_file_folder = os.path.split(html_file_name)[0]
                if not os.path.isdir(html_file_folder):
                    os.makedirs(html_file_folder)
                with open(full_path, encoding='utf-8') as f, open(html_file_name, 'w+', encoding='utf-8') as\
                        html_file:
                    html_file.write(header)
                    content = f.read()
                    # print(full_path)
                    # print(content)
                    content_group = re.findall('class="blog_title">([.\n]*)<div\sclass="blog_footer', content)
                    if content_group:
                        content = content_group[0]
                        # print(content)
                    html_file.write(content)
                    html_file.write(footer)
                    blog_title = split_full_path[-1].rstrip(".html")
                    # print(blog_title)
                    # print(end_path)
                    end_path1 = '\\'.join(split_full_path[blog_folder_len:])
                    blog_link_template = """           \n<br>            \n<a href="./{0}">{1}</a>\n"""
                    blog_para = blog_link_template.format(end_path1, blog_title)
                    # print(blog_para)
                    index_html.write(blog_para)
        footer1 = footer.replace('../index.html">博客', '../blog/index.html">博客')
        index_html.write(footer1)


def make_photo_html(folders, html_folder_name):
    photo_base_folder = folders + '/photo'
    photo_aim_folder = html_folder_name + '/photo'
    if not os.path.isdir(photo_base_folder):
        return
    merge(photo_base_folder, photo_aim_folder)
    with open((html_folder_name + '/photo/' + 'header.html'), 'r', encoding='utf-8') as f:
        header = f.read()
    with open((html_folder_name + '/photo/' + 'footer.html'), 'r', encoding='utf-8') as f:
        footer = f.read()
    with open((html_folder_name + '/photo/' + 'album_info.json'), encoding='utf-8') as albums:
        album_dict = json.load(albums)
        album_dict = album_dict['data']['albumListModeSort']
    with open((html_folder_name + '\\photo\\' + 'index.html'), 'w+', encoding='utf-8') as index_html:
        header1 = header.replace('../index.html">相册', '../photo/index.html">相册')
        header1 = header1.replace('../../', '../')
        index_html.write(header1)
        album_link_template = """      \n<br>            \n<a href="./{0}_{1}/index.html">{2}</a>\n         <br>"""
        for album in album_dict:
            aim_album_link = album_link_template.format(album['name'], album['id'], album['name'])
            # print(aim_album_link)
            index_html.write(aim_album_link)
        footer1 = footer.replace('../index.html">相册', '../photo/index.html">相册')
        footer1 = footer1.replace('../../', '../')
        index_html.write(footer1)
    for album in album_dict:
        album_folder = photo_base_folder + '\\' + "{0}_{1}/".format(album['name'], album['id'])
        if os.path.isdir(album_folder):
            file_list = os.listdir(album_folder)
        else:
            continue
        # header2 = header.replace('../index.html">相册', '../../photo/index.html">相册')
        # footer2 = footer.replace('../index.html">相册', '../../photo/index.html">相册')
        with open((album_folder + '/index.html'), 'w+', encoding='utf-8') as album_index:
            album_index.write(header)
            for file in file_list:
                if file.endswith('.json') and file.startswith('photo'):
                    with open(os.path.join(album_folder, file), encoding='utf-8') as album_json:
                        photo_dict = json.load(album_json)
                        # print(photo_dict['data'])
                        photo_list = photo_dict['data']['photoList']
                        photo_link_template = """
                              \n<br>            \n{0}<br><img src="./downloaded/{1}.{2}"  alt="{3}" />\n         <br>"""
                        for photo in photo_list:
                            if photo['phototype'] == 1:
                                suffix = 'jpeg'
                            elif photo['phototype'] == 2:
                                suffix = 'gif'
                            elif photo['phototype'] == 3:
                                suffix = 'png'
                            else:
                                suffix = 'jpeg'
                            photo_link = photo_link_template.format(photo['name'], photo['lloc'].replace('*', '%2A'), suffix, photo['name'])
                            album_index.write(photo_link)
            album_index.write(footer)


# To-do 1.替换说说中的图片为本地图片，并且下载图片到本地；2.支持emoji表情
def make_shuoshuo_html(folders, html_folder_name):
    shuoshuo_base_folder = folders + '/shuoshuo'
    shuoshuo_aim_folder = html_folder_name + '/shuoshuo'
    if not os.path.isdir(shuoshuo_base_folder):
        return
    merge(shuoshuo_base_folder, shuoshuo_aim_folder)
    with open((html_folder_name + '/shuoshuo/' + 'header.html'), 'r', encoding='utf-8') as f:
        header = f.read()
    with open((html_folder_name + '/shuoshuo/' + 'footer.html'), 'r', encoding='utf-8') as f:
        footer = f.read()
    with open((html_folder_name + '\\shuoshuo\\' + 'index.html'), 'w+', encoding='utf-8') as index_html:
        index_html.write(header)
        shuoshuo_link_template = """      \n<br>            \n<a href="./{0}.html">{1}</a>\n         <br>"""
        for root, dir_names, file_names in os.walk(shuoshuo_aim_folder):
            for file_name in file_names:
                if file_name.endswith('.json') and file_name.startswith('shuoshuo'):
                    file_name_list = file_name.split('.')
                    # print(file_name)
                    # print(file_name_list[0])
                    shuoshuo_link = shuoshuo_link_template.format(file_name_list[0], file_name_list[0])
                    index_html.write(shuoshuo_link)
        index_html.write(footer)
    file_names = os.listdir(shuoshuo_aim_folder)
    # print(file_names)
    for file_name in file_names:
        if file_name.endswith('.json') and file_name.startswith('shuoshuo'):
            file_name_list = file_name.split('.')
            with open((html_folder_name + '/shuoshuo/' + file_name_list[0] + '.html'), 'w+', encoding='utf-8') as\
                    aim_html, open((html_folder_name + '/shuoshuo/' + file_name), 'r', encoding='utf-8') as aim_json:
                aim_html.write(header)
                shuoshuo_dict = json.load(aim_json)
                shuoshuo_list = shuoshuo_dict['msglist']
                """
                <div class="shuoshuo">
                    <div class="shuoshuo-time"><span>{发布时间}</span></div>
                    <div class="shuoshuo-content">
                        <p class="weibo-text">{说说内容}{图片} </p>
                    </div>\n
                    {评论内容}
                </div>\n
                    """
                shuoshuo_template = """
            <div class="shuoshuo">
                <div class="shuoshuo-time"><span>{0}##</span></div>
                <div class="shuoshuo-content">
                    <p class="weibo-text">{1}{2} </p>
                </div>\n
                {3}
            </div>\n
                """
                shuoshuo_comment_template = '<br><div class="comment" id={0}><span uid="{1}">{2}<span>:{3}@{4}</div>'
                # <div class="comment" id={评论序号}><span uid="{作者qq}">{作者昵称}<span>:{评论内容}@{评论时间}</div>
                shuoshuo_comment_reply_template = '<br><div class="comment_reply" id={0}>' \
                                                  '<span uid="{1}">{2}<span>:{3}@{4}</div>'
                # <div class="comment" id={评论序号}><span uid="{作者qq}">{作者昵称}回复{评论者}<span>:{评论内容}@{评论时间}</div>
                shuoshuo_pic_template = '<br><div class="comment_pic"> <img src="{0}"></div>'
                for shuoshuo in shuoshuo_list:
                    # 如果说说存在评论
                    shuoshuo_comment = '<br>'
                    if 'commentlist' in shuoshuo.keys():
                        for comment in shuoshuo['commentlist']:
                            shuoshuo_comment = shuoshuo_comment + shuoshuo_comment_template.format(
                                comment['tid'], comment['uin'], comment['name'], comment['content'],
                                comment['createTime'])
                            # 如果评论的回复存在
                            shuoshuo_reply = '<br>'
                            if 'list_3' in comment.keys():
                                for reply in comment['list_3']:
                                    shuoshuo_reply = shuoshuo_reply + shuoshuo_comment_reply_template.format(
                                        reply['tid'], reply['uin'], reply['name'], reply['content'], reply['createTime'])
                            # 合并所有的评论
                            shuoshuo_comment = shuoshuo_comment + shuoshuo_reply
                    # 如果说说存在图片
                    shuoshuo_pic = ''
                    if 'pic' in shuoshuo.keys():
                        for pic in shuoshuo['pic']:
                            shuoshuo_pic = shuoshuo_pic + shuoshuo_pic_template.format(pic['url2'])
                    shuoshuo_html = shuoshuo_template.format(
                        shuoshuo['createTime'], shuoshuo['content'], shuoshuo_pic, shuoshuo_comment)
                    aim_html.write(shuoshuo_html)
                aim_html.write(footer)


def make_msg_board_html(folders, html_folder_name):
    pass


"""
记得删除 puck up中的调试注释掉的功能
记得删除make_blog_html 中调用各个函数的调试注释的功能
"""


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
            # clear()
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
