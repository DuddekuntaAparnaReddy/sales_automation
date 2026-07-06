async function loadRegistrations() {

    try {

        const response =
            await fetch(
                "http://127.0.0.1:8000/registrations"
            );

        const data =
            await response.json();

        const registrationList =
            document.getElementById(
                "registration-list"
            );

        registrationList.innerHTML = "";

        data.forEach(registration => {

            registrationList.innerHTML += `

            <tr>

                <td>${registration[1]}</td>

                <td>${registration[2]}</td>

                <td>${registration[3]}</td>

            </tr>

            `;

        });

    } catch (error) {

        console.log(error);

    }

}

loadRegistrations();