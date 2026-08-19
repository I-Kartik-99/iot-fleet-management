const API_BASE_URL = "http://127.0.0.1:8000";

const loginForm = document.getElementById("loginForm");
const errorMessage = document.getElementById("errorMessage");


loginForm.addEventListener("submit", async function (event) {

    event.preventDefault();

    const username =
        document.getElementById("username").value;

    const password =
        document.getElementById("password").value;


    errorMessage.textContent = "";


    try {

        const formData = new URLSearchParams();

        formData.append("username", username);
        formData.append("password", password);


        const response = await fetch(
            `${API_BASE_URL}/auth/login`,
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/x-www-form-urlencoded"
                },

                body: formData
            }
        );


        if (!response.ok) {

            throw new Error(
                "Invalid username or password"
            );
        }


        const data = await response.json();


        // Save JWT
        localStorage.setItem(
            "access_token",
            data.access_token
        );


        // Go to dashboard
        window.location.href = "index.html";


    } catch (error) {

        errorMessage.textContent =
            error.message;

    }

});