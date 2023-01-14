document.addEventListener('DOMContentLoaded', async function() {
    const sportsBoxes = document.querySelectorAll('.sport_box');
    let registeredSports = [];

    async function fetchRegisteredSports() {
        try {
            const response = await fetch('/get_registered_sports');
            const data = await response.json();

            if (!response.ok) {
                const errorMessage = data.message || response.statusText;
                throw new Error(`Error fetching registered sports: ${errorMessage}`);
            } else {
                return data;
            }
        } catch (error) {
            console.error('Error fetching registered sports:', error);
            return [];
        }
    }
    registeredSports = await fetchRegisteredSports()

    sportsBoxes.forEach(box => {
        const sportName = box.getAttribute('data-sport-name');
        
        if (registeredSports.includes(sportName)) {
            box.setAttribute('data-sport-colour', 'green');
        } else {
            box.setAttribute('data-sport-colour', 'grey');
        }
        
        let sportColour = box.getAttribute('data-sport-colour');
        const imgElement = box.querySelector('img');

        // Initial set-up of sport_box
        // Get CSS class
        if (sportColour == "grey") {
            box.classList.add('sport_box--grey');
        } else if (sportColour == "green") {
            box.classList.add('sport_box--green');
        }

        // Get relevant image
        fetch(`/get_sport_icon/${sportName}/${sportColour}`)
            .then(response => response.text())
            .then(imageUrl => {
                const imgElement = box.querySelector('img');
                imgElement.src = imageUrl;
            })
            .catch(error => console.error('Error fetching image URL:', error));

        // Listener for registering and deregistering from sports
        box.addEventListener('click', function() {
            let box_status = this.getAttribute('data-sport-colour');

            if (box_status == "grey") {
                const sportName = this.getAttribute('data-sport-name');
                const postData = { sportName: sportName };

                fetch('/register_for_sport', {
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
                    box.setAttribute('data-sport-colour', 'green');
                })
                .catch(error => {
                    console.error('Network error or cannot connect to server:', error);
                });

            } else if (box_status == "green") {
                const sportName = this.getAttribute('data-sport-name');
                const postData = { sportName: sportName };

                fetch('/deregister_for_sport', {
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
                    box.setAttribute('data-sport-colour', 'grey');
                })
                .catch(error => {
                    console.error('Network error or cannot connect to server:', error);
                });
            }
        })

        // Event listener for each box
        box.addEventListener('click', function() {
            let sportName = this.getAttribute('data-sport-name');
            let sportColour = this.getAttribute('data-sport-colour');
            
            if (sportColour == "grey") {
                this.classList.remove('sport_box--grey');
                this.classList.add('sport_box--green');
                this.setAttribute('data-sport-colour', 'green');
            } else if (sportColour == "green") {
                this.classList.remove('sport_box--green');
                this.classList.add('sport_box--grey');
                this.setAttribute('data-sport-colour', 'grey')
            }
            
            sportColour = this.getAttribute('data-sport-colour');

            fetch(`/get_sport_icon/${sportName}/${sportColour}`)
            .then(response => response.text())
            .then(imageUrl => {
                const imgElement = box.querySelector('img');
                imgElement.src = imageUrl;
            })
            .catch(error => console.error('Error fetching image URL:', error));
        })
    });
})