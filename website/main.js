function submitForm() {
    // Update to Loading...
    document.getElementById('responseContainer').innerText = "\nLoading...this may take up to 25 seconds for new summary requests...to keep you engaged, here is a joke:\nHow do you catch de fish? With de-bate!"
    // Get form data
    const tournamentNumber = document.getElementById('tournamentNumber').value;
    const schoolName = document.getElementById('schoolName').value;
    const email = document.getElementById('email').value;

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

    // Email must include @ sign.
    if (email.length > 50 || (email.length != 0  && !/@/.test(email))) {
        alert('Please enter a valid email with 50 characters or less.');
        return;
    }

    // Create a JSON object with the form data
    const formData = {
        tournament: tournamentNumber,
        school: schoolName,
        email: email
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

// document.addEventListener('DOMContentLoaded', function() {
//     // Replace with your bucket name and file path
//     const bucketName = 'tabroomsummary.com';
//     const filePath = 'recent_tournaments.txt';
//     const fileUrl = `http://${bucketName}.s3.amazonaws.com/${filePath}`;
    
//     // Fetch the .txt file
//     fetch(fileUrl)
//         .then(response => {
//             if (!response.ok) {
//                 throw new Error('Network response was not ok');
//             }
//             return response.text();
//         })
//         .then(data => {
//             // Display the file content in the div with id 'file-content'
//             document.getElementById('file-content').textContent = data;
//         })
//         .catch(error => {
//             console.error('There was a problem with the fetch operation:', error);
//         });
// });