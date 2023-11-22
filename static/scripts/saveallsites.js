
// Only run what comes next *after* the page has loaded
const regexplural = new RegExp('........-....-....-....-............');

addEventListener("DOMContentLoaded", function () {
  // Grab all of the elements with a class of command
  // (which all of the buttons we just created have)

  let saveallbutton = document.querySelectorAll(".saveallbutton")[0];
  if (saveallbutton == null)
    return;

  saveallbutton.addEventListener("click", function (e) {
    // When a click happens, stop the button
    // from submitting our form (if we have one)
    e.preventDefault();

    console.log("clicked")

    let visibleSiteBoxes = document.querySelectorAll('.site-box:not([hidden])');
    console.log("Visible site boxes length: " + String(visibleSiteBoxes.length));

    let new_sites = [];
    visibleSiteBoxes.forEach(
      function(siteBox) {
        if (siteBox.querySelector('.star:not(.favorited)') !== null) {
          new_sites.push(siteBox.querySelector('.star:not(.favorited)'));
        }
      }
    );
    console.log("new_sites length: " + String(new_sites.length));

    let site_ids = [];
    let flag = false;

    new_sites.forEach(
      function (currentValue) {
        if(regexplural.test(currentValue.parentNode.value)){
          site_ids.push(currentValue.parentNode.value);
        }
        else{
          console.log("invalid-site-id");
          alert("Invalid site-id. Please reload page and try again");
          flag = true;
        }
        
      },
    );

    if(flag) return;

    // console.log(site_ids)
    // Now we need to send the data to our server
    // without reloading the page - this is the domain of
    // AJAX (Asynchronous JavaScript And XML)
    // We will create a new request object
    // and set up a handler for the response
    let request = new XMLHttpRequest();


    request.open("POST", "/saveallsites", true);
    request.setRequestHeader('Content-Type', 'application/json');

    data = JSON.stringify(site_ids);
    request.send(data);

    request.onload = function () {
      // We could do more interesting things with the response
      // or, we could ignore it entirely
      console.log(request.responseText);

      if (request.responseText == "success") {
        let stars = new_sites;

        stars.forEach(
          function (currentValue) {
            currentValue.classList.add('favorited');
          },
        );

      }
      if(request.responseText == "NotSignedIn"){
        alert("Sign in to save sites");
      }
      
      if(request.responseText == "NotInDatabase"){
        alert("Save your profile info before adding sites");
      }
      




    };
  });
}, true);

addEventListener("DOMContentLoaded", function () {

  let deleteallbutton = document.querySelectorAll(".deleteallbutton")[0];
  if (deleteallbutton == null)
    return;

  deleteallbutton.addEventListener("click", function (e) {
    // When a click happens, stop the button
    // from submitting our form (if we have one)
    e.preventDefault();

    console.log("clicked")

    let visibleSiteBoxes = document.querySelectorAll('.site-box:not([hidden])');
    console.log("Visible site boxes length: " + String(visibleSiteBoxes.length));

    let old_sites = [];
    // console.log(old_sites)
    visibleSiteBoxes.forEach(
      function(siteBox) {
        if (siteBox.querySelector('.star.favorited') !== null) {
          old_sites.push(siteBox.querySelector('.star.favorited'));
        }
      }
    );
    console.log("old_sites length: " + String(old_sites.length));

    let site_ids = []

    let flag = false

    old_sites.forEach(
     function addingsites(currentValue) {
        if(regexplural.test(currentValue.parentNode.value)){
          site_ids.push(currentValue.parentNode.value)
        }
        else{
          console.log("invalid-site-id")
          alert("Invalid site-id. Please reload page and try again");
          flag = true;
        }
      },
    );

    if(flag) return;

    // console.log(site_ids)
    // Now we need to send the data to our server
    // without reloading the page - this is the domain of
    // AJAX (Asynchronous JavaScript And XML)
    // We will create a new request object
    // and set up a handler for the response
    let request = new XMLHttpRequest();


    request.open("POST", "/deleteallsites", true);
    request.setRequestHeader('Content-Type', 'application/json');

    data = JSON.stringify(site_ids);
    request.send(data);

    request.onload = function () {
      // We could do more interesting things with the response
      // or, we could ignore it entirely
      console.log(request.responseText);

      if (request.responseText == "success") {
        let stars = old_sites;

        stars.forEach(
          function (currentValue) {
            currentValue.classList.remove('favorited');
          },
        );

      }

      if(request.responseText == "NotSignedIn"){
        alert("Sign in to save sites");
      }
      if(request.responseText == "NotInDatabase"){
        alert("Save your profile info before adding sites");
      }


    };
  });
}, true);



