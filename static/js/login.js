document.querySelector(".submit-button").addEventListener("click", (e) => {
  e.preventDefault();
  userLogin();
});
function userLogin() {
  let username = document.querySelector(".username").value;
  let password = document.querySelector(".password").value;
  $.ajax({
    url: "/login",
    type: "POST",
    data: {
      username: username,
      password: password,
    },
    success: (data) => {
      if (data == "user") {
        location.href = "/index?message=logging_in&duration=5000";
      } else if (data == "deo") {
        location.href = "/deo/home?message=logging_in&duration=5000";
      } else if (data == "DNV") {
        popup(
          "Your account is not verified...! Please try again later",
          "blue",
          "5s"
        );
        $(".username").val("");
        $(".password").val("");
        let errorContainer = $("error");
        $.each(errorContainer, (i, error) => {
          $(error).text("");
        });
      } else if (data == "blocked") {
        popup(
          "Your account is blocked by admin... Please try again later",
          "blue",
          "5s"
        );
        $(".username").val("");
        $(".password").val("");
        let errorContainer = $("error");
        $.each(errorContainer, (i, error) => {
          $(error).text("");
        });
      } else {
        let errorContainer = $("error");
        let inputContainer = $(".input");
        $.each(errorContainer, (i, error) => {
          if (i != data.length - 1)
            if (data[i] == "") inputContainer[i + 1].focus();
          $(error).html(data[i]);
        });
      }
    },
  });
}
