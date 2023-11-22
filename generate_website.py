from datetime import datetime
import os
import shutil


"""
V2 of the website generation creates one website with sub pages for each team.
"""

def main(input_directory):
    sidebar = []
    # Iterate through text files in the input directory
    for filename in os.listdir(input_directory):
        if filename.endswith(".txt"):
            school = filename.replace("_summary.txt", "")
            sidebar.append(f"<a href=\"#\" onclick=\"loadContent(\"{filename}\")\">{school}</a>")
    sidebar.sort()
    sidebar_content = "\r\n".join(sidebar)
    # HTML template
    template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Glenbrooks 2023 Speech and Debate Result Summaries</title>
    <style>
        body {{
            margin: 0;
            font-family: Arial, sans-serif;
        }}

        header {{
            background-color: #333;
            color: #fff;
            padding: 10px;
            text-align: center;
        }}

        nav {{
            width: 200px;
            height: 100%;
            background-color: #f4f4f4;
            position: fixed;
            top: 60px;
            left: 0;
            overflow-x: hidden;
            padding-top: 20px;
        }}

        nav a {{
            display: block;
            padding: 15px;
            text-decoration: none;
            color: #333;
        }}

        main {{
            margin-left: 220px;
            padding: 20px;
        }}
    </style>
</head>
<body>

<header>
    <h1>Glenbrooks 2023 Speech and Debate Result Summaries</h1>
</header>

<nav>
    {sidebar_content}
</nav>

<main id="content">
    <!-- Content will be loaded here -->
</main>

<script>
    function loadContent(filename) {{
        var xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = function() {{
            if (this.readyState == 4 && this.status == 200) {{
                document.getElementById("content").innerHTML = this.responseText;
            }}
        }};
        xhttp.open("GET", filename, true);
        xhttp.send();
    }}
</script>

</body>
</html>
    """

    with open(
        "index.html",
        "w",
    ) as output:
        output.write(
            template
        )

    print("Webpage generated successfully!")


if __name__ == "__main__":
    # Not really intending for this to be called from __main__, but may eventually for testing purposes
    main(
        input_directory="./Glenbrooks Speech and Debate Tournament_summaries",
    )
