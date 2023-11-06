from datetime import datetime
import os
import shutil


def main(input_directory, output_directory=None, image_path="smiling_debaters.png"):
    # HTML template
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            /* Define a CSS class to control the layout */
            .text-and-image {{
                display: flex; /* Use flexbox to control layout */
                align-items: center; /* Vertically align items */
            }}
            /* Style for the image */
            .image {{
                margin-left: 20px; /* Add margin to separate text and image */
                max-width: 500px; /* Set a maximum width for the image */
                height: auto; /* Maintain the image's aspect ratio */
            }}
        </style>
        <title>{title}</title>
    </head>
    <body>
        <h1>{title}</h1>
        <p>Author: {author}</p>
        <p>Date: {date}</p>
        <div class="text-and-image">
            <p>
                {body}
            </p>
            <img class="image" src={image_path} alt="Speech and Debate is fun!">
        </div>
    </body>
    </html>
    """
    if output_directory is None:
        output_directory = input_directory.replace("_summaries", "_webpages")
    os.makedirs(output_directory, exist_ok=True)
    shutil.copyfile(image_path, os.path.join(output_directory, image_path))
    os
    # Iterate through text files in the input directory
    for filename in os.listdir(input_directory):
        if filename.endswith(".txt"):
            with open(os.path.join(input_directory, filename), "r") as file:
                with open(
                    os.path.join(output_directory, filename.replace(".txt", ".html")),
                    "w",
                ) as output:
                    output.write(
                        template.format(
                            title=file.readline(),
                            author="Tabroom Summary Services",
                            date=datetime.today().strftime("%Y-%m-%d"),
                            body=file.read().replace("\n", "<br>"),
                            image_path=image_path,
                        )
                    )

    print("Web pages generated successfully!")


if __name__ == "__main__":
    # Not really intending for this to be called from __main__, but may eventually for testing purposes
    main(
        input_directory="./MyTournament MySchool_summaries",
        output_directory="MyTournament MySchool_webpages",
    )
