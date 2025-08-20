"use strict";

// side navigation bar - Desktop only
function toggleSidebar() {
  try {
    const sideNav = document.getElementById("side-nav");
    const main = document.getElementById("main");
    const topNavbar = document.getElementById("top-navbar");
    const manageWrap = document.querySelector(".manage-wrap");
    
    // Only toggle if we're on desktop (width > 768px)
    if (window.innerWidth > 768) {
      if (sideNav) {
        sideNav.classList.toggle("toggle-active");
      }
      
      if (main) {
        main.classList.toggle("toggle-active");
      }
      
      if (topNavbar) {
        topNavbar.classList.toggle("toggle-active");
      }
      
      if (manageWrap) {
        manageWrap.classList.toggle("toggle-active");
      }
    }
  } catch (error) {
    console.error("Error in toggleSidebar:", error);
  }
}

// #################################
// popup

var c = 0;
function pop() {
  if (c == 0) {
    document.getElementById("popup-box").style.display = "block";
    c = 1;
  } else {
    document.getElementById("popup-box").style.display = "none";
    c = 0;
  }
}

// ##################################

// Example starter JavaScript for disabling form submissions if there are invalid fields
// Fetch all the forms we want to apply custom Bootstrap validation styles to
var forms = document.getElementsByClassName("needs-validation");

// Loop over them and prevent submission
Array.prototype.filter.call(forms, function (form) {
  form.addEventListener(
    "submit",
    function (event) {
      if (form.checkValidity() === false) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add("was-validated");
    },
    false
  );
});
// ##################################

// extend and collapse
function showCourses(btn) {
  var btn = $(btn);

  if (collapsed) {
    btn.html('Collapse <i class="fas fa-angle-up"></i>');
    $(".hide").css("max-height", "unset");
    $(".white-shadow").css({ background: "unset", "z-index": "0" });
  } else {
    btn.html('Expand <i class="fas fa-angle-down"></i>');
    $(".hide").css("max-height", "150");
    $(".white-shadow").css({
      background: "linear-gradient(transparent 50%, rgba(255,255,255,.8) 80%)",
      "z-index": "2",
    });
  }
  collapsed = !collapsed;
}

$(document).ready(function () {
  $("#primary-search").focus(function () {
    $("#top-navbar").attr("class", "dim");
    $("#side-nav").css("pointer-events", "none");
    $("#main-content").css("pointer-events", "none");
  });
  $("#primary-search").focusout(function () {
    $("#top-navbar").removeAttr("class");
    $("#side-nav").css("pointer-events", "auto");
    $("#main-content").css("pointer-events", "auto");
  });
});
