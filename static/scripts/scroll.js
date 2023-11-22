let scrollButton = document.querySelector('.scrolltotop-button')

window.onscroll = function() {scrollFunction()};

function scrollFunction() {
  if (document.body.scrollTop > 30 || document.documentElement.scrollTop > 30) {
    scrollButton.style.display = "block";
  } else {
    scrollButton.style.display = "none";
  }
}

$(document).on('click', 'a[href^="#"]', function (event) {
    event.preventDefault();
    $('html, body').animate({
        scrollTop: $($.attr(this, 'href')).offset().top
    }, 500);
});

scrollButton.addEventListener("click", (function() {
  $("html, body").animate({ scrollTop: 0 });
  return false;
}));
