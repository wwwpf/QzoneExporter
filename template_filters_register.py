from template_filters import (album_position_style, calc_floor,
                              content_beautify, extract_media_info_from_photo,
                              extract_nick_uin_content_from_comment,
                              format_datetime, get_displayed_page_nums,
                              get_photo_comment_media_list, get_photo_url,
                              get_shuoshuo_media_list, get_uin_avatar_url,
                              matched_comments, photo_position_style,
                              purge_file, shuoshuo_media_class,
                              shuoshuo_media_size)


def register_filters(app):
    app.jinja_env.filters["album_position_style"] = album_position_style
    app.jinja_env.filters["calc_floor"] = calc_floor
    app.jinja_env.filters["content_beautify"] = content_beautify
    app.jinja_env.filters["extract_info"] = extract_nick_uin_content_from_comment
    app.jinja_env.filters["extract_media_info_from_photo"] = extract_media_info_from_photo
    app.jinja_env.filters["format_datetime"] = format_datetime
    app.jinja_env.filters["get_displayed_page_nums"] = get_displayed_page_nums
    app.jinja_env.filters["get_photo_url"] = get_photo_url
    app.jinja_env.filters["get_photo_comment_media_list"] = get_photo_comment_media_list
    app.jinja_env.filters["get_shuoshuo_media_list"] = get_shuoshuo_media_list
    app.jinja_env.filters["get_uin_avatar_url"] = get_uin_avatar_url
    app.jinja_env.filters["matched_comments"] = matched_comments
    app.jinja_env.filters["photo_position_style"] = photo_position_style
    app.jinja_env.filters["purge_file"] = purge_file
    app.jinja_env.filters["shuoshuo_media_class"] = shuoshuo_media_class
    app.jinja_env.filters["shuoshuo_media_size"] = shuoshuo_media_size
