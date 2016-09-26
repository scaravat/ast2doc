function setContentSize () {

    // Get the height of the banner div and that available for the content (px)
    var bannerList = window.document.getElementsByClassName("wideautoheightbanner");
    if (bannerList.length !== 1)
        alert("resizeContentWindow error 0");
    var banner = bannerList[0], grace = 8,
        availableHeight = window.innerHeight - banner.offsetHeight - grace;

    // Set the height of the content div (px)
    var contentList = window.document.getElementsByClassName("landing_page_content");
    if (contentList.length !== 1)
        alert("resizeContentWindow error 1");
    var contentDiv = contentList[0];
    contentDiv.setAttribute("style","height:"+availableHeight+"px;");

}
