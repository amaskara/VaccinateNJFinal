const regex = new RegExp('........-....-....-....-............');
// Only run what comes next *after* the page has loaded
addEventListener("DOMContentLoaded", starSetup, true);

function starSetup() {
  // Grab all of the elements with a class of command
  // (which all of the buttons we just created have)
  let starbuttons = document.querySelectorAll(".starbutton");
  for (let i=0, l=starbuttons.length; i<l; i++) {
    let button = starbuttons[i];
    // For each button, listen for the "click" event
    button.addEventListener("click", function(e) {
      // When a click happens, stop the button
      // from submitting our form (if we have one)
      e.preventDefault();

      let clickedButton = e.target;
      let siteid = clickedButton.value;
      if(!regex.test(siteid)) {

        console.log("invalid-site-id")
        alert("Invalid site-id. Please reload page and try again");
        return;
        
      }
      console.log("done")
      // Now we need to send the data to our server
      // without reloading the page - this is the domain of
      // AJAX (Asynchronous JavaScript And XML)
      // We will create a new request object
      // and set up a handler for the response
      let request = new XMLHttpRequest();
      request.onload = function() {
          // We could do more interesting things with the response
          // or, we could ignore it entirely
          console.log(request.responseText);

          if(request.responseText == "AddedSite"){
            clickedButton.children[0].classList.add("favorited");
          }
          if(request.responseText == "DeletedSite"){
            clickedButton.children[0].classList.remove("favorited");
          }
          if(request.responseText == "NotSignedIn"){
            alert("Sign in to save sites");
          }

          if(request.responseText == "NotInDatabase"){
            alert("Save your profile info before adding sites");
          }
          
      };
      // We point the request at the appropriate command
      request.open("POST", "/savesite/" + siteid, true);
      // and then we send it off
      request.send();
    });
  }
}
