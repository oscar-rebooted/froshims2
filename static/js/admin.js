document.addEventListener('DOMContentLoaded', function() {
    const newAdminButton = document.querySelector('#new_admin__button');

    newAdminButton.addEventListener('click', function() {
        const newAdmin = document.getElementById('#new_admin__textbox').value;
        const postData = { new_admin_username: newAdmin };
        
        // function toggleDisplay(elementId) {
        // } 

        fetch('/make_admin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(postData),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error: status ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log(data.message);
            
            document.getElementById('successMessage').style.display = 'block';
            setTimeout(() => {
                document.getElementById('successMessage').style.display = 'none';
            }, 3000)
        })
        .catch(error => {
            console.error('Network error or cannot connect to server:', error);
        });
    })
})