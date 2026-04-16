function openSidebar() {
	document.getElementById("sidebar").style.visibility= "visible";
	document.getElementById("sidebar-open").style.visibility= "hidden";
	document.getElementById("sidebar").style.width = "250px";
	document.getElementById("main").style.marginLeft = "250px";
}

function closeSidebar() {
	document.getElementById("sidebar").style.visibility= "hidden";
	document.getElementById("sidebar-open").style.visibility= "visible";
	document.getElementById("sidebar").style.width = "0";
	document.getElementById("main").style.marginLeft = "0";
} 
