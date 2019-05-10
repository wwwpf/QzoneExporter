function mouseOver(...ids) {
    for (i in ids) {
        showElement(ids[i]);
    }
}

function mouseOut(...ids) {
    for (i in ids) {
        hideElement(ids[i]);
    }
}

function showElement(id) {
    controlDisplay(id, "block");
}

function hideElement(id) {
    controlDisplay(id, "none");
}

function controlDisplay(id, s) {
    var x = document.getElementById(id).style;
    x.display = s;
}

function adjustImg(img, max_width, max_height, in_shuoshuo = false, keep = false) {
    var img_width = img.width,
        img_height = img.height,
        r = {},
        l = {},
        d = {};
    r.width = img_width;
    r.height = img_height;
    r.wh = r.width / r.height;
    l.width = max_width;
    l.height = max_height;
    l.wh = l.width / l.height;
    l.base = 1;
    if (r.wh > l.wh) {
        l.base = l.height / r.height
    } else {
        l.base = l.width / r.width
    }
    l.base = Math.min(l.base, 1.5);
    d.width = r.width * l.base;
    d.height = r.height * l.base;
    if (d.height <= l.height || d.height * .8 < l.height) {
        d.marginTop = Math.round((l.height - d.height) / 2)
    } else {
        d.marginTop = -Math.round(d.height * .1)
    }
    if (d.width <= l.width) {
        d.marginLeft = Math.round((l.width - d.width) / 2)
    } else {
        d.marginLeft = Math.round((l.width - d.width) / 2)
    }
    if (in_shuoshuo && img_width < max_width && img_height < max_height) {
        d.width = img_width;
        d.height = img_height;
        d.marginLeft = 0;
        d.marginTop = Math.round((max_height - img_height) / 2);
    }
    if (in_shuoshuo && keep && 0) {
        d.marginLeft = 0;
        d.marginTop = 0;
    }
    img.style.marginLeft = d.marginLeft + "px";
    img.style.marginTop = d.marginTop + "px";
    img.style.width = d.width + "px";
    img.style.height = d.height + "px";
}

