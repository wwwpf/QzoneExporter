var o = $;

function setViewerSize() {
    var windowWidth = o(window).width(),
        windowHeight = o(window).height(),
        c = 0,
        p = 0,
        l = 0,
        a = {
            minViewerHeight: 100,
            maxViewerWidth: 9999,
            minViewerWidth: 10
        },
        u = Math.max(windowHeight - c - p, a.minViewerHeight),
        h = Math.max(a.minViewerWidth, Math.min(a.maxViewerWidth, windowWidth * 0.9));
        // h = Math.max(Math.min(Math.min(u * 4 / 3, a.maxViewerWidth), windowWidth - l), a.minViewerWidth);
    this.wrapper = o("#js-viewer-main");
    this.wrapper.width(h + 10 - 25).height(u).show();
    this.imgWrapper = o("#js-viewer-imgWraper");
    this.imgWrapper.width(h - 25).height(u - 60);
    this.figure = o("#js-viewer-figure");
    this.figure.css({
        marginTop: (windowHeight - u) / 2,
        marginLeft: 0
    })
    o("#_slideView_figure_side").height(u);
    o("#js-sidebar-ctn").height(u - 30);
    o("#js-viewer-layer").height(windowHeight);
    o("#js-thumb-ctn").show().css("opacity", 1);
    o("#js-viewer-container").height(windowHeight);
    o("#js-viewer-container").css("display", "block");

    this.imgWrapper.width(this.imgWrapper.width() - o("#js-sidebar-ctn").width() - 20);
}

function setImageCenterInRectangle(img, rect_width, rect_height) {
    var img_width = img.width,
        img_height = img.height,
        scale1 = rect_width / img_width,
        scale2 = rect_height / img_height,
        scale = Math.min(scale1, scale2, 1),
        new_img_width = img_width * scale,
        new_img_height = img_height * scale;
    img.style.width = new_img_width + "px";
    img.style.height = new_img_height + "px";
    img.style.marginLeft = Math.round((rect_width - new_img_width) / 2) + "px";
    img.style.marginTop = Math.round((rect_height - new_img_height) / 2) + "px";
}

function onImageLoad() {
    var t = o("#js-image-ctn"),
        p = document.getElementById("js-img-disp");
    p.style.opacity = 1;
    setImageCenterInRectangle(p, t.width(), t.height());
}

function showLayer(index, num, container_id, layer_name, fun = null) {
    if (index < 0 || index >= num) {
        return;
    }
    var xmlhttp;
    if (window.XMLHttpRequest) {
        xmlhttp = new XMLHttpRequest();
    } else {
        xmlhttp = new ActiveXObject("Microsoft.XMLHTTP");
    }

    xmlhttp.onreadystatechange = function () {
        if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
            document.getElementById(container_id).innerHTML = xmlhttp.responseText;
            if (fun) {
                fun();
            }
        }
    }
    var u = window.location.href + layer_name + "/" + index;
    xmlhttp.open("GET", u, true);
    xmlhttp.send();
}

function showPhotoLayer(photo_index, photo_number) {
    showLayer(photo_index, photo_number, "js-viewer-container", "photo_layer", setViewerSize);
}

function adjustDialogRect() {
    var z = document.getElementById("dialog_main_2");
    var y = document.getElementById("dialog_content_2");
    y.style.height = z.getBoundingClientRect().height - 32 + "px";
}

function showDialogLayer(page, total_page) {
    var layer_id = "qz_dialog_layer";
    showLayer(page - 1, total_page, layer_id, "dialog_layer", adjustDialogRect);
    var x = document.getElementById(layer_id);
    x.style.display = "block";
}