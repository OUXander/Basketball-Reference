function openSidebar() {
	document.getElementById("sidebar").style.visibility = "visible";
	document.getElementById("sidebar-open").style.visibility = "hidden";
	document.getElementById("sidebar").style.width = "260px";
}

function closeSidebar() {
	document.getElementById("sidebar").style.visibility = "hidden";
	document.getElementById("sidebar-open").style.visibility = "visible";
	document.getElementById("sidebar").style.width = "0";
}

document.addEventListener("DOMContentLoaded", () => {
	const input = document.getElementById("searchInput");
	const button = document.getElementById("searchButton");

	if (!input || !button) return;

	input.addEventListener("input", () => {
		if (input.value.trim().length > 0) {
			button.disabled = false;
			button.classList.add("active");
		} else {
			button.disabled = true;
			button.classList.remove("active");
		}
	});
});