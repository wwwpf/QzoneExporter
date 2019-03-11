var loadUrl = document.getElementsByTagName("script")[0].getAttribute("src");
 
 function getCode(url,parm) {
		console.log(" url  "+url);
       var reg = new RegExp("(^|&)"+ parm +"=([^&]*)(&|$)");
       var r = url.substr(url.indexOf("\?")+1).match(reg);
       if (r!=null) return unescape(r[2]); return null;
 };
var result = getCode.call(this,loadUrl,"userCode");
alert(result);