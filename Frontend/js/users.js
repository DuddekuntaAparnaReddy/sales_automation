async function loadUsers() {

    try {

        const response =
            await fetch(
                "http://127.0.0.1:8000/allusers"
            );

        const data =
            await response.json();

        const usersList =
            document.getElementById(
                "users-list"
            );

        usersList.innerHTML = "";

        data.forEach(user => {

            usersList.innerHTML += `

            <tr>

                <td>${user[1]}</td>

                <td>${user[3]}</td>

                <td>System Access</td>

            </tr>

            `;

        });

    } catch(error) {

        console.log(error);

    }

}

loadUsers();