function submitForm() {
    // Update to Loading...
    document.getElementById('responseContainer').innerText = "Loading..."
    // Get form data
    const tournamentNumber = document.getElementById('tournamentNumber').value;
    const schoolName = document.getElementById('schoolName').value;

    // Validate tournament number format
    if (!/^\d{5}$/.test(tournamentNumber) || (tournamentNumber == "00000")) {
        alert('Please enter a valid 5-digit number for the Tournament Number.');
        return;
    }

    // Validate school name length
    if (schoolName.length > 50) {
        alert('Please enter a school name with 50 characters or less.');
        return;
    }

    // Create a JSON object with the form data
    const formData = {
        tournament: tournamentNumber,
        school: schoolName
    };

    // Perform a POST request to the API Gateway endpoint
    fetch('https://4wvm0o3xmb.execute-api.us-east-1.amazonaws.com/prod/submit_tournament', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
    })
    .then(response => response.json())
    .then(data => {
        // Display the response
        file_content = data['file_content'].replace("Event-by-Event Results", "### Event-by-Event Results") //.replace(/\n/g, '<br>');
        gpt_content = data['gpt_content'].replace(/\n/g, "\n\n"); // more newlines!
        display_md = "<md-block>" + "## Tournament Summary:\n" + file_content + "\n## Prompt passed to ChatGPT:\n" + gpt_content + "\n" + "</md-block>";
        document.getElementById('responseContainer').innerHTML = display_md;
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('responseContainer').innerText = 'Error occurred. Please try again.';
    });
}

document.querySelector('#myForm').addEventListener('submit', function(e) {
    e.preventDefault();

    // Show the loading message
    document.getElementById('loadingMessage').style.display = 'block';

    // Add the dots
    let dots = window.setInterval( function() {
        let wait = document.getElementById("dots");
        if ( wait.innerHTML.length > 3 ) 
            wait.innerHTML = "";
        else 
            wait.innerHTML += ".";
    }, 300);
});