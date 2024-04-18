function submitForm() {
    // Update to Loading...
    document.getElementById('responseContainer').innerText = "\nLoading...this may take up to 25 seconds for new summary requests...to keep you engaged, here is a joke:\nHow do you catch de fish? With de-bate!"
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

    // Perform a POST request to the API Gateway endpoint to send the request
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
        file_content = data['file_content']
        gpt_content = data['gpt_content'].replace(/\n/g, "\n\n"); // more newlines!
        numbered_list_prompt_content = data['numbered_list_prompt_content']
        display_md = "<md-block>" + "## Tournament Summary:\n" + file_content + 
                     "\n## Prompt passed to Claude:\n" + gpt_content + "\n" + 
                     "\n## Line-by-Line prompt passed to Claude:\n" + numbered_list_prompt_content + "</md-block>";
        document.getElementById('responseContainer').innerHTML = display_md;
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('responseContainer').innerText = 'Error occurred. Please try again later, as this may have been due to high server demand.';
    });
}
