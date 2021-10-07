var xhr = new XMLHttpRequest();
xhr.open("POST", "/open", true);
xhr.send();
addEventListener('beforeunload', function () {
  xhr = new XMLHttpRequest();
  xhr.open("POST", "/close", true);
  xhr.send();
});
var settings = getCookie("settings");
if (settings != "") {
  try {
    dark = settings[3];
    if (dark == 1) {
      document.body.style.backgroundColor = "#111";
      document.body.style.color = "#fff";
      links = document.getElementsByTagName("a");
      for (var link = 6; link < links.length; link++) {
        links[link].style.color = "#c7dfff";
      }
      document.getElementsByClassName("navbar")[0].style.color = "#fff";
      document.getElementsByClassName("navbar")[0].style.backgroundColor = "#176e99";
      sections = document.getElementsByClassName("section");
      for (var section = 0; section < sections.length; section++) {
        sections[section].style.backgroundColor = "#444";
      }
    }
  }
  catch(err) {}
}
function openTab(event, tabName, display) {
  var i, tabcontent, tablinks;
  
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }
  tablinks = document.getElementsByClassName("tablinks");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].className = tablinks[i].className.replace(" active", "");
  }
  document.getElementById(tabName).style.display = display;
  event.currentTarget.className += " active";
}
function getCookie(cname) {
  let name = cname + "=";
  let decodedCookie = decodeURIComponent(document.cookie);
  let ca = decodedCookie.split(';');
  for(let i = 0; i <ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) == ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}
function getAPI(url) {
  var xhr = new XMLHttpRequest();
  xhr.open("GET",url,false);
  xhr.send(null);
  return JSON.parse(xhr.responseText);
}